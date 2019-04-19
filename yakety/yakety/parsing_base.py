#! /usr/bin/env python3

import re

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

def parses(start, s):
    for x in start(s):
        p, rest = x
        if not rest.strip(): yield p


def parse(start, s): return next(parses(start, s))
