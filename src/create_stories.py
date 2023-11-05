from pathlib import Path
import yaml
from typing import Dict, List, Tuple, Optional
import os
from argparse import ArgumentParser

from get_posts_metadata import get_posts_metadata

from canvas import Canvas, ImageElements, Background, Text
from canvas import create_story

from pydantic import BaseModel


class Template(BaseModel):
    canvas: Dict
    elements: Dict
    background: Dict
    texts_config: Optional[List]
    

def get_post_elements(number, post, template):
    canvas_size = Canvas(width=template.canvas["width"], height=template.canvas["height"])
    
    if template.background["from_cover"]:
        bg_path = post.cover
    else:
        bg_path = template.background["path"]
    
    for im_id, image in enumerate(template.elements["images"]):
        if image["from_cover"]:
            template.elements["images"][im_id].update({"path": post.cover})
            
    if "shapes" in template.elements:
        shapes=template.elements["shapes"]
    else:
        shapes=None
        
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
        ))


def create_stories(posts, site):
    template_path = os.path.join("data", site, "template.yaml")
    
    with open(template_path) as template:
        template_content = yaml.safe_load(template)
        
        if "texts" in template_content["elements"]:
            texts_config = template_content["elements"]["texts"]
        else: 
            text_config = None
        
        story_template = Template(
            canvas = template_content["canvas"],
            elements = template_content["elements"],
            background = template_content["elements"]["background"],
            texts_config = texts_config,
        )
    
    for number, post in enumerate(posts):
        post_elements = get_post_elements(number, post, story_template)
        create_story(post_elements, site)
        
        links_folder = os.path.join("stories", site)
        if not os.path.isdir(links_folder):
            os.mkdir(links_folder)
        with open(os.path.join(links_folder, "links.txt"), "a") as links:
            links.write(f"{number}: {post.link}\n")
        

if __name__ == "__main__":
    parser = ArgumentParser(description="Create IG stories for specific IG page")
    parser.add_argument("-s", "--site", 
                        help="Name of the site to create IG stories for", 
                        action="store",
                        choices=["ht", "pe"],
                        required=True,
                        type=str,
                        )
    args = parser.parse_args()
    
    site = args.site
    
    # api_url = "https://hashtag.zoznam.sk/wp-json/wp/v2"
    api_url = "https://plnielanu.zoznam.sk/wp-json/wp/v2"
    posts = get_posts_metadata(api_url)
    create_stories(posts, site)
    