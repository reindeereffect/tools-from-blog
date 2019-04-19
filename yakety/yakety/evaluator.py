#! /usr/bin/env python3

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
