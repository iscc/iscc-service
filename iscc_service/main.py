import os
import shutil
import uuid
from os.path import join, splitext
from typing import List, Optional
import mobi
import uvicorn
import uvarint
from fastapi import FastAPI, Query, UploadFile, File, Form, HTTPException
import iscc
from iscc_cli.tika import detector, parser
from iscc_cli.const import SUPPORTED_MIME_TYPES, GMT
import iscc_service
from iscc_service.config import ALLOWED_ORIGINS, ISCC_STREAM
from iscc_service.conn import get_client
from iscc_service.models import (
    Chain,
    Metadata,
    ShortID,
    Text,
    ISCC,
    MetaID,
    ContentID,
    DataID,
    InstanceID,
    StreamItem,
)
from iscc_service.tools import (
    code_to_bits,
    code_to_int,
    stream_filter,
    add_placeholders,
)
from pydantic import HttpUrl
from iscc_cli.lib import iscc_from_url
from iscc_cli.utils import iscc_split, get_title, mime_to_gmt, iscc_verify
from iscc_cli import APP_DIR, audio_id, video_id
from starlette.middleware.cors import CORSMiddleware
from starlette.status import (
    HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_503_SERVICE_UNAVAILABLE,
    HTTP_400_BAD_REQUEST,
)


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

    if media_type == "application/x-mobipocket-ebook":
        file.file.seek(0)
        tempdir, filepath = mobi.extract(file.file)
        tika_result = parser.from_file(filepath)
        shutil.rmtree(tempdir)
    else:
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
    iscc_raw = "".join([iscc.decode(code).hex() for code in components])

    result = dict(
        iscc=iscc_code,
        iscc_raw=iscc_raw,
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


@app.post(
    "/generate/short_id",
    response_model=ShortID,
    tags=["generate"],
    summary="Generate ISCC Short-ID",
)
def short_id(
    chain: Chain, iscc_code: str, counter: Optional[int] = Query(0, ge=0, le=127)
):
    """Generate Short-ID from 'chain', 'iscc_code', and 'counter'"""
    components = iscc_split(iscc_code)
    # First 7 bytes (including header) of all but Instance-ID
    digests = [iscc.decode(c)[:7] for c in components if not c.startswith("CR")]
    iscc_id_body = iscc.similarity_hash(digests)
    sid = iscc.encode(chain.code + iscc_id_body + uvarint.encode(counter))
    return dict(short_id=sid, chain=chain.name, counter=counter)


@app.get(
    "/lookup",
    response_model=List[StreamItem],
    tags=["lookup"],
    summary="Lookup ISCC Codes",
)
def lookup(iscc: str):
    """Lookup an ISCC Code"""
    client = get_client()
    if client is None:
        raise HTTPException(
            HTTP_503_SERVICE_UNAVAILABLE, "ISCC lookup service not available"
        )
    try:
        iscc_verify(iscc)
    except ValueError as e:
        raise HTTPException(HTTP_400_BAD_REQUEST, str(e))

    components = iscc_split(iscc)
    results = []
    seen = set()
    for component in components:
        response = client.liststreamkeyitems(ISCC_STREAM, component, True, 100, 0, True)
        for result in response:
            txid = result.get("txid")
            if txid is None or txid in seen:
                continue
            results.append(result)
            seen.add(txid)
    result = stream_filter.search(results)
    cleaned = []
    for entry in result:
        keys = entry["keys"]
        # Better be conservative until we have a similarity based index.
        # So for now we only match if at least two components are identical.
        matches = set(keys).intersection(set(components))
        if not len(matches) >= 2:
            continue
        keys = add_placeholders(keys)

        entry["bits"] = [code_to_bits(c) for c in keys]
        while len(entry["bits"]) < 4:
            entry["bits"].append("0" * 64)
        cleaned.append(entry)
    return cleaned


def run_server():
    uvicorn.run("iscc_service.main:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    uvicorn.run("iscc_service.main:app", host="127.0.0.1", port=8000, reload=True)
