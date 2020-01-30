import os
import uuid
from os.path import join, splitext

import uvicorn
from fastapi import FastAPI, UploadFile, File
import iscc
from starlette.responses import RedirectResponse

from iscc_service.tools import code_to_bits, code_to_int
from pydantic import BaseModel, Field, HttpUrl
from iscc_cli.lib import iscc_from_file, iscc_from_url
from iscc_cli.utils import iscc_split
from iscc_cli import APP_DIR
from starlette.middleware.cors import CORSMiddleware


app = FastAPI()

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Meta(BaseModel):
    title: str = Field("", description="The title of an intangible creation.")
    extra: str = Field(
        "",
        description="An optional short statement that distinguishes "
        "this intangible creation from another one for the "
        "purpose of forced Meta-ID uniqueness.",
    )


class Text(BaseModel):
    text: str = Field(None, description="Extracted full plain text for Content-ID.")


class ISCC(BaseModel):
    iscc: str = Field(None, description="Full ISCC Code")
    norm_title: str = Field(None, description="Normalized Title")
    tophash: str = Field(None, description="Normalized Title")
    gmt: str = Field(None, description="Generic Media Type")
    bits: list = Field(None, description="Per component bitstrings")


class IsccComponent(BaseModel):
    code: str = Field(None, description="Single ISCC component", max_length=13)
    bits: str = Field(None, description="Bitstring of component body", max_length=64)
    ident: int = Field(
        None, description="Integer representation of component body", le=2 ** 64
    )


class MetaID(IsccComponent):
    title: str
    title_trimmed: str
    extra: str
    extra_trimmed: str


class ContentID(IsccComponent):
    gmt: str = Field(
        "text", description="Generic Media Type of Content-ID", max_length=64
    )


class DataID(IsccComponent):
    pass


class InstanceID(IsccComponent):
    tophash: str = Field(
        None, description="Hex-encoded 256-bit Top Hash", max_length=64
    )


@app.get("/")
def root():
    response = RedirectResponse(url="/docs")
    return response


@app.post("/generate/meta_id/", response_model=MetaID)
def meta_id(meta: Meta):
    """Generate MetaID from 'title' and 'creators'"""
    mid, title_trimmed, extra_trimmed = iscc.meta_id(meta.title, meta.extra)
    return {
        "code": mid,
        "bits": code_to_bits(mid),
        "ident": code_to_int(mid),
        "title": meta.title,
        "title_trimmed": title_trimmed,
        "extra": meta.extra,
        "extra_trimmed": extra_trimmed,
    }


@app.post("/generate/content_id_text", response_model=ContentID)
def content_id_text(text: Text):
    """Generate ContentID-Text from 'text'"""
    cid_t = iscc.content_id_text(text.text)
    return {
        "gmt": "text",
        "bits": code_to_bits(cid_t),
        "code": cid_t,
        "ident": code_to_int(cid_t),
    }


@app.post("/generate/data_id", response_model=DataID)
def data_id(file: UploadFile = File(...)):
    """Generate DataID from raw binary data"""
    did = iscc.data_id(file.file)
    return {"code": did, "bits": code_to_bits(did), "ident": code_to_int(did)}


@app.post("/generate/instance_id", response_model=InstanceID)
def instance_id(file: UploadFile = File(...)):
    """Generate InstanceID from raw binary data"""
    iid, tophash = iscc.instance_id(file.file)
    return {
        "code": iid,
        "bits": code_to_bits(iid),
        "ident": code_to_int(iid),
        "tophash": tophash,
    }


@app.post("/generate/data_instance_id")
def data_instance_id(file: UploadFile = File(...)):
    """Generate DataID and InstanceID from raw binary data"""

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


@app.post("/generate/from_url", response_model=ISCC)
def generate_iscc_url(url: HttpUrl):
    """Generate Full ISCC from URL."""
    r = iscc_from_url(url, guess=False)
    components = iscc_split(r["iscc"])
    r["bits"] = [code_to_bits(c) for c in components]
    return r


@app.post("/generate/from_file", response_model=ISCC)
def generate_iscc_file(file: UploadFile = File(...)):
    """Generate Full ISCC from Media File."""
    _, ext = splitext(file.filename)
    fn = "{}{}".format(uuid.uuid4(), ext)
    tmp_path = join(APP_DIR, fn)
    with open(tmp_path, "wb") as outf:
        outf.write(file.file.read())
    r = iscc_from_file(tmp_path, guess=False)
    os.remove(tmp_path)
    components = iscc_split(r["iscc"])
    r["bits"] = [code_to_bits(c) for c in components]
    return r


if __name__ == "__main__":
    uvicorn.run("iscc_service.main:app", host="127.0.0.1", port=8000, reload=True)
