#!/usr/bin/env python2

import sys

if len(sys.argv) == 1:
    print('''usage: parse_expr.py <filename> ...
   Example: parse_expr.py Hello.java Hello2.java ''')
    sys.exit(1)

import parser as plyj

parser = plyj.Parser()
for filename in sys.argv[1:]:
    parsed = parser.parse_file(filename)
    print(parsed)
    print(parsed.__dict__)
