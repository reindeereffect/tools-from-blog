#! /usr/bin/env python3

from ebnf_parser import *

import sys
import json

################################################################################

def skip_ignores(igs, s):
    t = ""
    while s and t != s:
        t = s
        for ig in igs:
            m = re.match(ig, s)
            if m: s = s[m.end():]
    return s

def literal3(igs, spec, s):
    n = len(spec)
    s = skip_ignores(igs, s)
    if s[:n] == spec: yield spec, s[n:]

def match3(igs, spec, s):
    s = skip_ignores(igs, s)
    m = re.match('(%s)' % spec, s)
    if m:
        g = m.group(0)
        yield g, s[len(g):]

################################################################################

def dummy_parser(parsefn):
    parsefn.__name__ = ''
    return parser(parsefn)

def enclosure(sym): return type(sym) == list

def nonterminal(sym): return not (isinstance(sym, symbol) and sym.terminal)

def combine(parts, fn):
    if   len(parts) == 0: return EPSILON
    elif len(parts) == 1: return parts[0]
    else                : return fn(*parts)
    
def parserize(parsefn):
    return parsefn if isinstance(parsefn, parser) else parser(parsefn)

## the parser generator

class Parser:
    def __init__(self, start, grammar, **symbols):
        self.start   = start
        self.grammar = grammar
        self.symbols = symbols
        self.ignore = set()
        
        self._eval(parse2(ebnf, grammar))
        
    def literal(self, spec):
        return dummy_parser(lambda s: literal3(self.ignore, spec, s))
    
    def match(self, spec)  :
        return dummy_parser(lambda s: match3(self.ignore, spec, s))

    def handle(self, sym):
        handler = getattr(self, 'h_' + sym.type, None)
        if handler:
            hargs = [sym.value] if sym.terminal else sym.value
            sym.result = handler(*hargs)
            return sym.result
        
    def subeval(self, sym):
        for child in sym: self._eval(child)
            
    def _eval(self, sym):
        self.subeval(sym)
        if not enclosure(sym): self.handle(sym)
                    
    def __call__(self, s):
        try:
            return next(self.parses(s))[0]
        except StopIteration:
            raise SyntaxError(skip_ignores(self.ignore, s))

    def parses(self, s, full=True):
        s = skip_ignores(self.ignore, s)
        if s:
            for x in self.symbols[self.start](s):
                p, rest = x
                if not full: yield x
                elif not skip_ignores(self.ignore, rest): yield x

                
    #### handlers
    
    def h_enclosed(self, _, body, __): return body.result
    def h_optional(self, _, body, __): return opt(body.result)
    def h_repeated(self, _, body, __): return rep(body.result)
    
    def h_substitution(self, subst) : return subst.result
    
    def h_STRING_LITERAL(self, s): return self.literal(s[1:-1])
    def h_REGEX         (self, r): return self.match  (r[1:-1])

    def h_reference(self, name):
        return lambda s: self.symbols[name.value](s)

    def h_production(self, *substs_):
        substs = [subst.result for subst in substs_ if subst]
        return combine(substs, seq)

    def h_productions(self, first, rest):
        prods = [first.result] + [prod.result for (_, prod) in rest]
        return combine(prods, alt)
        
    def h_rule(self, name_, _, prods):
        parsefn = parserize(prods.result)
        parsefn.f.__name__ = name = name_.value
        self.symbols[name] = parsefn

    def h_directive(self, _, cmd, *args):
        if cmd.value == 'ignore':
            self.ignore |= {arg.value[1:-1] for arg in args}


    
################################################################################
        
if __name__ == '__main__':
    JSON = False
    if '-j' in sys.argv:
        JSON = True
        del sys.argv[sys.argv.index('-j')]
        
    _, start, grammarfn = sys.argv
    grammar = open(grammarfn).read()
    
    text = sys.stdin.read()
    P = Parser(start, grammar)

    try:
        sym = P(text)
        if JSON: print(json.dumps(sym.todict()))
        else: print(sym)
    except SyntaxError as e:
        if e.args[0]:
            ps = P.parses(text, full=False)
            sym = min((len(p[1]), p) for p in ps)[1]
            
            if JSON:
                sys.stderr.write(json.dumps(dict(parsed=sym[0].todict(),
                                                 unconsumed=sym[1])))
            else: sys.stderr.write(repr(sym))
