#! /usr/bin/env python3

from parsing_base import *

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

def parses2(start, s):
    for x in start(s):
        p, rest = x
        if not rest.strip(): yield p
        elif not skip_comment(rest.strip()): yield p
            


def parse2(start, s): return next(parses2(start, s))

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

@parser
def directive(s):
    'directive : EXCLAMATION IGNORE REGEX'
    return seq(EXCLAMATION, IGNORE, REGEX)(s)

@parser
def EXCLAMATION(s):
    return literal2('!', s)

@parser
def IGNORE(s):
    return literal2('ignore', s)

@parser
def directives(s):
    return rep(directive)(s)

@parser
def ebnf(s):
    return seq(directives, rules)(s)
