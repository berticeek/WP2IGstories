from PIL import Image, ImageDraw, ImageFont

from typing import List
from pydantic import BaseModel
from pathlib import Path

import os

class Canvas(BaseModel):
    width: int
    height: int


def create_canvas(canvas) -> Image:
    blank_canvas = Image.new(
        "RGBA", 
        (canvas.width, canvas.height),
        (255, 255, 255, 255),
        )
    blank_canvas.save("new.png")
    
    return blank_canvas
    
    
class ImageElements(BaseModel):
    logo: Path
    background: Path
    text_box: object
    text: str
    

def _merge_elements(image, element, position):    
    image.paste(element, position, element)
    # return image
    

def merge_elements(elements: ImageElements, canvas: Image):
    background = Image.open(elements.background).convert("RGBA")    
    logo = Image.open(elements.logo)
    
    logo_pos_y = 1100
    text_box_pos_y = 1194
    
    logo = logo.resize((150, 150))
    background = resize_background(background, canvas)
    
    _merge_elements(canvas, background, (horizontal_center(canvas, background), 0))
    _merge_elements(canvas, elements.text_box, (horizontal_center(canvas, elements.text_box), text_box_pos_y))
    _merge_elements(canvas, logo, (horizontal_center(canvas, logo), logo_pos_y))
    add_text(canvas, elements.text)
    
    canvas.save("result.png", format="png")


def add_text(image, text):
    text_position = 1370
    font_size = 53
    text = split_text(text)
    font = ImageFont.truetype("media/fonts/Montserrat-ExtraBold.ttf", font_size)
    draw = ImageDraw.Draw(image)
    for line in text:
        draw.text((image.width // 2, text_position), line, font=font, align="center", fill="black", anchor="mm")
        text_position += font_size * 1.3


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


def draw_text_box() -> Image:
    size = (980, 940)
    text_box = Image.new("RGBA", size)
    draw = ImageDraw.Draw(text_box)
    draw.rounded_rectangle(((0, 0), size), 20, fill=(255,255,255,220))
    
    return text_box


# merge_elements(image_elements)
canvas = create_canvas(Canvas(width=1080, height=1920))

image_elements = ImageElements(
    logo = Path("media", "logo.png"),
    background = Path("media", "background.jpg"),
    text_box=draw_text_box(),
    text = "HBO v novembri: Dočkáš sa hereckých hviezd v novinkách, ktorým nebude chýbať napätie a dráma",
)


merge_elements(image_elements, canvas)
