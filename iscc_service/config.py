import os

ALLOWED_ORIGINS = os.environ.get("ISCC_SERVICE_ALLOWED_ORIGINS", "*").split()
