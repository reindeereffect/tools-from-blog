#! /usr/bin/env python3

from yakety import *
from yakety.evaluator import *

import operator as ops

class asdf_interpreter:
    '''
    ! ignore /\s+/
    ! ignore /#[^\n]*/

    statements     : {statement}
    
    statement      : print 
                   | loop 
                   | conditional
                   | assignment 
                   | expression
    
    assignment     : IDENTIFIER '=' expression
    expression     : term {/[+-]/ term}
    term           : factor {/[%*\/]/ factor}
    
    factor         : reference 
                   | NUMBER 
                   | enclosed
    
    reference      : IDENTIFIER
    enclosed       : '(' expression ')'
    print          : 'print' (expression | STRING_LITERAL)
    loop           : WHILE expression statements 'end'
    conditional    : IF expression statements 'end'
    NUMBER         : /[-]?[0-9]+/
    STRING_LITERAL : /\'(\\.|[^\\'])*\'/

    # it's critical that IDENTIFIER not pick up any reserved words
    
    IDENTIFIER     : /(?!print|while|if|end)[a-zA-Z_][a-zA-Z_0-9]*/
    
    # we'll put a handler on these introductions so we have the opportunity
    # to operate the 'skip' mechanism and control evaluation of the bodies
    
    WHILE          : 'while'
    IF             : 'if'
    '''

    def __init__(self):
        self.calc = calc = evaluator()
        self.parse = Parser(self.__class__.__doc__)
        self.vars = {}
        
        @calc.on('reference')
        def h_reference(name): return self.vars[name.value]
            
        @calc.on('NUMBER')
        def h_NUMBER(p): return int(p)
            
        @calc.on('enclosed')
        def h_enclose(_, inside, __): return inside.result
            
        @calc.on('factor')
        def h_factor(p): return p.result
        
        @calc.on('term')
        @calc.on('expression')
        def h_apply_ops(first, rest):
            OP = {'+': ops.add, '-': ops.sub, 
                  '*': ops.mul, '/': ops.truediv, '%': ops.mod}

            acc = first.result
            
            for (op, mag) in rest: 
                acc = OP[op.value](acc, mag.result)
            
            return acc
            
        @calc.on('STRING_LITERAL')
        def h_STRING_LITERAL(s): return s[1:-1]
                        
        @calc.on('assignment')
        def h_assignment(name, _, val): 
            self.vars[name.value] = val.result

        @calc.on('print')
        def h_print(_, out): print(out.result)
            
        @calc.on('WHILE')
        @calc.on('IF')
        def h_compound_intro(_): calc.skip = -1
            
        @calc.on('conditional')
        def h_conditional(_, cond, conseq, __):
            if calc(cond): calc(conseq)
                
        @calc.on('loop')
        def h_loop(_, test, body, end):
            while calc(test): calc(body)
            
    def __call__(self, prog): self.calc(self.parse(prog))


ASDF = asdf_interpreter()

fizzbuzz = '''
i = 1

while 101 - i
    fizz = 1
    buzz = 1
    emit = 1
    
    if i % 3
        fizz = 0
    end
    
    if i % 5
        buzz = 0
    end
    
    if fizz * buzz
        fizz = 0
        buzz = 0
        emit = 0
        print 'FizzBuzz'
    end

    if fizz
        emit = 0
        print 'Fizz'
    end
    
    if buzz
        buzz = 0
        emit = 0
        print 'Buzz'
    end

    if emit
        print i
        emit = 0
    end
    i = i + 1
end
'''

ASDF(fizzbuzz)

