# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, HttpUrl


def main():
    pass


if __name__ == "__main__":
    main()


class Metadata(BaseModel):
    """Metadata for Meta-ID creation."""

    title: str = Field(
        ..., description="The title of an intangible creation.", min_length=1
    )
    extra: Optional[str] = Field(
        None,
        description="An optional short statement that distinguishes "
        "this intangible creation from another one for the "
        "purpose of forced Meta-ID uniqueness.",
    )


class Text(BaseModel):
    text: str = Field(None, description="Extracted full plain text for Content-ID.")


class ISCC(BaseModel):
    """Full ISCC Code including Metadata."""

    iscc: str = Field(..., description="Full ISCC Code")
    iscc_raw: str = Field(..., description="Hex-encoded ISCC Code")
    title: str = Field(None, description="Title of intangible creation")
    title_trimmed: str = Field(None, description="Normalized and trimmed title")
    extra: str = Field(None, description="Optional extra metadata")
    extra_trimmed: str = Field(
        None, description="Normalized and trimmed extra metadata"
    )
    tophash: str = Field(..., description="Normalized Title")
    gmt: str = Field(..., description="Generic Media Type")
    bits: List[str] = Field(..., description="Per component bitstrings")


class IsccComponent(BaseModel):
    """A single ISCC Component as code, bits and headerless integer."""

    code: str = Field(..., description="Single ISCC component", max_length=13)
    bits: str = Field(..., description="Bitstring of component body", max_length=64)
    ident: int = Field(
        ..., description="Integer representation of component body", le=2 ** 64
    )


class MetaID(IsccComponent):
    """A Meta-ID ISCC Component including Metadata."""

    title: str = Field(..., description="Title of intangible creation")
    title_trimmed: str = Field(..., description="Normalized and trimmed title")
    extra: str = Field(None, description="Optional extra metadata")
    extra_trimmed: str = Field(
        None, description="Normalized and trimmed extra metadata"
    )


class ContentID(IsccComponent):
    """A Content-ID ISCC Component including Generic Media Type."""

    gmt: str = Field(
        "text", description="Generic Media Type of Content-ID", max_length=64
    )


class DataID(IsccComponent):
    """A Data-ID ISCC Component."""

    pass


class InstanceID(IsccComponent):
    """An Instance-ID ISCC Component including Tophash."""

    tophash: str = Field(
        None, description="Hex-encoded 256-bit Top Hash", max_length=64
    )


class StreamItem(BaseModel):
    txid: str
    vout: int
    keys: List[str]
    title: str
    extra: Optional[str]
    tophash: Optional[str]
    time: datetime
    content_url: Optional[HttpUrl]
    bits: List[str]
