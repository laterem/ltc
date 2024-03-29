from ltc_builtins import *
from ltc_compiler import *
from ltc_core import *

all_tests = []


def run_tests():
    for test in all_tests:
        test()


class TestFailed(Exception):
    pass


def test(name):
    def wrapper(function):
        def new():
            print(f"[ ] <Test {name}>" + "\t" + "Starting...")
            try:
                function()
            except TestFailed as e:
                print(f"[!] <Test {name}>" + "\t" + "Test failed! " + str(e))
            except Exception as e:
                print(
                    f"[!] <Test {name}>"
                    + "\t"
                    + "Runtime error occured: "
                    + type(e).__name__
                    + ": "
                    + str(e)
                )
            else:
                print(
                    f"[ ] <Test {name}>" + "\t" + "Test passed successfully!"
                )

        all_tests.append(new)
        return new

    return wrapper


@test("1 Basic")
def test1():
    string = """
a = 5
check Equal($input, a)"""

    ltcc = LTCCompiler()

    ltc = ltcc.compile(string.splitlines())
    ltc.execute(extend_ns={"$input": 5})

    if not ltc.check():
        raise TestFailed("5")

    ltc = ltcc.compile(string.splitlines())
    ltc.execute(extend_ns={"$input": "5"})
    if not ltc.check():
        raise TestFailed("'5'")

    ltc = ltcc.compile(string.splitlines())
    ltc.execute(extend_ns={"$input": 10})
    if ltc.check():
        raise TestFailed("10")

    ltc = ltcc.compile(string.splitlines())
    ltc.execute(extend_ns={"$input": "chunky"})
    if ltc.check():
        raise TestFailed("chunky")


@test("2 Functions")
def test2():
    string = """
a = Rand10(-20, 20)
b = Rand10(-20, 20)
check Equal($input, Sum(a, b))"""

    ltcc = LTCCompiler()

    metadata = LTCMetadataManager()
    metadata.seed = 1
    metadata.salt = 214
    metadata.xor = 100
    ltc = ltcc.compile(string.splitlines())
    ltc.execute(metadata=metadata)
    a, b = ltc.namespace["a"], ltc.namespace["b"]

    metadata = LTCMetadataManager()
    metadata.seed = 1
    metadata.salt = 214
    metadata.xor = 100
    ltc = ltcc.compile(string.splitlines())
    ltc.execute(metadata=metadata, extend_ns={"$input": a + b})
    print(ltc.namespace)
    if not ltc.check():
        raise TestFailed()


@test("3 Shortcuts")
def test3():
    raise TestFailed("Deprecated feature")
    string = """
a = Rand10(-20, 20)
b = Rand10(-20, 20)
input?Sum(a, b)"""

    ltcc = LTCCompiler()

    metadata = LTCMetadataManager()
    metadata.seed = 1
    metadata.salt = 214
    metadata.xor = 100
    ltc = ltcc.compile(string)
    ltc.execute(metadata=metadata)
    a, b = ltc.field_table["a"], ltc.field_table["b"]

    ltc = ltcc.compile(string)
    ltc.execute(metadata=metadata, extend_ns={"input": a + b})
    if not ltc.check():
        raise TestFailed()


@test("4 Lists")
def test4():
    string = """
a = [0, 1, 2, 3, 4, "[I'm no list, capiche?]", Reverse(['But', 'I', 'am!'])]
check Equal($input, Reverse(a))"""

    ltcc = LTCCompiler()

    ltc = ltcc.compile(string.splitlines())

    input = reversed(
        [
            0,
            1,
            2,
            3,
            4,
            "[I'm no list, capiche?]",
            reversed(["But", "I", "am!"]),
        ]
    )

    ltc.execute(extend_ns={"$input": input})
    correct = [
        0,
        1,
        2,
        3,
        4,
        "[I'm no list, capiche?]",
        list(reversed(["But", "I", "am!"])),
    ]

    if not ltc.namespace["a"] == correct:
        raise TestFailed(
            "list is "
            + str(ltc.namespace["a"])
            + ", should be "
            + str(correct)
        )

    if not ltc.check():
        raise TestFailed()


@test("5 Constrains 1")
def test5():
    string = """
a = Rand10(0, 10)
constrain NotEqual(a, 5)"""

    ltcc = LTCCompiler()

    for i in range(10000):
        ltc = ltcc.compile(string.splitlines())
        ltc.execute()
        if ltc.namespace["a"] == 5:
            raise TestFailed("a == 5")


@test("6 Constrains 2")
def test6():
    ltcc = LTCCompiler()

    string = """
a = 21
b = Sum(a, a)

constrain Equal(b, 42)"""

    ltcc = LTCCompiler()

    ltc = ltcc.compile(string.splitlines())
    ltc.execute()

    for i in range(10000):
        if ltc.namespace["b"] != "42":
            raise TestFailed("b != 42")


@test("7 Tricky typing")
def test7():
    ltcc = LTCCompiler()
    string = """
a = 7
b = 3.5
c = Multiply(b, 2)
d = Sum(b, b)
e = Sum(Sum(b, b), Sum(a, a))

f = Multiply(c, 11)
g = GenerateLine(2, a)

check Equal(inputa, c)
check Equal(inputc, d)
check Equal(inpute, 21)
check Equal(inputg, f)
"""
    ltc = ltcc.compile(string.splitlines())
    input = {
        "inputa": 7,
        "inputc": 7,
        "inpute": 21,
        "inputg": 77,
    }
    ltc.execute(extend_ns=input)
    ft = ltc.namespace
    if not ltc.check():
        raise TestFailed(str(ft) + " (must be )")


@test("8 Basic Algebra")
def test8():
    ltcc = LTCCompiler()
    string = """
a = 10
b = 5
c = Divide(a, b)
d = Substract(b, a)
e = Power(a, b)

"""
    ltc = ltcc.compile(string.splitlines())
    ltc.execute()
    ft = ltc.namespace
    if ft["c"] != 2:
        raise TestFailed("Division")
    elif ft["d"] != -5:
        raise TestFailed("Substract")
    elif ft["e"] != 10**5:
        raise TestFailed("Exponention")


@test("9 Parser Test")
def test9():
    string = """
_ = Calc("3*(2-1)")
a = Calc("42 / 2 + (1 * 10)")
b = Calc("(2*(9 - 12) ^ 2) * 2")
c = Calc("0.1 + 0.02 + (3 / 1000)")
"""

    ltcc = LTCCompiler()

    ltc = ltcc.compile(string.splitlines())
    ltc.execute()

    a, b, c = ltc.namespace["a"], ltc.namespace["b"], ltc.namespace["c"]
    correct_a = 42 / 2 + (1 * 10)
    correct_b = (2 * (9 - 12) ** 2) * 2
    correct_c = 0.1 + 0.02 + (3 / 1000)
    if a != correct_a:
        raise TestFailed("A: " + str(a) + " instead of " + str(correct_a))
    if b != correct_b:
        raise TestFailed("B: " + str(b) + " instead of " + str(correct_b))
    if c != correct_c:
        raise TestFailed("C: " + str(c) + " instead of " + str(correct_c))


@test("10 Parser Unary Minus Problem Test")
def test10():
    string = """
a = Calc("42 / 2 + (-(1 * 10))")
"""
    ltcc = LTCCompiler()

    ltc = ltcc.compile(string.splitlines())
    ltc.execute()

    a = ltc.namespace["a"]
    correct_a = 42 / 2 + (-(1 * 10))
    if a != correct_a:
        raise TestFailed("A: " + str(a) + " instead of " + str(correct_a))


@test("11 Manual boolean parser test")
def test11():
    from lib.booleans import BooleanParser, BooleanFormula

    f1 = BooleanFormula("!(A&B)")
    f2 = BooleanFormula("!A | !B")
    tt1 = f1.truth_table()
    tt2 = f2.truth_table()
    if tt1 != {(0, 0): True, (1, 0): True, (0, 1): True, (1, 1): False}:
        raise TestFailed("TT incorrect " + str(tt1))
    if tt1 != tt2:
        raise TestFailed("Truth tables not equal")
    if not f1.is_equal(f2):
        raise TestFailed("Formulas not equal")
    if set(f1.operators(True)) != {"NOT", "AND"}:
        raise TestFailed("f1 operators " + str(f1.operators(True)))
    if set(f2.operators(True)) != {"NOT", "OR"}:
        raise TestFailed("f2 operators " + str(f2.operators(True)))


@test("12 Exporting fields")
def test12():
    string = """
a = 1
export b = 10
export c = 42
export d = 'Default'
"""
    ltcc = LTCCompiler()

    ltc = ltcc.compile(string.splitlines())
    ltc.execute()

    a = ltc.exporting_fields
    if a != {"b", "c", "d"}:
        raise TestFailed(str(a))


@test("13 Formula generator showcase")
def test13():
    from lib.booleans import RandomBooleanFormula

    metadata = LTCMetadataManager()
    metadata.seed = 1
    metadata.salt = 214
    metadata.xor = 100

    for i in range(10):
        func = RandomBooleanFormula().compile({}, metadata)
        print(func({}))


@test("14 Formula truth table showcase")
def test14():
    from lib.booleans import TruthTable

    func = TruthTable('a|b').call()
    print(func)


if __name__ == "__main__":
    run_tests()
