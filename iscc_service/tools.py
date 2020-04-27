# -*- coding: utf-8 -*-
import iscc
import jmespath
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


stream_filter = jmespath.compile(
    "[].{txid: txid, vout: vout, keys: keys, title: data.json.title, tophash:data.json.tophash, extra:data.json.extra, time: time, content_url: data.json.meta[0].data.encoding[0].contentUrl}"
)


def add_placeholders(components):
    """Add placeholders for missing DATA/INSTANCE components"""
    headers = [s[:2] for s in components]
    for prefix in ("CD", "CR"):
        if prefix not in headers:
            components.append(prefix + ("C" * 11))
    return components


if __name__ == "__main__":
    print(code_to_bits("CCDFPFc87MhdT"))
    print(code_to_int("CCDFPFc87MhdT"))
