# -*- coding: utf-8 -*-
from loguru import logger
import mcrpc

from iscc_service.config import NODE_IP, NODE_PORT, NODE_USER, NODE_PWD


client = None


def get_client():
    global client
    if client is not None:
        return client
    conn = mcrpc.RpcClient(NODE_IP, NODE_PORT, NODE_USER, NODE_PWD)
    try:
        info = conn.getblockchaininfo()
        logger.debug("Connected to {}".format(info))
        client = conn
        return conn
    except Exception as e:
        logger.warning("No connection to blockchain node: {}".format(e))
        return None


if __name__ == "__main__":
    main()
