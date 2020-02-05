import os
import shutil
import uuid
from os.path import join, splitext
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import iscc
from tika import detector, parser
from iscc_cli.const import SUPPORTED_MIME_TYPES, GMT
import iscc_service
from iscc_service.models import (
    Metadata,
    Text,
    ISCC,
    MetaID,
    ContentID,
    DataID,
    InstanceID,
)
from iscc_service.tools import code_to_bits, code_to_int
from pydantic import HttpUrl
from iscc_cli.lib import iscc_from_url
from iscc_cli.utils import iscc_split, get_title, mime_to_gmt
from iscc_cli import APP_DIR, audio_id, video_id
from starlette.middleware.cors import CORSMiddleware
from starlette.status import (
    HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    HTTP_422_UNPROCESSABLE_ENTITY,
)


app = FastAPI(
    title="ISCC Web Service API",
    version=iscc_service.__version__,
    description="Microservice for creating ISCC Codes from Media Files.",
    docs_url="/",
)

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post(
    "/generate/from_file",
    response_model=ISCC,
    response_model_exclude_unset=True,
    tags=["generate"],
    summary="Generate ISCC from File",
)
def from_file(
    file: UploadFile = File(...), title: str = Form(""), extra: str = Form("")
):
    """Generate Full ISCC Code from Media File with optional explicit metadata."""

    media_type = detector.from_buffer(file.file)
    if media_type not in SUPPORTED_MIME_TYPES:
        raise HTTPException(
            HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Unsupported media type '{}'. Please request support at "
            "https://github.com/iscc/iscc-service/issues.".format(media_type),
        )

    file.file.seek(0)
    tika_result = parser.from_buffer(file.file)

    if not title:
        title = get_title(tika_result, guess=True)

    mid, norm_title, norm_extra = iscc.meta_id(title, extra)
    gmt = mime_to_gmt(media_type)
    if gmt == GMT.IMAGE:
        file.file.seek(0)
        cid = iscc.content_id_image(file.file)
    elif gmt == GMT.TEXT:
        text = tika_result["content"]
        if not text:
            raise HTTPException(HTTP_422_UNPROCESSABLE_ENTITY, "Could not extract text")
        cid = iscc.content_id_text(tika_result["content"])
    elif gmt == GMT.AUDIO:
        file.file.seek(0)
        features = audio_id.get_chroma_vector(file.file)
        cid = audio_id.content_id_audio(features)
    elif gmt == GMT.VIDEO:
        file.file.seek(0)
        _, ext = splitext(file.filename)
        fn = "{}{}".format(uuid.uuid4(), ext)
        tmp_path = join(APP_DIR, fn)
        with open(tmp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        features = video_id.get_frame_vectors(tmp_path)
        cid = video_id.content_id_video(features)
        os.remove(tmp_path)

    file.file.seek(0)
    did = iscc.data_id(file.file)
    file.file.seek(0)
    iid, tophash = iscc.instance_id(file.file)

    if not norm_title:
        iscc_code = "-".join((cid, did, iid))
    else:
        iscc_code = "-".join((mid, cid, did, iid))

    components = iscc_split(iscc_code)

    result = dict(
        iscc=iscc_code,
        tophash=tophash,
        gmt=gmt,
        bits=[code_to_bits(c) for c in components],
    )
    if norm_title:
        result["title"] = title
        result["title_trimmed"] = norm_title
    if norm_extra:
        result["extra"] = extra
        result["extra_trimmed"] = norm_extra

    file.file.close()
    return result


@app.post(
    "/generate/from_url",
    response_model=ISCC,
    tags=["generate"],
    summary="Generate ISCC from URL",
)
def from_url(url: HttpUrl):
    """Generate Full ISCC from URL."""
    result = iscc_from_url(url, guess=True)
    result["title"] = result.pop("norm_title")
    result["title_trimmed"] = result["title"]
    components = iscc_split(result["iscc"])
    result["bits"] = [code_to_bits(c) for c in components]
    return result


@app.post(
    "/generate/meta_id/",
    response_model=MetaID,
    response_model_exclude_unset=True,
    tags=["generate"],
    summary="Generate ISCC Meta-ID",
)
def meta_id(meta: Metadata):
    """Generate MetaID from 'title' and optional 'extra' metadata"""
    extra = meta.extra or ""
    mid, title_trimmed, extra_trimmed = iscc.meta_id(meta.title, extra)
    result = {
        "code": mid,
        "bits": code_to_bits(mid),
        "ident": code_to_int(mid),
        "title": meta.title,
        "title_trimmed": title_trimmed,
    }

    if extra:
        result["extra"] = extra
        result["extra_trimmed"] = extra_trimmed

    return result


@app.post(
    "/generate/content_id_text",
    response_model=ContentID,
    tags=["generate"],
    summary="Generate ISCC Content-ID-Text",
)
def content_id_text(text: Text):
    """Generate ContentID-Text from 'text'"""
    cid_t = iscc.content_id_text(text.text)
    return {
        "gmt": "text",
        "bits": code_to_bits(cid_t),
        "code": cid_t,
        "ident": code_to_int(cid_t),
    }


@app.post(
    "/generate/data_id",
    response_model=DataID,
    tags=["generate"],
    summary="Generate ISCC Data-ID",
)
def data_id(file: UploadFile = File(...)):
    """Generate Data-ID from raw binary data"""
    did = iscc.data_id(file.file)
    return {"code": did, "bits": code_to_bits(did), "ident": code_to_int(did)}


@app.post(
    "/generate/instance_id",
    response_model=InstanceID,
    tags=["generate"],
    summary="Generate ISCC Instance-ID",
)
def instance_id(file: UploadFile = File(...)):
    """Generate Instance-ID from raw binary data"""
    iid, tophash = iscc.instance_id(file.file)
    return {
        "code": iid,
        "bits": code_to_bits(iid),
        "ident": code_to_int(iid),
        "tophash": tophash,
    }


@app.post(
    "/generate/data_instance_id",
    tags=["generate"],
    summary="Generate ISCC Data-ID and Instance-ID",
)
def data_and_instance_id(file: UploadFile = File(...,)):
    """Generate Data-ID and Instance-ID from raw binary data"""

    did = iscc.data_id(file.file)
    file.file.seek(0)
    iid, tophash = iscc.instance_id(file.file)
    return {
        "data_id": {"code": did, "bits": code_to_bits(did), "ident": code_to_int(did),},
        "instance_id": {
            "code": iid,
            "bits": code_to_bits(iid),
            "ident": code_to_int(iid),
            "tophash": tophash,
        },
    }


if __name__ == "__main__":
    uvicorn.run("iscc_service.main:app", host="127.0.0.1", port=8000, reload=True)
