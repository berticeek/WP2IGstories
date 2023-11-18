from PIL import Image, ImageDraw, ImageFont

from typing import List, Dict, Optional
from pydantic import BaseModel
from pathlib import Path
import requests

import os
import urllib


SCRIPT_FOLDER = Path(__file__).parent
PROJECT_FOLDER = SCRIPT_FOLDER.parent


class Text(BaseModel):
    text: str
    font: Optional[str]
    font_size: Optional[int]
    align: Optional[str]
    color: Optional[str | int]
    y_axis: int
    x_axis: int | str
    line_height: Optional[float]
    word_wrap: Optional[int]
    anchor: str
    
    
class Background(BaseModel):
    path: str
    position: List[str | int]
    size: List[str | int]
    from_cover: bool
    

class Canvas(BaseModel):
    width: int
    height: int


class ImageElements(BaseModel):
    number: int
    canvas_size: Canvas
    background: Background
    images: Optional[List]
    shapes: Optional[List]
    texts: List[Text]
    post_url: str


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
    
    
def _merge_shapes(elements, canvas):
    if not elements.shapes:
        return
    for element in elements.shapes:
        shape = draw_shape(element)
        _merge_elements(canvas, shape, element["position"])


def _merge_images(elements, canvas):
    if not elements.images:
        return
    for element in elements.images:
        image = open_image(element["path"])
        if "size" in element.keys() and image.size != element["size"]:
            image = image.resize(tuple(element["size"]))
        _merge_elements(canvas, image, element["position"])
    

def merge_elements(elements: ImageElements, canvas: Image):
    background = open_image(elements.background.path)
    background = resize_background(background, elements.background.size)
    
    if elements.background.position[0] == "center":
        elements.background.position[0] = horizontal_center(canvas, background)
        
    x_axis = int(elements.background.position[0])
    y_axis = int(elements.background.position[1])
    
    _merge_elements(canvas, background, (x_axis, y_axis))
    _merge_shapes(elements, canvas)
    _merge_images(elements, canvas)
    for text in elements.texts:   
        _add_text(canvas, text)
    
    return canvas


def open_image(path):
    if path.startswith("https://") or path.startswith("http://"):
        response = requests.get(path, stream=True)
        return Image.open(response.raw).convert("RGBA")
    else:
        if os.path.exists(path):
            return Image.open(path).convert("RGBA")


def _add_text(image, text):
    y_axis = text.y_axis
    x_axis = text.x_axis
    
    if x_axis == "center":
        x_pos = image.width // 2
    else:
        x_pos = x_axis
        
    font_size = text.font_size
    message = split_text(text.text, text.word_wrap)
    font = ImageFont.truetype(text.font, text.font_size)
    align = text.align
    fill = text.color
    anchor = text.anchor
    draw = ImageDraw.Draw(image)
    for line in message:
        draw.text((x_pos, y_axis), line, font=font, align=align, fill=fill, anchor=anchor)
        y_axis += font_size * text.line_height


def split_text(text:str, max_char) -> List:
    if len(text) <= max_char or "\n" in text:
        return text.rstrip().split("\n")
     
    text_list = []
    remaining_text = text.rstrip()
    
    while remaining_text:        
        char = ""
        cur_char = max_char
        while char != " " and len(remaining_text) >= cur_char and cur_char>0:
            char = remaining_text[cur_char-1]
            cur_char -= 1
        
        text_list.append(remaining_text[:cur_char].strip())
        remaining_text = remaining_text[cur_char:].strip()
    
    if not text_list:
        text_list = text.rstrip().split("\n")
            
    return text_list
         

def horizontal_center(el_a: Image, el_b: Image) -> int:
    return -(el_b.width//2)+(el_a.width//2)


def resize_background(background: Image, size: List) -> Image:
    bg_width, bg_height = background.size
    if size[0] == "full":
        ratio = bg_height / size[1]
    else:
        ratio = bg_width / size[1]
    
    return background.resize((round(bg_width/ratio) ,round(bg_height/ratio)))


def draw_shape(details) -> Image:
    size = tuple(details["size"])
    shape = Image.new("RGBA", size)
    draw = ImageDraw.Draw(shape)
    if details["type"] == "rounded_rectangle":
        radius = details["corner_radius"]
        fill = tuple(details["fill"])
        draw.rounded_rectangle(((0, 0), size), radius, fill=fill)
    
    return shape


def create_story(post_elements, site: str) -> Path:
    
    stories_site_dir = PROJECT_FOLDER / "stories" / site
    image_path = f"{stories_site_dir}/{post_elements.number}.png"
    
    canvas = create_canvas(post_elements.canvas_size)
    story = merge_elements(post_elements, canvas)
    if not os.path.isdir(stories_site_dir):
        os.mkdir(stories_site_dir)
    story.save(image_path, format="png")
    
    # return os.path.basename(image_path)
