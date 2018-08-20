#!/usr/bin/python

import sys
import argparse

print (sys.argv[0])

if len(sys.argv) == 2:
    print("tem argumento")

parser = argparse.ArgumentParser()

parser.add_argument('-n', action='store', dest='simple_value',
                    help='Store a simple value')

results = parser.parse_args()
if results.simple_value:
    print('simple_value =', results.simple_value)
