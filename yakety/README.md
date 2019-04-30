usage: ykt [-h] [-j] grammar

Use an EBNF grammar to parse STDIN, sending the parse tree to STDOUT.

positional arguments:
  grammar     EBNF grammar file

optional arguments:
  -h, --help  show this help message and exit
  -j, --json  emit JSON

Yakety is a simple Extended Backus-Nauer Form (EBNF) recursive descent parser
generator. Its specification language is described in yakety.ykt, in the examples
directory of this distribution.
