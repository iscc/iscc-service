from fastapi import FastAPI
import iscc
from iscc_service.tools import code_to_bits, code_to_int
from pydantic import BaseModel


app = FastAPI()


class Meta(BaseModel):
    title: str = ""
    extra: str = ""


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
