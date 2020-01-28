# -*- coding: utf-8 -*-
import iscc
from bitstring import BitArray


def code_to_bits(code: str) -> str:
    """Convert ISCC Code to bitstring"""
    data = iscc.decode(code)
    ba = BitArray(data[1:])
    return ba.bin


def code_to_int(code: str) -> int:
    """Convert ISCC Code to integer"""
    data = iscc.decode(code)
    ba = BitArray(data[1:])
    return ba.uint


if __name__ == "__main__":
    print(code_to_bits("CCDFPFc87MhdT"))
    print(code_to_int("CCDFPFc87MhdT"))
