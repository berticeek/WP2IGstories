from PIL import Image, ImageDraw

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
    
    canvas.save("result.png", format="png")


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
    draw.rounded_rectangle(((0, 0), size), 30, fill=(255,255,255,196))
    
    return text_box


# merge_elements(image_elements)
canvas = create_canvas(Canvas(width=1080, height=1920))

image_elements = ImageElements(
    logo = Path("media", "logo.png"),
    background = Path("media", "background.jpg"),
    text_box=draw_text_box()
)


merge_elements(image_elements, canvas)
