# -*- coding: utf-8 -*-
import io
import requests
from loguru import logger as log
from iscc import audio
from tika import detector


def init():
    """Initialize environmen"""
    log.info("init tika ...")
    detector.from_buffer(io.BytesIO(b"Wakeup Tika"))
    url = detector.ServerEndpoint + "/version"
    resp = requests.get(url)
    log.info("tika initialized: {}".format(resp.text))

    log.info("init fpcalc ...")
    audio.fpcalc_install()
    fpc_version = audio.fpcalc_version_info()
    log.info("fpcalc initialized: {}".format(fpc_version))


if __name__ == "__main__":
    init()
