from typing import List
from pydantic import BaseModel, HttpUrl


class Tag(BaseModel):
    """Represents a quote tag."""
    name: str
    url: HttpUrl


class Quote(BaseModel):
    """Represents a quote with its metadata."""
    text: str
    author: str
    author_url: HttpUrl
    tags: List[Tag]
    goodreads_url: HttpUrl
