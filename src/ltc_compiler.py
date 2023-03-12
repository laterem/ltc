try:
    from .ltc_builtins import *
    from .ltc_core import *
    #from context_objects import LATEREM_FLAGS, LTC_CheckerShortcuts, LTC_SingleStorage
    #from context_objects import LTC_DEFAULT_EXPORT_VALUE, LTC_DEFAULT_INPUT_VALUE
except ImportError:
    from ltc_builtins import *
    from ltc_core import *
    #LTC_CheckerShortcuts = LTC_SingleStorage = True
    #LATEREM_FLAGS = {True}
    #LTC_DEFAULT_EXPORT_VALUE = '0'
    #LTC_DEFAULT_INPUT_VALUE = '0'

VERSION = "dev-NewSyntax0.1"
RECOMPILATION_ATTEMPTS = 100

class LTCMetadataManager:
    seed: int
    salt: int
    xor: int

    def tick_seed(self):
        self.seed = (self.seed + self.salt) ^ self.xor
    
class LTCFakeMetadata:

    @property
    def seed(self):
        return randint(0, 10000000)

    def tick_seed(self):
        pass

class LTC:
    def __init__(self, namespace, checks, constrains,
                 exporting_fields):
        self.namespace = namespace
        self.exporting_fields = exporting_fields
        self.checks = checks
        self.constrains = constrains
        self.known_input_fields = set()
        self.executed = False
    
    def feed_html(self, text):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(text, features="html.parser")
        for inp in soup.find_all('input'):
            self.known_input_fields.add(inp.get('name'))

    #def get_answer_fields(self):
    #    return [x[0] for x in self.checker_functions]
    
    def mask_answer_dict(self, __dict):
        return {key: __dict[key] for key in self.known_input_fields}

    @classmethod
    def from_dict(cls, data):
        executed = True
        namespace = data['namespace']
        checks = []
        constrains = []
        exporting_fields = set(data["exporting_fields"])
        for checkerobj in data['checks']:
            function = KEYWORD_TABLE[checkerobj['function']](*checkerobj['args'])
            checks.append(function)
        for checkerobj in data['constrains']:
            function = KEYWORD_TABLE[checkerobj['function']](*checkerobj['args'])
            constrains.append(function)
        ltc = cls(namespace, checks, constrains, exporting_fields)
        ltc.executed = executed 
        return ltc

    def to_dict(self):
        INVERSE_TABLE = dict((v,k) for k,v in KEYWORD_TABLE.items())
        if not self.executed: self.execute()
        mainobj = {}
        mainobj['namespace'] = self.namespace
        mainobj['checks'] = []
        mainobj['constrains'] = []
        mainobj['exporting_fields'] = list(self.exporting_fields)
        for checker in self.checks:
            checkerobj = {}
            checkerobj['function'] = INVERSE_TABLE[checker.__class__]
            checkerobj['args'] = checker.args
            mainobj['checks'].append(checkerobj)
        for checker in self.constrains:
            checkerobj = {}
            checkerobj['function'] = INVERSE_TABLE[checker.__class__]
            checkerobj['args'] = checker.args
            mainobj['constrains'].append(checkerobj)
        return mainobj
    
    def execute(self, extend_ns=None, metadata=None, 
                timeout=RECOMPILATION_ATTEMPTS,
                default_export_value='0',
                default_input_value='0'):
        try:
            if metadata is None:    
                metadata = LTCFakeMetadata()

            if extend_ns is None:
                extend_ns = {}

            if not timeout:
                raise LTCError(f"LTC could not fit user forbidden cases conditions for {RECOMPILATION_ATTEMPTS} attempts of recompilation.")
            new_namespace = {}
            new_checks = []
            new_constrains = []

            for field in self.exporting_fields:
                new_namespace[field] = default_export_value
            for field in self.known_input_fields:
                new_namespace['$' + field] = default_input_value
            
            new_namespace.update(extend_ns)
            
            for key, value in self.namespace.items():
                new_namespace[key] = value.compile(new_namespace, metadata)(ns=new_namespace)
            for value in self.checks:
                new_checks.append(value.compile(new_namespace, metadata))
            for value in self.constrains:
                new_constrains.append((field, value.compile(new_namespace, metadata)))

            if not LTC.validate(new_namespace, new_checks, new_constrains):
                return self.execute(extend_ns, metadata, timeout-1)
            
            del self.namespace
            del self.checks
            del self.constrains
            self.namespace = new_namespace
            self.checks = new_checks
            self.constrains = new_constrains
            self.executed = True
        except Exception as e:
            raise LTCExecutionError(str(e))
    
    @staticmethod
    def validate(namespace, checks, constrains):
        valid = True
        for checker in constrains:
            valid = valid and checker()
        return valid

    def check(self):
        try:
            valid = True
            for checker in self.checks:
                valid = valid and checker()
            return valid
        except Exception as e: # <-- ПЛОХО ОЧЕНЬ ПЛОХО но работает
            return False
            raise LTCExecutionError(str(e))
    

class LTCCompiler:
    def _typevalue(txt: str):
        txt = txt.strip()
        if txt[-1] == txt[0] == '"':
            txt = txt.strip('"')
            return LTCValue(txt)
        elif txt[-1] == txt[0] == "'":
            txt = txt.strip("'")
            return LTCValue(txt)
        elif txt.lstrip('-').replace(".", "", 1).isdigit():
            return LTCValue(txt)
        elif txt[0] == '[' and txt[-1] == ']':
            args = txt[1:-1].split(',')
            args = LTCCompiler._combine_kws(args, ',')
            args = [LTCCompiler._typevalue(arg) for arg in args]
            return LTCValue(args)
        elif '(' in txt and txt[-1] == ')':
            return LTCCompiler._build_func(txt)
        else:
            return LTCAllias(txt)

    def _build_func(txt):
        fname = txt[:txt.find('(')]
        try:
            func = KEYWORD_TABLE[fname]
        except KeyError:
            raise LTCCompileError('Unknown function ' + fname + '. Maybe you forgot to import it?')
        args = txt[txt.find('(') + 1:-1].split(',')
        args = LTCCompiler._combine_kws(args, ',')
        fargs = [LTCCompiler._typevalue(arg) for arg in args]

        funcobj = func(*fargs)
        return funcobj

    def _combine_kws(kws, joiner=' '):
        for i, kw in enumerate(kws):
            if kw is None:
                continue
            kw = kw.strip()
            if kw.startswith('['):
                LTCCompiler._combine_kw(i, '[', ']', kws, joiner)
            elif kw.startswith('"'):
                LTCCompiler._combine_kw(i, '"', '"', kws, joiner)
            elif kw.startswith("'"):
                LTCCompiler._combine_kw(i, "'", "'", kws, joiner)
            elif '(' in kw:
                LTCCompiler._combine_kw(i, '(', ')', kws, joiner)
        return [kw for kw in kws if kw]

    def _combine_kw(origin, opener, closer, kws, joiner=' '):
        kw = kws[origin]
        ff = kw
        if opener != closer:
            runf = lambda _: ff.count(opener) != ff.count(closer) 
        else:
            runf = lambda _: ff.count(opener) % 2 != 0
        i = origin
        while runf(...):
            i += 1
            ff += joiner + kws[i]
            kws[i] = None
        kws[origin] = ff
    
    def compile(self, source_lines_iter):
        COMPILER_VERSION = "dev-NewSyntax0.1"
        if COMPILER_VERSION != VERSION:
            raise NotImplemented
        
        namespace = {}
        exported_fields = set()
        checks = []
        constrains = []

        def tokenize(line, lineop=None):
            if lineop is not None:
                line = line.replace(lineop, ' ')
            return [token.strip()
                    for token in LTCCompiler._combine_kws(line.split())]
            
        for i, line in enumerate(source_lines_iter):
            if '#' in line:
                line = line[:line.find('#')]
            line = line.strip()
            if not line:
                continue
            
            try:
                if '=' in line:
                    tokens = tokenize(line, '=')
                    if tokens[0] == 'export':
                        tokens = tokens[1:]
                        exported_fields.add(tokens[0])
                    namespace[tokens[0]] = LTCCompiler._typevalue(tokens[1])
                    continue
                
                tokens = tokenize(line)
                if tokens[0] == 'check':
                    function = LTCCompiler._typevalue(tokens[1])
                    checks.append(function)
                    continue
                if tokens[0] == 'constain':
                    function = LTCCompiler._typevalue(tokens[1])
                    constrains.append(function)
                    continue
            except IndexError:
                raise LTCCompileError(f'Not enough arguments on line {i}: {line}')
            raise LTCCompileError(f'Could not recognize any known operations on line {i}: {line}')
        
        return LTC(namespace=namespace, 
                   checks=checks,
                   constrains=constrains,
                   exporting_fields=exported_fields)



if __name__ == '__main__':
    test = '''
a = Rand10(0, 10)
check Equal(a, 5)'''

    ltcc = LTCCompiler()
    
    for _ in range(100):
        ltc = ltcc.compile(test.splitlines())
        ltc.execute()