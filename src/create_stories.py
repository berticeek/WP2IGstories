from pathlib import Path
import yaml
from typing import Dict, List, Tuple, Optional
import os
from argparse import ArgumentParser

from get_posts_metadata import get_posts_metadata
from get_posts_metadata import PostData

from canvas import Canvas, ImageElements, Background, Text
from canvas import create_story

from pydantic import BaseModel


class Template(BaseModel):
    canvas: Dict
    elements: Dict
    background: Dict
    texts_config: Optional[List]


def template_path(site: str) -> str:
    return os.path.join("data", site, "template.yaml")


def get_api_url(site: str) -> str:
    with open(template_path(site)) as template:
        template = yaml.safe_load(template)
    return template["url"]

def get_story_template(site: str) -> Template:
    with open(template_path(site)) as template:
        template = yaml.safe_load(template)
        
        if "texts" in template["elements"]:
            texts_config = template["elements"]["texts"]
        else: 
            text_config = None
        
        return Template(
            canvas = template["canvas"],
            elements = template["elements"],
            background = template["elements"]["background"],
            texts_config = texts_config,
        )
    
    
def clear_files(site: str) -> None:
    output_folder = os.path.join("stories", site)
    for file in os.listdir(output_folder):
        if file != "metadata.yaml":
            os.remove(os.path.join(output_folder, file))


def get_post_elements(number: int, post, template) -> ImageElements:
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


def store_metadata(post: PostData, elements: ImageElements) -> Dict:
    texts = [x.text for x in elements.texts]
    return {
        "number": elements.number,
        "url": f"{post.link}",
        "image": f"{elements.background.path}",
        "image_position_x":f"{elements.background.position[0]}",
        "texts": texts,
        
    }


def write_metadata_file(metadata: List[Dict]) -> None:
    md_file = os.path.join("stories", site, "metadata.yaml")
    if os.path.isfile(md_file):
        os.remove(md_file)
        
    with open(md_file, "a", encoding="utf-8") as f_metadata:
        yaml.dump(metadata, f_metadata, default_flow_style=False, allow_unicode=True, sort_keys=False)


def adjust_elements(elements: ImageElements, site: str) -> ImageElements:
    """Adjust text, cover image or its position based on modified metadata.yaml file"""
    
    # Currently supports only text change
    metadata_file = os.path.join("stories", site, "metadata.yaml")
    with open(metadata_file, "r") as metadata:
        metavalues = yaml.safe_load(metadata)[elements.number]
    for text_id, text in enumerate(metavalues["texts"]):
        elements.texts[text_id].text = text
    
    elements.background.position[0] = metavalues["image_position_x"]
        
    return elements
        

if __name__ == "__main__":
    parser = ArgumentParser(description="Create IG stories for specific IG page")
    parser.add_argument("-s", "--site", 
                        help="Name of the site to create IG stories for", 
                        action="store",
                        choices=["ht", "pe"],
                        required=True,
                        type=str,
                        )
    parser.add_argument("-r", "--recreate", 
                        help="Recreate IG stories for selected site based on modified metadata.yaml file", 
                        action="store_true",
                        required=False,
                        )
    args = parser.parse_args()
    
    site = args.site
    clear_files(site)

    posts = get_posts_metadata(get_api_url(site))
    
    story_template = get_story_template(site)
    metadata = []    
    for number, post in enumerate(posts):
        post_elements = get_post_elements(number, post, story_template)

        if args.recreate:
            post_elements = adjust_elements(post_elements, site)

        create_story(post_elements, site)
        
        output_folder = os.path.join("stories", site)
        if not os.path.isdir(output_folder):
            os.mkdir(output_folder)
        with open(os.path.join(output_folder, "links.txt"), "a") as links:
            links.write(f"{number}: {post.link}\n")
           
        metadata.append(store_metadata(post, post_elements))
        
    write_metadata_file(metadata)
        