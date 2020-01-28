from fastapi import FastAPI, UploadFile, File
import iscc
from iscc_service.tools import code_to_bits, code_to_int
from pydantic import BaseModel
from iscc_cli.lib import iscc_from_file


app = FastAPI()


class Meta(BaseModel):
    title: str = ""
    extra: str = ""


class Text(BaseModel):
    text: str = ""


@app.get("/")
def root():
    return {"message": "ISCC Web Service API"}


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


@app.post('/generate/content_id_text')
def content_id_text(text: Text):
    """Generate ContentID-Text from 'text'"""
    cid_t = iscc.content_id_text(text.text)
    return {
        'content_id': {
            'type': 'text',
            'bits': code_to_bits(cid_t),
            'code': cid_t,
            'ident': code_to_int(cid_t),
            'text': text.text,
        }
    }


@app.post('/generate/data_id')
def data_id(file: UploadFile = File(...)):
    """Generate DataID from raw binary data"""
    did = iscc.data_id(file.file)
    return {
        'data_id': {
            'code': did,
            'bits': code_to_bits(did),
            'ident': code_to_int(did),
        }
    }
