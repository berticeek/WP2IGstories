from pathlib import Path
import yaml
from typing import Dict, List, Tuple

from get_posts_metadata import get_posts_metadata

from canvas import Canvas, ImageElements, Background, Text
from canvas import create_story
from pydantic import BaseModel


class Template(BaseModel):
    canvas: Dict
    elements: Dict
    bg_pos: Tuple
    text_config: Dict
    

def get_post_elements(number, post, template):
    # for number, post in enumerate(posts):
    canvas_size = Canvas(width=template.canvas["width"], height=template.canvas["height"])
    
    return (
        ImageElements(
            number=number,
            canvas_size=canvas_size,
            background=Background(
                path = post.cover,
                position = template.bg_pos,
            ),
            images=template.elements["images"],
            shapes=template.elements["shapes"],
            text=Text(
                text=post.title,
                font=template.text_config["font"],
                font_size=template.text_config["font_size"],
                align=template.text_config["align"],
                color=template.text_config["color"],
                y_axis=template.text_config["y_axis"],
                line_height=template.text_config["line_height"],
                word_wrap=template.text_config["word_wrap"],       
            )
        ))


def create_stories(posts):
    with open("data/template.yaml") as template:
        template_content = yaml.safe_load(template)
        story_template = Template(
            canvas = template_content["canvas"],
            elements = template_content["elements"],
            bg_pos = template_content["elements"]["background"]["position"],
            text_config = template_content["elements"]["text"],
        )
    
    for number, post in enumerate(posts):
        post_elements = get_post_elements(number, post, story_template)
        create_story(post_elements)
        with open("stories/links.txt", "a") as links:
            links.write(f"{number}: {post.link}\n")
        

if __name__ == "__main__":
    api_url = "https://hashtag.zoznam.sk/wp-json/wp/v2"
    posts = get_posts_metadata(api_url)
    create_stories(posts)
    