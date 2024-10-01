
from math import log2

def encode(value: float) -> bytes:
    exponent = round(log2(abs(value)))
    exponent = min(exponent, 3)
    exponent = max(-4, exponent)
    nonexponent_part = (value / pow(2, exponent))
    fixed = round(pow(2,4) * nonexponent_part) / pow(2,4)
    fixed_whole = int(pow(2,4) * fixed)
    fixed_whole = min(fixed_whole, 32)
    binary = ((fixed_whole << 3) + (4 + exponent)).to_bytes()
    print(bin(int.from_bytes(binary)))
    return binary


def decode(binary: bytes) -> float:
    exponent = pow(2, -4 + (int.from_bytes(binary) % pow(2, 3)))
    fixed = (int.from_bytes(binary) >> 3) / pow(2,4)
    return fixed * exponent



class SmallFloat:
    def __init__(self, fixed_bits: int, exponent_bits: int, zero_exponent_code: int):
        self.f = fixed_bits
        self.e = exponent_bits
        self.z = zero_exponent_code

    def encode(self, value: float) -> bytes:
        exponent = round(log2(abs(value)))
        scale = pow(2, self.e)
        if exponent >= scale - self.z or exponent < -self.z:
            raise OverflowError
        nonexponent_part = (value / pow(2, exponent))
        fixed = round(pow(2, self.p()) * nonexponent_part) / pow(2, self.p())
        fixed_whole = int(pow(2, self.p()) * fixed)
        if fixed_whole >= pow(2, self.f) or fixed_whole < 0:
            raise OverflowError
        binary = ((fixed_whole << self.e) + (self.z + exponent)).to_bytes()
        return binary

    def decode(self, binary: bytes) -> float:
        exponent = pow(2, -self.z + (int.from_bytes(binary) % pow(2, self.e)))
        fixed = (int.from_bytes(binary) >> self.e) / pow(2, self.p())
        return fixed * exponent

    def p(self):
        return self.f - 1

c = SmallFloat(5, 3, 4)
c.decode(c.encode(11.32))
c.decode(c.encode(11.3))
    
l = []
for i in range(256):
    l.append((i, i.to_bytes(), c.decode(i.to_bytes())))

for x in sorted(l, key=lambda t: t[2]):
    print(f'{str(x[0]).ljust(8)} {str(x[1]).ljust(8)} {str(x[2]).ljust(8)}')

