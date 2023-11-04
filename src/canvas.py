from PIL import Image, ImageDraw, ImageFont

from typing import List, Dict, Optional
from pydantic import BaseModel
from pathlib import Path
import requests

import os


class Text(BaseModel):
    text: str
    font: Optional[str]
    font_size: Optional[int]
    align: Optional[str]
    color: Optional[str | int]
    y_axis: int
    line_height: Optional[float]
    word_wrap: Optional[int]
    
    
class Background(BaseModel):
    path: str
    position: List[str | int]
    

class Canvas(BaseModel):
    width: int
    height: int


class ImageElements(BaseModel):
    number: int
    canvas_size: Canvas
    background: Background
    images: Optional[List]
    shapes: Optional[List]
    text: Text


def create_canvas(canvas) -> Image:
    blank_canvas = Image.new(
        "RGBA", 
        (canvas.width, canvas.height),
        (255, 255, 255, 255),
        )
    blank_canvas.save("new.png")
    
    return blank_canvas
    

def _merge_elements(image, element, position):
    if position[0] == "center":
        position[0] = horizontal_center(image, element)
    image.paste(element, tuple(position), element)
    

def merge_elements(elements: ImageElements, canvas: Image):
    background = get_background_from_url(elements.background.path)
    background = resize_background(background, canvas)
    _merge_elements(canvas, background, (horizontal_center(canvas, background), 0))
    
    for element in elements.shapes:
        shape = draw_shape(element)
        _merge_elements(canvas, shape, element["position"])
    
    for element in elements.images:
        image = Image.open(element["path"])
        if "size" in element.keys() and image.size != element["size"]:
            image = image.resize(tuple(element["size"]))
        _merge_elements(canvas, image, element["position"])
        
    add_text(canvas, elements.text)
    
    canvas.save(f"stories/{elements.number}.png", format="png")


def get_background_from_url(url):
    response = requests.get(url, stream=True)
    return Image.open(response.raw).convert("RGBA")


def add_text(image, text):
    text_position = text.y_axis
    font_size = text.font_size
    message = split_text(text.text)
    font = ImageFont.truetype(text.font, text.font_size)
    align = text.align
    fill = text.color
    draw = ImageDraw.Draw(image)
    for line in message:
        draw.text((image.width // 2, text_position), line, font=font, align=align, fill=fill, anchor="mm")
        text_position += font_size * text.line_height


def split_text(text:str) -> List:
    max_char = 29
    
    if len(text) <= max_char:
        return [text]
     
    text_list = []
    remaining_text = text
    
    while remaining_text:        
        char = ""
        cur_char = max_char
        while char != " " and len(remaining_text) >= cur_char:
            char = remaining_text[cur_char-1]
            cur_char -= 1
        
        text_list.append(remaining_text[:cur_char].strip())
        remaining_text = remaining_text[cur_char:].strip()
            
    return text_list
         

def horizontal_center(el_a: Image, el_b: Image) -> int:
    return -(el_b.width//2)+(el_a.width//2)


def resize_background(background: Image, canvas: Image) -> Image:
    bg_width, bg_height = background.size
    c_width, c_height = canvas.size
    
    ratio = bg_height / c_height
    
    return background.resize((round(bg_width/ratio) ,round(bg_height/ratio)))

def open_image(element):
    if os.path.isfile(element):
        return Image.open(element)


def draw_shape(details) -> Image:
    size = tuple(details["size"])
    shape = Image.new("RGBA", size)
    draw = ImageDraw.Draw(shape)
    if details["type"] == "rounded_rectangle":
        radius = details["corner_radius"]
        fill = tuple(details["fill"])
        draw.rounded_rectangle(((0, 0), size), radius, fill=fill)
    
    return shape


def create_story(post_elements):
    canvas = create_canvas(post_elements.canvas_size)
    merge_elements(post_elements, canvas)
