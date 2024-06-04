#!/usr/bin/python
from equations import Equation, parse_expr
import struct
import sys


def main():
    if len(sys.argv) < 2:
        print('add output file to arguments')
        sys.exit(1)
    numEquations = int(input('Number of equations> '))
    equations = [input_equation(i + 1) for i in range(numEquations)]
    header = struct.pack('<4sBB', b'\x7fEQU', 0, numEquations)
    payload = header + b''.join([eq.serialize() for eq in equations])
    with open(sys.argv[1], 'wb') as fp:
        fp.write(payload)


def input_equation(index: int) -> Equation:
    print(f'=== equation {index} ===')
    r, g, b = [int(x) for x in input('Color (red green blue)> ').split()]
    expr = input('right side of equation> ')
    action = parse_expr(expr)
    return Equation((r, g, b), action)


if __name__ == '__main__':
    main()
