#! /usr/bin/env python3
'''
Yakety is a simple Extended Backus-Nauer Form (EBNF) recursive descent parser
generator.

A language specification consists of rules and directives:

  ebnf             : directives rules

where directives (purely optional) are introduced by '!' and may be either
start or ignore directives:

  directives       : {directive}
  directive        : '!' (ignore_directive | start_directive)
  ignore_directive : 'ignore' REGEX
  start_directive  : 'start' IDENTIFIER

A start directive indicates start symbol for the grammar; if not specified, it
will be the first nonterminal encountered. An ignore directive indicates what
character sequences to skip when scanning for terminals.

The remainder of Yakety's notation is fairly conventional EBNF, both described
and demonstrated here:

  rules            : {rule}
  rule             : IDENTIFIER ':' productions
  productions      : production {'|' production}
  production       : {substitution}
  enclosed         : '(' productions ')'
  repeated         : '{' productions '}'
  optional         : '[' productions ']'
  reference        : IDENTIFIER
  IDENTIFIER       : /[a-zA-Z_][a-zA-Z0-9_]*/
'''

import json
import sys

from .ebnf_parser import *

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
    def __init__(self, grammar, **symbols):
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
        s = skip_ignores(self.ignore, s)
        if s:
            n, pr0 = len(s), None
            for x in self.symbols[self.start](s):
                pr = p, rest = x
                rest = skip_ignores(self.ignore, rest)
                if not rest:
                    return p
                elif len(rest) < n:
                    n, pr0 = len(rest), pr

            raise SyntaxError(pr0)
                
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
        if not hasattr(self, 'start'):
            self.start = name

    def h_ignore_directive(self, _, *args):
        self.ignore |= {arg.value[1:-1] for arg in args}

    def h_start_directive(self, _, start):
        self.start = start.value

################################################################################
