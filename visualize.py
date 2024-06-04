#!/usr/bin/python
from equations import Equation
from matplotlib import pyplot as plt
import sys
import struct


def main():
    with open(sys.argv[1], 'rb') as fp:
        data = fp.read()
    start, end, step = [float(x) for x in sys.argv[2:5]]

    xs = []
    x = start
    while x <= end:
        xs.append(x)
        x += step

    signature, ver, numEquations = struct.unpack('<4sBB', data[:6])
    if signature != b'\x7fEQU' or ver != 0:
        print('Bad file format')
        sys.exit(1)
    data = data[6:]

    for i in range(numEquations):
        equation, data = Equation.parse_bin(data)
        ys = [equation.action.eval(x) for x in xs]
        plt.plot(xs, ys, color=tuple(x / 255 for x in equation.color))

    if len(data) != 0:
        print('Bad file format')
        sys.exit(1)

    plt.show()


if __name__ == '__main__':
    main()
