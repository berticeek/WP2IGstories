from typing import List, Optional

from pydantic import BaseModel


class Text(BaseModel):
    """Parameters of texts"""
    
    text: str
    font: Optional[str]
    font_size: Optional[int]
    letter_case: str
    align: Optional[str]
    color: Optional[str | int]
    y_axis: int
    x_axis: int | str
    line_height: Optional[float]
    word_wrap: Optional[int]
    anchor: str
    
    
class Background(BaseModel):
    """Parameters of background image"""
    
    path: str
    position: List[str | int]
    min_position_x: int = 0
    max_position_x: int = 0
    size: List[str | int]
    from_cover: bool
    

class Canvas(BaseModel):
    """Canvas width and height"""
    
    width: int
    height: int


class ImageElements(BaseModel):
    """All elements of image to be created"""
    
    number: int
    canvas_size: Canvas
    background: Background
    images: Optional[List]
    shapes: Optional[List]
    texts: List[Text]
    post_url: str