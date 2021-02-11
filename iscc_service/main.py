import asyncio
from concurrent.futures.process import ProcessPoolExecutor
from secrets import token_hex
from pathlib import Path
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
import iscc
from starlette.status import HTTP_415_UNSUPPORTED_MEDIA_TYPE
import iscc_service
from iscc_service.config import ALLOWED_ORIGINS
from starlette.middleware.cors import CORSMiddleware
from iscc_service.utils import secure_filename
import aiofiles
from asynctempfile import TemporaryDirectory

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


@app.post("/code_iscc", summary="Generate ISCC from File")
async def code_iscc(
    file: UploadFile = File(...), title: str = Form(""), extra: str = Form("")
):
    """Generate Full ISCC Code from Media File with optional explicit metadata."""

    filename = secure_filename(file.filename) or token_hex(16)

    async with TemporaryDirectory() as tmp_dir:
        tmp_file_path = Path(tmp_dir, filename)

        async with aiofiles.open(tmp_file_path, "wb") as out_file:
            await file.seek(0)
            data = await file.read(4096)
            # Exit Early on unsupported mediatype
            mediatype = iscc.mime_guess(data)
            if not iscc.mime_supported(mediatype):
                raise HTTPException(
                    HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    "Unsupported media type '{}'. Please request support at "
                    "https://github.com/iscc/iscc-service/issues.".format(mediatype),
                )
            while data:
                await out_file.write(data)
                data = await file.read(1024 * 1024)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            app.state.executor, iscc.code_iscc, tmp_file_path, title, extra
        )

        return result


@app.get("/configuration", response_model=iscc.Opts, summary="Show ISCC Service configuration")
def config():
    """Return current ISCC-Service Configuration"""
    return iscc.Opts()


@app.on_event("startup")
async def on_startup():
    app.state.executor = ProcessPoolExecutor()


@app.on_event("shutdown")
async def on_shutdown():
    app.state.executor.shutdown()


def run_server():
    uvicorn.run("iscc_service.main:app", host="127.0.0.1", port=8080, reload=False)


if __name__ == "__main__":
    uvicorn.run("iscc_service.main:app", host="127.0.0.1", port=8080, reload=True)
