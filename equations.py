import struct
from dataclasses import dataclass


__all__ = ('Action', 'VariableX', 'Constant', 'BinOp', 'Add', 'Sub', 'Mul', 'Div', 'Power', 'parse_expr')


class Action:
    @staticmethod
    def parse_bin(source):
        if len(source) > 0:
            opcode = source[0]
            if opcode == 0:
                # X
                return VariableX(), source[1:]
            elif opcode == 1:
                value = struct.unpack('<f', source[1:5])[0]
                return Constant(value), source[5:]
            elif opcode < 7:
                binop = BINOP_OPCODES[opcode]
                arg_a, source = Action.parse_bin(source[1:])
                arg_b, remainder = Action.parse_bin(source)
                return binop(arg_a, arg_b), remainder
            else:
                raise ValueError('Bad opcode byte')

    def eval(self, x: float) -> float:
        raise NotImplementedError()

    def serialize(self) -> bytes:
        raise NotImplementedError()


class VariableX(Action):
    def eval(self, x: float) -> float:
        return x

    def serialize(self) -> bytes:
        return bytes([0])


class Constant(Action):
    val: float

    def __init__(self, val: float):
        self.val = val

    def eval(self, x: float) -> float:
        return self.val

    def serialize(self) -> bytes:
        return struct.pack('<Bf', 1, self.val)


class BinOp(Action):
    a: Action
    b: Action
    ID_BYTE: int

    def __init__(self, a: Action, b: Action):
        self.a = a
        self.b = b

    def eval(self, x: float) -> float:
        return self.operator(self.a.eval(x), self.b.eval(x))

    @staticmethod
    def operator(a: float, b: float) -> float:
        raise NotImplementedError()

    def serialize(self) -> bytes:
        return bytes([self.ID_BYTE]) + self.a.serialize() + self.b.serialize()


class Add(BinOp):
    ID_BYTE = 2

    @staticmethod
    def operator(a: float, b: float) -> float:
        return a + b


class Sub(BinOp):
    ID_BYTE = 3

    @staticmethod
    def operator(a: float, b: float) -> float:
        return a - b


class Mul(BinOp):
    ID_BYTE = 4

    @staticmethod
    def operator(a: float, b: float) -> float:
        return a * b


class Div(BinOp):
    ID_BYTE = 5

    @staticmethod
    def operator(a: float, b: float) -> float:
        return a / b


class Power(BinOp):
    ID_BYTE = 6

    @staticmethod
    def operator(a: float, b: float) -> float:
        return a ** b


BINOP_OPCODES = {2: Add, 3: Sub, 4: Mul, 5: Div, 6: Power}


@dataclass
class Equation:
    color: tuple[int, int, int]
    action: Action

    def serialize(self):
        action = self.action.serialize()
        return struct.pack('<HBBB', len(action), *self.color) + action

    @staticmethod
    def parse_bin(source: bytes):
        length, r, g, b = struct.unpack('<HBBB', source[:5])
        remainder = source[length + 5:]
        action = Action.parse_bin(source[5:length + 5])
        return Equation((r, g, b), action[0]), remainder


def parse_expr(source):
    tokens = tokenize(source)
    tokens, result = parse_sum(tokens)
    if len(tokens) > 0:
        raise Exception('Error in expression')
    return result


TOKENS = ('x', '+', '-', '*', '/', '^', '(', ')')


def tokenize(source: str) -> list[str]:
    result = []
    token = None
    currentType = None
    for ch in source:
        if ch.isspace():
            if token is not None:
                result.append(token)
                token = None
        elif ch in TOKENS:
            if token is not None:
                result.append(token)
                token = None
            result.append(ch)
        elif ch.isnumeric() or ch == '.':
            if token is None:
                token = ch
            else:
                token += ch
        else:
            raise Exception('Error in expression')
    if token is not None:
        result.append(token)
    return result


def parse_sum(tokens: list[str]) -> tuple[list[str], Action]:
    tokens, result = parse_mul(tokens)
    while len(tokens) > 0 and tokens[0] in ('+', '-'):
        op = tokens[0]
        tokens, rhs = parse_mul(tokens[1:])
        if op == '+':
            result = Add(result, rhs)
        elif op == '-':
            result = Sub(result, rhs)
    return tokens, result


def parse_mul(tokens: list[str]) -> tuple[list[str], Action]:
    tokens, result = parse_power(tokens)
    while len(tokens) > 0 and tokens[0] in ('*', '/'):
        op = tokens[0]
        tokens, rhs = parse_power(tokens[1:])
        if op == '*':
            result = Mul(result, rhs)
        elif op == '/':
            result = Div(result, rhs)
    return tokens, result


def parse_power(tokens: list[str]) -> tuple[list[str], Action]:
    tokens, result = parse_unary_minus(tokens)
    while len(tokens) > 0 and tokens[0] == '^':
        op = tokens[0]
        tokens, rhs = parse_unary_minus(tokens[1:])
        result = Power(result, rhs)
    return tokens, result


def parse_unary_minus(tokens: list[str]) -> tuple[list[str], Action]:
    if tokens[0] == '-':
        return Sub(Constant(0), parse_unary_minus(tokens[1:]))
    else:
        return parse_atom(tokens)


def parse_atom(tokens: list[str]) -> tuple[list[str], Action]:
    if tokens[0] == '(':
        tokens, result = parse_sum(tokens[1:])
        if tokens[0] == ')':
            return tokens[1:], result
        else:
            raise Exception('Error in expression')
    elif tokens[0] == 'x':
        return tokens[1:], VariableX()
    else:
        return tokens[1:], Constant(float(tokens[0]))
