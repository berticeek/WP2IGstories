from pathlib import Path

from get_posts_metadata import get_posts_metadata

from canvas import Canvas, ImageElements
from canvas import create_canvas, draw_text_box, create_story

api_url = "https://hashtag.zoznam.sk/wp-json/wp/v2"
canvas_size = Canvas(width=1080, height=1920)

posts = get_posts_metadata(api_url)

for number, post in enumerate(posts):
    post_elements = (
        ImageElements(
            number = number,
            canvas_size=canvas_size,
            logo = Path("media", "logo.png"),
            background = post.cover,
            text_box=draw_text_box(),
            text = post.title,
        ))

    create_story(post_elements)

    with open("stories/links.txt", "a") as links:
        links.write(f"{number}: {post.link}\n")