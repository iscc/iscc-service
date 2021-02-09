from secrets import token_hex
from loguru import logger
from pathlib import Path
from tempfile import mkdtemp
import shutil
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form
import iscc
import iscc_service
from iscc_service.config import ALLOWED_ORIGINS
from starlette.middleware.cors import CORSMiddleware
from iscc_service.utils import secure_filename


app = FastAPI(
    title="ISCC Web Service API",
    version=iscc_service.__version__,
    description="Microservice for creating ISCC Codes from Media Files.",
    docs_url="/",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post(
    "/generate/from_file", tags=["generate"], summary="Generate ISCC from File",
)
def from_file(
    file: UploadFile = File(...), title: str = Form(""), extra: str = Form("")
):
    """Generate Full ISCC Code from Media File with optional explicit metadata."""

    filename = secure_filename(file.filename) or token_hex(16)
    filepath = Path(mkdtemp(), filename)
    try:
        with filepath.open("wb") as outfile:
            logger.debug(f"Create tempfile at {filepath}")
            shutil.copyfileobj(file.file, outfile)
    finally:
        file.file.close()

    result = iscc.code_iscc(filepath, title=title, extra=extra)

    return result


@app.get("/status/config", response_model=iscc.Opts, tags=["status"])
def config():
    """Return current ISCC-Service Configuration"""
    return iscc.Opts()


def run_server():
    uvicorn.run("iscc_service.main:app", host="127.0.0.1", port=8080, reload=False)


if __name__ == "__main__":
    uvicorn.run("iscc_service.main:app", host="127.0.0.1", port=8080, reload=True)
