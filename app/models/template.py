
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Template(BaseModel):
    id: Optional[str] = None
    title: str
    description: str
    category: str
    uploaded_by: str
    zip_s3_key: str
    images: List[str] = []
    tags: List[str] = []
    preview_url: Optional[str] = None
    status: str = "pending"
    is_public: bool = False   # <-- NEW FIELD
    created_at: datetime = Field(default_factory=datetime.utcnow)
