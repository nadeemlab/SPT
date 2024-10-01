
from math import log2
import re
from json import dumps as json_dumps

from attr import define
from attr import fields as attrs_fields
from pandas import DataFrame


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
    lowest_denomination: float


def float_format(fixed_bits: int, exponent_bits: int, exponent_shift: int) -> SmallFloatByteFormat:
    """Constructor for the SmallFloatByteFormat specification object."""
    f = SmallFloatByteFormat(
        fixed_bits,
        exponent_bits,
        exponent_shift,
        2**fixed_bits,
        2**exponent_bits,
        2**(-1 * exponent_shift),
    )
    bits = f.fixed_bits + f.exponent_bits
    if bits != 8:
        raise ValueError(f'Format requires exactly 8 bits in memory map, not {bits}.')
    return f


# SMALL_FLOAT_FORMAT = float_format(5, 3, 4)
SMALL_FLOAT_FORMAT = float_format(6, 2, 2)


def encode(value: float, f: SmallFloatByteFormat) -> bytes:
    """
    Create an approximation of `value` in the 1-byte format specified by `f`.
    `value` should be non-negative and, approximately, less than the largest `f`-representable
    number.
    """
    _value = f.lowest_denomination + value
    if _value <= 0:
        raise OverflowError
    exponent_integer = round(log2(_value))
    nonexponent_part = _value / pow(2, exponent_integer)
    if nonexponent_part < 1:
        exponent_integer -= 1
        nonexponent_part = _value / pow(2, exponent_integer)

    exponent_stored = exponent_integer + f.exponent_shift
    if exponent_stored >= f.max_exponent or exponent_stored < 0:
        raise OverflowError
    fixed = f.max_fixed * (nonexponent_part - 1)
    fixed_stored = int(fixed)
    if fixed_stored >= f.max_fixed or fixed_stored < 0:
        raise OverflowError
    return ((fixed_stored << f.exponent_bits) + (exponent_stored)).to_bytes()


def decode(byte1: bytes, f: SmallFloatByteFormat) -> float:
    exponent = -f.exponent_shift + (int.from_bytes(byte1) % f.max_exponent)
    fixed = ((int.from_bytes(byte1) >> f.exponent_bits) / f.max_fixed) + 1
    return fixed * pow(2, exponent) - f.lowest_denomination


@define
class SmallFloatMetadata:
    integer: int
    byte1: bytes
    decoded_value: float
    recoded: bytes
    recoded_integrity: bool
    expression: str


def expand_metadata(s: SmallFloatMetadata) -> tuple:
    return (s.integer, s.byte1, s.decoded_value, s.recoded, s.recoded_integrity, s.expression)


def get_expression(byte1: bytes, f: SmallFloatByteFormat) -> str:
    exponent = -f.exponent_shift + (int.from_bytes(byte1) % f.max_exponent)
    fixed = ((int.from_bytes(byte1) >> f.exponent_bits) / f.max_fixed) + 1
    return f'{str(fixed).ljust(8)} * 2^{exponent} - lowest value'


def generate_whole_table(f: SmallFloatByteFormat) -> tuple[list[SmallFloatMetadata], DataFrame]:
    rows: list[SmallFloatMetadata] = []
    for i in range(256):
        s = SmallFloatMetadata(
            i,
            i.to_bytes(),
            decode(i.to_bytes(), f),
            encode(decode(i.to_bytes(), f), f),
            encode(decode(i.to_bytes(), f), f) == i.to_bytes(),
            get_expression(i.to_bytes(), f),
        )
        rows.append(s)
    rows = sorted(rows, key=lambda s: s.decoded_value)
    tuple_rows = [expand_metadata(r) for r in rows]
    df = DataFrame(tuple_rows, columns=list(map(lambda field: field.name, attrs_fields(SmallFloatMetadata))))
    return rows, df


def print_javascript_lookup() -> None:
    rows, df = generate_whole_table(SMALL_FLOAT_FORMAT)
    def format_bin(integer: int):
        return bin(integer)[2:].rjust(8, '0')
    data = json_dumps(dict(map(lambda row: (format_bin(row.integer), row.decoded_value), rows)), indent=4)
    data = 'var lookup = ' + re.sub('"([01]+)"', r'0b\1' , data)
    print(data)


def print_table() -> None:
    rows, df = generate_whole_table(SMALL_FLOAT_FORMAT)
    print(df.to_string())


if __name__=='__main__':
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == 'javascript':
            print_javascript_lookup()
            sys.exit()
    print_table()
