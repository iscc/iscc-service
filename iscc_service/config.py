import os

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split()
