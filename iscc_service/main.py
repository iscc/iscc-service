import os
import uuid
from os.path import join, splitext

from fastapi import FastAPI, UploadFile, File
import iscc
from iscc_service.tools import code_to_bits, code_to_int
from pydantic import BaseModel
from iscc_cli.lib import iscc_from_file, iscc_from_url
from iscc_cli import APP_DIR
from starlette.middleware.cors import CORSMiddleware


app = FastAPI()

ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*').split()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Meta(BaseModel):
    title: str = ""
    extra: str = ""


class Text(BaseModel):
    text: str = ""


class URL(BaseModel):
    url: str


class ISCC(BaseModel):
    iscc: str
    norm_title: str
    tophash: str
    gmt: str


@app.post("/generate/meta_id/")
def meta_id(meta: Meta):
    """Generate MetaID from 'title' and 'creators'"""
    mid, title_trimmed, extra_trimmed = iscc.meta_id(meta.title, meta.extra)
    return {
        "meta_id": {
            "code": mid,
            "bits": code_to_bits(mid),
            "ident": code_to_int(mid),
            "title": meta.title,
            "title_trimmed": title_trimmed,
            "extra": meta.extra,
            "extra_trimmed": extra_trimmed,
        }
    }


@app.post("/generate/content_id_text")
def content_id_text(text: Text):
    """Generate ContentID-Text from 'text'"""
    cid_t = iscc.content_id_text(text.text)
    return {
        "content_id": {
            "type": "text",
            "bits": code_to_bits(cid_t),
            "code": cid_t,
            "ident": code_to_int(cid_t),
            "text": text.text,
        }
    }


@app.post("/generate/data_id")
def data_id(file: UploadFile = File(...)):
    """Generate DataID from raw binary data"""
    did = iscc.data_id(file.file)
    return {
        "data_id": {"code": did, "bits": code_to_bits(did), "ident": code_to_int(did),}
    }


@app.post("/generate/instance_id")
def instance_id(file: UploadFile = File(...)):
    """Generate InstanceID from raw binary data"""
    iid, tophash = iscc.instance_id(file.file)
    return {
        "instance_id": {
            "code": iid,
            "bits": code_to_bits(iid),
            "ident": code_to_int(iid),
            "tophash": tophash,
        }
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
def generate_iscc_url(url: str):
    """Generate Full ISCC from URL."""
    r = iscc_from_url(url, guess=False)
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
    return r
