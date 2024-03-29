class LTCCompileError(Exception):
    pass

class LTCError(Exception):
    pass

class LTCExecutionError(Exception):
    pass

class LTCObject:
    def __init__(self, value):
        self.value = value

    def __call__(self):
        return self.value

KEYWORD_TABLE = {}

def register_function(**kwargs):
    KEYWORD_TABLE.update(kwargs)

NResult = object()

class LTCFunction:
    expected_argsc = 0
    result = NResult
    compiled = False
    _is_checker = False

    def __init__(self, *args):
        argsc = len(args)
        if argsc != self.expected_argsc:
            raise LTCCompileError(f'{type(self).__name__} expected {self.expected_argsc} arguments, {argsc} were given.')
        self.args = list(args)

    def __call__(self, ns):
        if self.result is NResult:
            self.result = self.call()
        return self.result
    
    def compile(self, ns, metadata):
        nargs = self.args[:]

        for i, arg in enumerate(nargs):
            if callable(arg):
                nargs[i] = arg.compile(ns, metadata)(ns)
            elif isinstance(arg, list):
                nargs[i] = [a.compile(ns, metadata)(ns) for a in arg]
            else:
                continue
        new = type(self)(*nargs)
        new.compiled = True
        new.metadata = metadata
        return new

class LTCValue(LTCFunction):
    expected_argsc = 1    
    def call(self):
        return self.args[0]

class LTCAllias(LTCFunction):
    def __init__(self, name):
         self.args = [name]
    
    def __call__(self, ns):
        r = ns[self.args[0]]
        if callable(r):
            return r(ns)
        else:
            return r