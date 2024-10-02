"""Custom 8-bit floats."""

from math import log2

from attr import define
from attr import fields as attrs_fields
from pandas import DataFrame


@define
class SmallFloatByteFormat:
    """
    The specification for a custom floating-point format to fit inside exactly 1 byte, or 8 bits.

    The basic idea is to represent numbers of the form:
    
        (fixed part) * 2^(exponent part)

    where the fixed part and the exponent part are encodeable as binary integers. The encoding that
    we actually do is not simply to make the fixed part and exponent part literally integers,
    because we want the floating-point scheme to have a favorable distribution.
            
    The memory map is:

    - a `fixed_bits`-bit binary integer, F
    - an `exponent_bits`-bit binary integer, E

    The pair (F, E) then represents exactly the number given by the arithmetic formula:

        A * [ ((F / M) + 1) * 2^(E - S) - 2^(-S) ]

    where:
    - S is the value of `exponent_shift`
    - M is the integer upper bound for F, i.e. 2^(fixed_bits)
    - A is a constant scale factor that ensures that the largest value that occurs is 1

    The term ((F / M) + 1) is a linear transformation of the F values, which range
    from 0 to M-1, onto the range 1 to 2. The purpose of this is to ensure that the fixed
    portion does not possibly contain duplicate information as the exponent portion, as in e.g.

        (3) * 2^4 = (6) * 2^3

    The term - 2^(-S) is an offset that ensures that byte 0 encodes 0 rather than the smallest
    denomination 1 * 2 ^ (-S), which would otherwise be the smallest representable value.

    The `test` area has a table of extended metadata and a flat lookup table for the encoding of
    this type which we use as the default (fixed_bits = 5, exponent_bits = 3, exponent_shift = 2)
    That area also has a script to generate distribution plots to compare the possible formats.
    
    Note that the exponent shift is not very important, since the overall scale factor `A` was
    introduced. The purpose of the shift was to do such a scaling, but the problem with that was
    that the highest value was only approximately, and not exactly, equal to a round power-of-2
    integer.
    """
    fixed_bits: int
    exponent_bits: int
    exponent_shift: int
    max_fixed: int
    max_exponent: int
    lowest_denomination: float
    scale_adjustment: float


def float_format(exponent_bits: int, exponent_shift: int) -> SmallFloatByteFormat:
    """Constructor for the SmallFloatByteFormat specification object."""
    if exponent_bits >= 8:
        raise ValueError(f'This format requires exactly 8 bits in memory map, and {exponent_bits} '
                          'exponent bits leave no room for the fixed portion.')
    if exponent_bits < 1:
        raise ValueError(f'This format requires at least 1 bit for encoding the exponent.')
    fixed_bits = 8 - exponent_bits
    highest = (1 + (-1 + (2**fixed_bits)) / (2**fixed_bits)) * 2**(2**exponent_bits - 1 - exponent_shift) - 2**(-1 * exponent_shift)
    f = SmallFloatByteFormat(
        fixed_bits,
        exponent_bits,
        exponent_shift,
        2**fixed_bits,
        2**exponent_bits,
        2**(-1 * exponent_shift),
        1.0 / highest,
    )
    return f


SMALL_FLOAT_FORMAT = float_format(3, 2)


def encode(value: float, f: SmallFloatByteFormat) -> bytes:
    """
    Create an approximation of `value` in the 1-byte format specified by `f`.
    `value` should be non-negative and less than or equal to the largest `f`-representable number.
    """
    _value = (f.lowest_denomination + (value / f.scale_adjustment))
    if _value < 0:
        raise OverflowError
    exponent_integer = round(log2(_value))
    nonexponent_part = _value / pow(2, exponent_integer)
    while nonexponent_part < 1:
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
    """
    Expand the `f`-encoded float.
    """
    exponent = -f.exponent_shift + (int.from_bytes(byte1) % f.max_exponent)
    fixed = ((int.from_bytes(byte1) >> f.exponent_bits) / f.max_fixed) + 1
    return (fixed * pow(2, exponent) - f.lowest_denomination) * f.scale_adjustment


@define
class SmallFloatMetadata:
    integer: int
    byte1: bytes
    decoded_value: float
    recoded: bytes
    recoded_integrity: bool
    expression: str
    fixed_integer: int
    exponent_integer: int


def _expand_metadata(s: SmallFloatMetadata) -> tuple:
    return tuple(map(
        lambda field: getattr(s, getattr(field, 'name')),
        attrs_fields(SmallFloatMetadata,
    )))


def _get_expression(byte1: bytes, f: SmallFloatByteFormat) -> str:
    exponent = -f.exponent_shift + (int.from_bytes(byte1) % f.max_exponent)
    fixed = ((int.from_bytes(byte1) >> f.exponent_bits) / f.max_fixed) + 1
    return f'(scale) * [{str(fixed).ljust(8)} * 2^{exponent} - lowest value]'


def _get_fixed_integer(byte1: bytes, f: SmallFloatByteFormat) -> int:
    return int.from_bytes(byte1) >> f.exponent_bits


def _get_exponent_integer(byte1: bytes, f: SmallFloatByteFormat) -> int:
    return int.from_bytes(byte1) % f.max_exponent


def generate_metadata_table(f: SmallFloatByteFormat) -> tuple[list[SmallFloatMetadata], DataFrame]:
    rows: list[SmallFloatMetadata] = []
    for i in range(256):
        value = decode(i.to_bytes(), f)
        recoded = encode(value, f)
        s = SmallFloatMetadata(
            i,
            i.to_bytes(),
            value,
            recoded,
            recoded == i.to_bytes(),
            _get_expression(i.to_bytes(), f),
            _get_fixed_integer(i.to_bytes(), f),
            _get_exponent_integer(i.to_bytes(), f),
        )
        rows.append(s)
    rows = sorted(rows, key=lambda s: s.decoded_value)
    tuple_rows = [_expand_metadata(r) for r in rows]
    c = list(map(lambda field: getattr(field, 'name'), attrs_fields(SmallFloatMetadata)))
    df = DataFrame(tuple_rows, columns=c)
    return rows, df
