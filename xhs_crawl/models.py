from typing import List, Optional
from pydantic import BaseModel

class XHSPost(BaseModel):
    """小红书帖子数据模型"""
    post_id: str
    title: Optional[str] = None
    content: Optional[str] = None
    images: List[str] = []