"""Place together all needed elements for story image using PIL library"""

import logging
import os
import requests
import sys
from pathlib import Path
from typing import List, Dict, Optional

from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel

from app.models.canvas import Canvas, ImageElements, Text

Image.MAX_IMAGE_PIXELS = None

SCRIPT_FOLDER = Path(__file__).parent
PROJECT_FOLDER = SCRIPT_FOLDER.parent

LOG = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
LOG.addHandler(handler)


def create_canvas(canvas: Canvas) -> Image:
    """Create blank canvas Image object"""
    
    blank_canvas = Image.new(
        "RGBA", 
        (canvas.width, canvas.height),
        (255, 255, 255, 255),
        )
    
    return blank_canvas
    

def _merge_elements(image: Image, element: Image, position: List[str|int]) -> None:
    """Merge together two Image objects"""
    
    # x_axis can be defined either in pixels or as "center"
    if position[0] == "center":
        position[0] = horizontal_center(image, element)
    image.paste(element, tuple(position), element)
    
    
def _merge_shapes(elements: ImageElements, canvas: Image) -> None:
    """Draw shape and merge it to the canvas"""
    
    if not elements.shapes:
        return None
    
    for element in elements.shapes:
        shape = draw_shape(element)
        LOG.info(f"Merging shape '{element}' into canvas...")
        _merge_elements(canvas, shape, element["position"])


def _merge_images(elements: ImageElements, canvas: Image) -> None:
    """Create image object out of image file and merge it to the canvas"""
    
    if not elements.images:
        return None
    
    for element in elements.images:
        image = open_image(element["path"])
        LOG.info(f"Merging image {element} into canvas...")
        
        # resize image if different dimensions are specified in the template
        if "size" in element.keys() and image.size != element["size"]:
            LOG.info(f"Resizing image: {image.size} -> {element['size']}")
            image = image.resize(tuple(element["size"]))
        _merge_elements(canvas, image, element["position"])
    

def merge_elements(elements: ImageElements, canvas: Image) -> Image:
    """Create and put together all elements of the image"""
    
    # Create image object of background, resize if needed and set position
    LOG.info("Getting background image...")
    background = open_image(elements.background.path)
    if background:
        background = resize_background(background, elements.background.size)
    else:
        LOG.error("Loading background image failed.")
        return None
    
    if elements.background.position[0] == "center":
        elements.background.position[0] = horizontal_center(canvas, background)
        
    # Set minimum and maximum value of bg position (max set by default to 0)
    elements.background.min_position_x = horizontal_center(canvas, background) * 2
        
    x_axis = int(elements.background.position[0])
    y_axis = int(elements.background.position[1])
    
    # First merge background with canvas, then add shapes, images and texts
    LOG.info("Merging background to the canvas...")
    _merge_elements(canvas, background, (x_axis, y_axis))
    _merge_shapes(elements, canvas)
    _merge_images(elements, canvas)
    for text in elements.texts:   
        _add_text(canvas, text)
    
    return canvas


def open_image(path: str|Path) -> Image:
    """Create Image object out of the image file, either from url or file path"""
    
    LOG.info(f"Getting image from {path}")
    if path.startswith("https://") or path.startswith("http://"):
        response = requests.get(path, stream=True)
        if response.status_code in [200, 201]:
            LOG.info(f"Image from {path} succefully retrieved.")
            return Image.open(response.raw).convert("RGBA")
        else: 
            LOG.error(f"Image could not be retrieved from the url {path}")
            return None
    else:
        if os.path.exists(path):
            return Image.open(path).convert("RGBA")
        else:
            LOG.error(f"Image path {path} does not exist.")
            return None


def _add_text(image: Image, text: Text) -> None:
    """Set all attributes of text and merge it to the canvas"""
    
    LOG.info(f"Adding text to the canvas: {text}")
    
    y_axis = text.y_axis
    x_axis = text.x_axis
    
    # Center text
    if x_axis == "center":
        x_pos = image.width // 2
    else:
        x_pos = x_axis
        
    text_str = text.text
    
    # Capitalize all letters 
    if text.letter_case == "uppercase":
        text_str = text_str.upper()
    
    font_size = text.font_size
    
    # split text if number of letters in line is exceeded
    message = split_text(text_str, text.word_wrap)
    
    font = ImageFont.truetype(text.font, text.font_size)
    align = text.align
    fill = text.color
    anchor = text.anchor
    
    # Draw all texts into image
    draw = ImageDraw.Draw(image)
    for line in message:
        draw.text((x_pos, y_axis), line, font=font, align=align, fill=fill, anchor=anchor)
        y_axis += font_size * text.line_height


def split_text(text:str, max_char: int) -> List:
    """Split text into list if number of letters exceeds defined value"""
    
    # If text is shorter then max letters allowed, or if text contains newline char, split it
    if len(text) <= max_char or "\n" in text:
        return text.rstrip().split("\n")
     
    text_list = []
    remaining_text = text.rstrip()
    
    # Split text so the words are not splitted
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
    """Center element on x axis"""
    
    return -(el_b.width//2)+(el_a.width//2)


def resize_background(background: Image, size: List) -> Image:
    """Resize background image and keep size ratio"""
    
    bg_width, bg_height = background.size
    if size[0] == "full":
        ratio = bg_height / size[1]
    else:
        ratio = bg_width / size[1]

    LOG.info(f"Resizing background image: '{background.size}' -> '{size}'. Ratio: {ratio}")
    
    return background.resize((round(bg_width/ratio) ,round(bg_height/ratio)))


def draw_shape(details: Dict) -> Image:
    """Create ImageDraw object"""
    
    # Currently supports only for rounded rectangle 
    size = tuple(details["size"])
    shape = Image.new("RGBA", size)
    draw = ImageDraw.Draw(shape)
    if details["type"] == "rounded_rectangle":
        radius = details["corner_radius"]
        fill = tuple(details["fill"])
        draw.rounded_rectangle(((0, 0), size), radius, fill=fill)
    
    return shape


def create_story(post_elements: ImageElements, site: str) -> Path:
    """Create and save image file. 
    Returns True if image was saved"""
    
    is_ok = True
    
    stories_site_dir = PROJECT_FOLDER / "stories" / site
    image_path = f"{stories_site_dir}/{post_elements.number}.png"
    
    # Create blank canvas as the base of the image
    canvas = create_canvas(post_elements.canvas_size)
    
    # Add elements from the template into the canvas
    story = merge_elements(post_elements, canvas)
    if story is None:
        LOG.error("Merging elements failed.")
        is_ok = False
    
    # Create stories dir if don't exist
    if not os.path.isdir(stories_site_dir):
        try:
            LOG.info(f"Creating folder -> {stories_site_dir}")
            os.mkdir(stories_site_dir)
        except PermissionError as e:
            LOG.exception("Stories directory could not be created.")
            is_ok = False
    
    try:
        LOG.info(f"Storing generated image in file -> {image_path}")
        story.save(image_path, format="png")
    except IOError:
        LOG.exception(f"Image {image_path} can not be saved.")
        is_ok = False
        
    return is_ok
