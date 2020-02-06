import os

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split()
ISCC_STREAM = os.environ.get("ISCC_STREAM", "iscc")
NODE_IP = os.environ.get("NODE_IP", "127.0.0.1")
NODE_PORT = os.environ.get("NODE_PORT", "9718")
NODE_USER = os.environ.get("NODE_USER", "")
NODE_PWD = os.environ.get("NODE_PWD", "")
