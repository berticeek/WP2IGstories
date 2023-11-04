from pathlib import Path
import yaml

from get_posts_metadata import get_posts_metadata

from canvas import Canvas, ImageElements, Background, Text
from canvas import create_story

with open("data/template.yaml") as template:
    story_template = yaml.safe_load(template)
    canvas = story_template["canvas"]
    elements = story_template["elements"]
    bg_pos = elements["background"]["position"]
    text_config = elements["text"]

api_url = "https://hashtag.zoznam.sk/wp-json/wp/v2"
canvas_size = Canvas(width=canvas["width"], height=canvas["height"])

posts = get_posts_metadata(api_url)

for number, post in enumerate(posts):
    post_elements = (
        ImageElements(
            number=number,
            canvas_size=canvas_size,
            background=Background(
                path = post.cover,
                position = bg_pos,
            ),
            images=elements["images"],
            shapes=elements["shapes"],
            text=Text(
                text=post.title,
                font=text_config["font"],
                font_size=text_config["font_size"],
                align=text_config["align"],
                color=text_config["color"],
                y_axis=text_config["y_axis"],
                line_height=text_config["line_height"],
                word_wrap=text_config["word_wrap"],       
            )
        ))

    create_story(post_elements)

    with open("stories/links.txt", "a") as links:
        links.write(f"{number}: {post.link}\n")