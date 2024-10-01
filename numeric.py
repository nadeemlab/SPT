
from math import log2

from attr import define

@define
class SmallFloatByteFormat:
    """
    The specification for a custom floating-point format to fit inside exactly 1 byte, or 8 bits.
    The memory map is:

    - a `fixed_bits`-bit binary integer, F
    - an `exponent_bits`-bit binary integer, E

    and the pair (F, E) is meant to represent exactly the number given by the arithmetic formula:

        ((F / M) + 1) * 2^(E - S) - 2^(-S)

    where:
    - S is the value of `exponent_shift`
    - M is the integer upper bound for F, i.e. 2^(fixed_bits)

    The term ((F / M) + 1) is a linear transformation of the F values, which range
    from 0 to M -1, onto the range 1 to 2. The purpose of this is to ensure that the fixed
    portion does not possibly contain duplicate information as the exponent portion, as in e.g.

        (3) * 2^4 = (6) * 2^3

    The term - 2^(-S) is an offset that ensures that byte 0 encodes 0 rather than the smallest
    denomination 1 * 2 ^ (-S) which would otherwise be the smallest representable value.
    """
    fixed_bits: int
    exponent_bits: int
    exponent_shift: int
    max_fixed: int
    max_exponent: int


def float_format(fixed_bits: int, exponent_bits: int, exponent_shift: int) -> SmallFloatByteFormat:
    """Constructor for the SmallFloatByteFormat specification object."""
    f = SmallFloatByteFormat(
        fixed_bits,
        exponent_bits,
        exponent_shift,
        2**fixed_bits,
        2**exponent_bits,
    )
    bits = f.fixed_bits + f.exponent_bits
    if bits != 8:
        raise ValueError(f'Format requires exactly 8 bits in memory map, not {bits}.')
    return f


def encode(value: float, f: SmallFloatByteFormat) -> bytes:
    """
    Create an approximation of `value` in the 1-byte format specified by `f`.
    `value` should be non-negative and, approximately, less than the largest `f`-representable
    number.
    """
    if value < 0:
        raise OverflowError
    if value == 0:
        exponent_integer = 0
    else:
        exponent_integer = round(log2(value))
    exponent_stored = exponent_integer + f.exponent_shift
    if exponent_stored >= f.max_exponent or exponent_stored < 0:
        raise OverflowError
    nonexponent_part = value / pow(2, exponent_integer)
    precision = f.exponent_bits - 1
    fixed = f.max_fixed * (nonexponent_part - 1)
    fixed_stored = int(fixed)
    if fixed_stored >= f.max_fixed or fixed_stored < 0:
        raise OverflowError
    return ((fixed_stored << f.exponent_bits) + (exponent_stored)).to_bytes()


def decode(byte1: bytes, f: SmallFloatByteFormat) -> float:
    exponent = -f.exponent_shift + (int.from_bytes(byte1) % f.max_exponent)
    fixed = ((int.from_bytes(byte1) >> f.exponent_bits) / f.max_fixed) + 1
    return fixed * pow(2, exponent)


def _print_expression(byte1: bytes, f: SmallFloatByteFormat) -> str:
    exponent = -f.exponent_shift + (int.from_bytes(byte1) % f.max_exponent)
    fixed = ((int.from_bytes(byte1) >> f.exponent_bits) / f.max_fixed) + 1
    expression = f'{str(fixed).ljust(8)} * 2^{exponent}'.ljust(15)
    return f'{expression}   ({int.from_bytes(byte1) >> f.exponent_bits}, {int.from_bytes(byte1)})'


# class SmallFloat:
#     def __init__(self, fixed_bits: int, exponent_bits: int, zero_exponent_code: int):
#         self.f = fixed_bits
#         self.e = exponent_bits
#         self.z = zero_exponent_code

#     def encode(self, value: float) -> bytes:
#         exponent = round(log2(abs(value)))
#         scale = pow(2, self.e)
#         if exponent >= scale - self.z or exponent < -self.z:
#             raise OverflowError
#         nonexponent_part = (value / pow(2, exponent))
#         fixed = round(pow(2, self.p()) * nonexponent_part) / pow(2, self.p())
#         fixed_whole = int(pow(2, self.p()) * fixed)
#         if fixed_whole >= pow(2, self.f) or fixed_whole < 0:
#             raise OverflowError
#         binary = ((fixed_whole << self.e) + (self.z + exponent)).to_bytes()
#         return binary

#     def decode(self, binary: bytes) -> float:
#         exponent = pow(2, -self.z + (int.from_bytes(binary) % pow(2, self.e)))
#         fixed = (int.from_bytes(binary) >> self.e) / pow(2, self.p())
#         return fixed * exponent

#     def p(self):
#         return self.f - 1

# c = SmallFloat(5, 3, 4)
# c.decode(c.encode(11.32))
# c.decode(c.encode(11.3))

def print_table():
    f = float_format(5, 3, 4)
    l = []
    for i in range(256):
        d = decode(i.to_bytes(), f)
        # print((i, d))
        # e = encode(d, f)
        e = 1
        l.append((i, i.to_bytes(), d, e))

    for x in sorted(l, key=lambda t: t[2]):
        print(f'{str(x[0]).ljust(8)} {str(x[1]).ljust(8)} {str(x[2]).ljust(14)} {str(x[3]).ljust(8)} {_print_expression(x[1], f)}')

if __name__=='__main__':
    print_table()
