#! /usr/bin/env python3

import re
import sys
import json

################################################################################

# Time spent on a nice printable representation of complex data structures 
# repays itself at debugging time.

def indent(s, tab='    '): return tab + s.replace('\n', '\n' + tab)

def todict(sym):
    if type(sym) == list:
        return list(map(todict, sym))
        return dict(type='', value=list(map(todict, sym)))
    elif sym.terminal:
        return dict(type=sym.type, value=sym.value)
    else:
        return dict(type=sym.type, value=list(map(todict, sym.value)))
    
class symbol:
    def __init__(self, type_, value):
        self.type = type_
        self.value = [value] if isinstance(value, symbol) else value
        self.terminal = type(self.value) != list
            
    def __repr__(self):
        if self.terminal: return '%s: %s' % (self.type, self.value)
        else:
            header = self.type + ':'
            body = '\n'.join(map(repr, self.value))
            
            if body.count('\n') == 0: return header + ' ' + body
            else: return header + '\n' + indent(body)
            
    def __iter__(self):
        if not self.terminal: return iter(self.value)
        else: return iter(())

    def todict(self):
        return todict(self)
        
class parse_result(tuple):
    def __repr__(self):
        return '''
        parse
        =====
        %s
        
        unconsumed
        ==========
        %s
        '''.replace('''
        ''', '\n') % self

################################################################################
# backtracking combinators

def alt(*ps):
    def parse(s):
        return (item for p in ps for item in p(s))
    return parse



def seq(*ps):
    def parse(s):
        if ps:
            for first, rest in ps[0](s):
                if ps[1:]:
                    for cont, rest2 in seq(*ps[1:])(rest):
                        yield [first] + cont, rest2
                else: yield [first], rest
    return parse

def rep(p):
    def parse(s):
        stack = [([], s)]
        while stack:
            path, s = stack.pop(-1)
            yield path, s
            for x, rest in p(s):
                if len(rest) < len(s): # EPSILON can cause infinite loopiness
                    stack.append((path + [x], rest))
    return parse


def opt(p): return alt(p, EPSILON)

def literal(spec, s):
    spec = spec.strip()
    n = len(spec)
    s = s.lstrip()
    if s[:n] == spec: yield spec, s[n:]

def match(spec, s):
    s = s.lstrip()
    m = re.match('(%s)' % spec, s)
    if m:
        g = m.group(0)
        yield g, s[len(g):]


class parser:
    def __init__(self, f): self.f = f
    
    def __call__(self, s):
        for matched, rest in self.f(s):
            sym = symbol(self.f.__name__, matched)
            yield parse_result((sym, rest))
            
@parser
def EPSILON(s): yield '', s

################################################################################

def parses(start, s):
    for x in start(s):
        p, rest = x
        if not rest.strip(): yield p


def parse(start, s): return next(parses(start, s))


def skip_comment(s):
    s2 = re.sub('^#[^\n]*', '', s.lstrip()).lstrip()
    while s2 != s:
        s = s2
        s2 = re.sub('^#[^\n]*', '', s.lstrip()).lstrip()
    return s
    
def literal2(spec, s): 
    return literal(spec, skip_comment(s))

def match2(spec, s): 
    return match(spec, skip_comment(s))


@parser
def IDENTIFIER(s): return match2(r'[a-zA-Z_][a-zA-Z0-9_]*', s)

@parser
def STRING_LITERAL(s): 
    return match2(r"\'(\\.|[^\\'])*\'", s)

@parser
def REGEX(s): return match2(r'/(\\.|[^\\/])+/', s)


@parser
def LBRACE(s): return literal2('{', s)

@parser
def RBRACE(s): return literal2('}', s)

@parser
def LBRACK(s): return literal2('[', s)

@parser
def RBRACK(s): return literal2(']', s)

@parser
def LPAREN(s): return literal2('(', s)

@parser
def RPAREN(s): return literal2(')', s)

@parser
def COLON(s): return literal2(':', s)

@parser
def PIPE(s): return literal2('|', s)


@parser
def rules(s):
    'rules : {rule}'
    return rep(rule)(s)

@parser
def rule(s):
    'rule : IDENTIFIER COLON productions'
    return seq(IDENTIFIER, COLON, productions)(s)

@parser
def productions(s):
    'productions : production {PIPE production}'
    return seq(production, rep(seq(PIPE, production)))(s)

@parser
def production(s): 
    'production : {substitution}'
    return rep(substitution)(s)

@parser
def substitution(s):
    '''
    substitution : repeated 
                 | optional 
                 | enclosed 
                 | reference 
                 | STRING_LITERAL 
                 | REGEX'
    '''
    return alt(repeated, 
               optional, 
               enclosed, 
               reference, 
               STRING_LITERAL, 
               REGEX)(s)

@parser
def enclosed(s):
    'enclosed : LPAREN productions RPAREN'
    return seq(LPAREN, productions, RPAREN)(s)

@parser
def repeated(s):
    'repeated : LBRACE productions RBRACE'
    return seq(LBRACE, productions, RBRACE)(s)

@parser
def optional(s):
    'optional : LBRACK productions RBRACK'
    return seq(LBRACK, productions, RBRACK)(s)

@parser
def reference(s):
    'reference : IDENTIFIER'
    return IDENTIFIER(s)


def dummy_parser(parsefn):
    parsefn.__name__ = ''
    return parser(parsefn)

def Literal(spec): return dummy_parser(lambda s: literal2(spec, s))
def Match(spec)  : return dummy_parser(lambda s: match2(spec, s))

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
        
        self._eval(next(parses(rules, grammar)))
    
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
        return parse(self.symbols[self.start], s)

    def parses(self, s, full=True):
        return self(s) if full else self.symbols[self.start](s)
        
    #### handlers
    
    def h_enclosed(self, _, body, __): return body.result
    def h_optional(self, _, body, __): return opt(body.result)
    def h_repeated(self, _, body, __): return rep(body.result)
    
    def h_substitution(self, subst) : return subst.result
    
    def h_STRING_LITERAL(self, s): return Literal(s[1:-1])
    def h_REGEX         (self, r): return Match  (r[1:-1])

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


class evaluator:
    def __init__(self):
        self.skip = 0
        self.handler = {}
        
    # If nonzero, self.skip inhibits evaluation of the next self.skip sibling
    # nodes in the parse tree by left-to-right postorder evaluation. It is
    # reset to 0 on moving up the parse tree. This was done to allow setting
    # skip to, say, -1 to inhibit the remaining siblings (however many there
    # are) while allowing handlers higher in the tree to operate normally.
    
    def __call__(self, sym):
        'evaluate the subtree rooted at sym'
        if self.skip: self.skip -= 1
        else: return self._eval_basic(sym)

    def _eval_basic(self, sym):
        ret = None
        dummy = type(sym) == list
        
        if not getattr(sym, 'terminal', False):
            for child in sym: ret = self(child)
            self.skip = 0
            if dummy: return ret
            
        try: handler = self.handler[sym.type]
        except KeyError: return
        except AttributeError: return
        
        hargs = [sym.value] if sym.terminal else sym.value
        sym.result = handler(*hargs)
        
        return sym.result
        
    def on(self, sym):
        'set a symbol handler'
        def deco(fn):
            self.handler[sym] = fn
            return fn
        return deco
    
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
    except StopIteration:
        ps = Parser(start, grammar).parses(text, full=False)
        sym = min((len(p[1]), p) for p in ps)[1]

        if JSON:
            sys.stderr.write(json.dumps(dict(parsed=sym[0].todict(),
                                             unconsumed=sym[1])))
        else: sys.stderr.write(repr(sym))
