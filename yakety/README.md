# Yakety

Yakety is a recursive descent parser generator for EBNF grammars. It is based
on the code from the article [Recursive Descent: The Next Iteration](https://reindeereffect.github.io/2019/01/16/recursive-descent-part2/), which
also discusses its principles of operation.

Included are:

* yakety: a Python module for generating parsers from grammars
* yakety.evaluator: provides an evaluator for parse trees, with a simple
interface for registering symbol handlers
* bin/ykt: a command line wrapper for yakety, allowing easy creation of parsers
that emit parse trees to stdout (optionally in JSON)
* bin/dotify: a tool for converting JSON-formatted parse trees produced by
ykt parsers to Graphviz dot syntax
* a collection of examples, including an implementation of FizzBuzz and a 
grammar for Yakety itself

N.B.: dotify is actually derived from library used to produce the parse tree
diagrams in the referenced article. None of its code actually appears in the
article itself.
