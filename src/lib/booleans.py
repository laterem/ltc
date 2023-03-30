from .formula_parser import FormulaParser, Operator

try:
    from ..ltc_core import LTCFunction, register_function
except ModuleNotFoundError:
    from ltc_core import LTCFunction, register_function
except ImportError:
    from ltc_core import LTCFunction, register_function

import random


class BooleanParser(FormulaParser):
    operators = {
        "|": Operator(0, lambda a, b: a or b, name="OR"),
        "&": Operator(1, lambda a, b: a and b, name="AND"),
        "!": Operator(2, lambda a: not a, arity=1, name="NOT"),
    }

    @staticmethod
    def object_convert(string, variables):
        if string in variables:
            return variables[string]
        else:
            return bool(int(string))

    @staticmethod
    def object_validation(string):
        if not string.strip():
            return False, False
        if string.strip().isalpha():
            return True, True
        return True, False

    @staticmethod
    def object_identification(symbol, carry):
        VARIABLE = "abcdefghijklmnopqrstuvwxyz"
        VARIABLE += VARIABLE.upper()
        NUMBER = "10"
        if symbol in VARIABLE:
            return True
        if symbol in NUMBER:
            return True
        return False


class BooleanFormula:
    def __init__(self, string):
        self.string = string
        self.variables = BooleanParser._collect_variables(string)

    def __str__(self):
        return self.string

    def calc(self, **variables):
        bp = BooleanParser()
        return bp.eval(self.string, variables)

    def is_equal_tt(self, tt):
        return NotImplemented
        for key, value in self.tt.items():
            try:
                if tt[key] != value:
                    return False
            except KeyError:
                return False
        return True

    def operators(self, string=False):
        if string:
            return [
                op.name for op in BooleanParser._collect_operators(self.string)
            ]
        return BooleanParser._collect_operators(self.string)

    def truth_table(self):
        variables = list(self.variables)
        tt = {}
        intrep = 0
        final = int("1" * len(variables), 2) + 1
        while intrep != final:
            prompt = {}
            intrepp = intrep
            for variable in self.variables:
                prompt[variable] = intrepp % 2
                intrepp //= 2
            result = self.calc(**prompt)
            tt[tuple([prompt[var] for var in variables])] = result
            intrep += 1
        return tt

    def is_equal(self, other):
        volume = len(self.variables)
        # if len(other.variables) != volume:
        #    return False
        variables = 0
        final = int("1" * volume, 2) + 1
        while variables != final:
            prompt = {}
            intrepp = variables
            for variable in self.variables:
                prompt[variable] = intrepp % 2
                intrepp //= 2
            result1 = self.calc(**prompt)
            result2 = other.calc(**prompt)
            if result1 != result2:
                return False
            variables += 1
        return True


# LTC Функции для работы с булевыми формулами


class EvalBoolean(LTCFunction):
    expected_argsc = 2

    def call(self):
        func, values = self.args
        func = BooleanFormula(func)
        variables = list(func.variables)
        return func.calc(
            {var: val for var, val in zip(sorted(variables), values)}
        )


class IsBooleanIdentical(LTCFunction):
    expected_argsc = 2

    def call(self):
        field, bf1 = self.args
        bf1 = BooleanFormula(bf1)
        bf2 = BooleanFormula(field)
        if bf1.is_equal(bf2):
            return True
        return False


class BooleanFormulaOperators(LTCFunction):
    expected_argsc = 1

    def call(self):
        (f,) = self.args
        return [op.name for op in BooleanParser._collect_operators(f)]


class IsBooleanFormulaOperators(LTCFunction):
    expected_argsc = 2

    def call(self):
        field = self.args[0]
        ops = set(self.args[1])
        return ops == set(
            [op.name for op in BooleanParser._collect_operators(field)]
        )


class RandomBooleanFormula(LTCFunction):
    expected_argsc = 0

    def call(self):
        inputs = "abcd"
        unary_operations = ("!", "", "")
        binary_operations = ("&", "|")

        def random_arg(depth=0):
            random.seed(self.metadata.seed)
            self.metadata.tick_seed()
            if depth >= 2:
                return random.choice(unary_operations) + random.choice(inputs)
            if depth > 0 and random.randint(0, 3) == 3:
                return random.choice(unary_operations) + random.choice(inputs)
            return (
                random.choice(binary_operations),
                random_arg(depth=depth + 1),
                random_arg(depth=depth + 1),
            )

        op_tree = random_arg()

        def concat_tree(tree, parenthesis=False):
            if isinstance(tree, str):
                return tree
            content = tree[0].join(
                map(lambda x: concat_tree(x, True), tree[1:])
            )
            if parenthesis:
                return f"({content})"
            return content

        return concat_tree(op_tree)


class TruthTable(LTCFunction):
    expected_argsc = 1

    def call(self):
        func = self.args[0]
        parsed = BooleanFormula(func)
        tt = parsed.truth_table()
        return [''.join(map(str, key)) for key, value in tt.items() if value]

class VariablesInFormula(LTCFunction):
    expected_argsc = 1

    def call(self):
        func = self.args[0]
        parser = BooleanParser()
        return parser._collect_variables(func)

register_function(
    BooleanFormulaOperators=BooleanFormulaOperators,
    IsBooleanIdentical=IsBooleanIdentical,
    IsBooleanFormulaOperators=IsBooleanFormulaOperators,
    EvalBoolean=EvalBoolean,
    RandomBooleanFormula=RandomBooleanFormula,
    TruthTable=TruthTable
)
