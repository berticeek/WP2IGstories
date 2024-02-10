from pydantic import BaseModel


class PostData(BaseModel):
    """Basic data retrieved from wordpress used in image"""
    
    title: str
    link: str
    cover: str