from typing import Dict, List, Optional

from pydantic import BaseModel


class Template(BaseModel):
    """Configuration of image - 
    images paths, sizes, positions, all settings for everything in the image"""
    
    canvas: Dict
    elements: Dict
    background: Dict
    texts_config: Optional[List]
    link_suffix: str | None