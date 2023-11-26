from pathlib import Path
import yaml
from envyaml import EnvYAML
import json
from typing import Dict, List, Tuple, Optional
import os
from argparse import ArgumentParser
from urllib.parse import quote

from get_posts_metadata import get_posts_metadata
from get_posts_metadata import PostData

from file_paths import template_path, clear_files

from canvas import Canvas, ImageElements, Background, Text
from canvas import create_story

from pydantic import BaseModel


SCRIPT_FOLDER = Path(__file__).parent
PROJECT_FOLDER = SCRIPT_FOLDER.parent


class Template(BaseModel):
    canvas: Dict
    elements: Dict
    background: Dict
    texts_config: Optional[List]
    link_suffix: str | None


def suffix_in_template(site):
    with open(template_path(site)) as template:
        template = yaml.safe_load(template)
    return template["url"]


def get_story_template(site: str) -> Template:
    template = EnvYAML(template_path(site))
    
    if "texts" in template["elements"]:
        texts_config = template["elements"]["texts"]
    else: 
        text_config = None
    
    if "link_suffix" in template:
        suffix = quote(template["link_suffix"])
    else:
        suffix = None
    
    return Template(
        canvas = template["canvas"],
        elements = template["elements"],
        background = template["elements"]["background"],
        texts_config = texts_config,
        link_suffix=suffix
    ).model_dump()


def get_post_elements(number: int, post: PostData, template: Template) -> ImageElements:
    canvas_size = Canvas(width=template.canvas["width"], height=template.canvas["height"])
    
    if template.background["from_cover"]:
        bg_path = post.cover
    else:
        bg_path = template.background.path
    
    for im_id, image in enumerate(template.elements["images"]):
        if image["from_cover"]:
            template.elements["images"][im_id].update({"path": post.cover})
            
    if "shapes" in template.elements:
        shapes=template.elements["shapes"]
    else:
        shapes=None
    
    if template.link_suffix and template.link_suffix not in post.link:
        link = post.link + template.link_suffix
    else:
        link = post.link
        
    texts = []   
    for text_conf in template.texts_config:
        if "text" in text_conf:
            text = text_conf["text"]
        else:
            text = post.title
        texts.append(Text(
            text=text,
            font=text_conf["font"],
            font_size=text_conf["font_size"],
            letter_case=text_conf["letter_case"],
            align=text_conf["align"],
            color=text_conf["color"],
            y_axis=text_conf["y_axis"],
            x_axis=text_conf["x_axis"],
            line_height=text_conf["line_height"],
            word_wrap=text_conf["word_wrap"],
            anchor=text_conf["anchor"]
            ))
    
    return (
        ImageElements(
            number=number,
            canvas_size=canvas_size,
            background=Background(
                path = bg_path,
                position = template.background["position"],
                size = template.background["size"],
                from_cover=template.background["from_cover"]
            ),
            images=template.elements["images"],
            shapes=shapes,
            texts=texts,
            post_url=quote(link)
        ).model_dump())


def store_metadata(elements: ImageElements) -> Dict:
    texts = [x.text for x in elements.texts]
    return {
        "number": elements.number,
        "url": f"{elements.post_url}",
        "image": f"{elements.background.path}",
        "image_position_x":f"{elements.background.position[0]}",
        "texts": texts,
        
    }


def write_metadata_file(metadata: List[Dict], site: str) -> Path:
    md_file = PROJECT_FOLDER / "stories" / site / "metadata.yaml"
    if os.path.isfile(md_file):
        os.remove(md_file)
        
    with open(md_file, "a", encoding="utf-8") as f_metadata:
        yaml.dump(metadata, f_metadata, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
    return md_file


def get_elements(posts, template):
    post_elements = []
    for number, post in enumerate(posts):
        post_elements.append(get_post_elements(number, post, template))
    return post_elements
        

def adjust_elements(elements: ImageElements, metadata) -> ImageElements:
    """Adjust text, cover image or its position based on modified metadata.yaml file"""
    
    # Currently supports only text change and background position
    for text_id, text in enumerate(metadata["texts"]):
        elements.texts[text_id].text = text
    
    elements.background.position[0] = metadata["image_position_x"]
    
    elements.post_url = quote(elements.post_url)
        
    return elements.model_dump()
        

def create_stories(site: str, posts_elements: List[ImageElements]) -> List:
    clear_files(site)
    
    metadata = []
    
    for elems in posts_elements:
        create_story(elems, site)
        
        output_folder = PROJECT_FOLDER / "stories" / site
        if not os.path.isdir(output_folder):
            os.mkdir(output_folder)
            
        with open(output_folder / "links.txt", "a") as links:
            links.write(f"{elems.number}: {elems.post_url}\n")

        metadata.append(store_metadata(elems))

    return metadata
        