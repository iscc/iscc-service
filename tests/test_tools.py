# -*- coding: utf-8 -*-
from iscc_service import tools


def test_add_placeholders():
    c = ["CCD277vDVpwNR", "CAd3AuPU1brqV"]
    r = tools.add_placeholders(c)
    assert r == ["CCD277vDVpwNR", "CAd3AuPU1brqV", "CDCCCCCCCCCCC", "CRCCCCCCCCCCC"]
