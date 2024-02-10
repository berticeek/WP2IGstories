from typing import Dict, List
from urllib.parse import quote
from envyaml import EnvYAML
from app import LOG
from app.models.canvas import Background, Canvas, ImageElements, Text
from app.models.story import Template

from app.utils.file_paths import template_path
from app.utils.get_posts_metadata import PostData


def get_story_template(site: str) -> dict:
    """Open template file and load all image settings"""
    
    try:
        template = EnvYAML(template_path(site))
    except Exception as e:
        LOG.exception("Template file couldn't be loaded.")
        return None
    
    # Load texts
    if "texts" in template["elements"]:
        texts_config = template["elements"]["texts"]
    else: 
        texts_config = None
    
    # Load url suffix if exists
    if "link_suffix" in template:
        suffix = quote(template["link_suffix"])
    else:
        suffix = None
    
    # Create template object with configuration
    try:
        return Template(
            canvas = template["canvas"],
            elements = template["elements"],
            background = template["elements"]["background"],
            texts_config = texts_config,
            link_suffix=suffix
        ).model_dump()
    except Exception as e:
        LOG.exception("Error while creating template object.")
        return None


def get_post_elements(number: int, post: PostData, template: Template) -> dict:
    """Put together all image elements with their settings"""
    
    canvas_size = Canvas(width=template.canvas["width"], height=template.canvas["height"])
    
    # Use post cover as the background image
    if template.background["from_cover"]:
        bg_path = post.cover
    # Or specify path to the custom image (not yet feature)
    else:
        bg_path = template.background.path
    
    # Use image from post (not the background)
    for im_id, image in enumerate(template.elements["images"]):
        if image["from_cover"]:
            template.elements["images"][im_id].update({"path": post.cover})
    
    # Include shapes if exist 
    if "shapes" in template.elements:
        shapes=template.elements["shapes"]
    else:
        shapes=None
    
    # add suffix to the link if exist
    # add only if it's not been already added - this is important when recreating stories
    if template.link_suffix and template.link_suffix not in post.link:
        link = post.link + template.link_suffix
    else:
        link = post.link
    
    # Create list of Text objects with all text parameters 
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
    
    # return dump model so it can be sent in the request
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
    """
    Create dict with metadata of the generated image
    These data are displayed on the show_images page
    Texts and image position can be changed by recreating image
    """
    
    texts = [x.text for x in elements.texts]
    return {
        "number": elements.number,
        "url": f"{elements.post_url}",
        "image": f"{elements.background.path}",
        "image_position_x":elements.background.position[0],
        "min_image_pos_x": elements.background.min_position_x,
        "max_image_pos_x": elements.background.max_position_x,
        "texts": texts,
    }


def get_elements(posts: List[PostData], template: Template) -> List:
    """Create list of elements for each post"""
    
    post_elements = []
    for number, post in enumerate(posts):
        post_elements.append(get_post_elements(number, post, template))
    return post_elements
        

def adjust_elements(elements: ImageElements, metadata: Dict) -> ImageElements:
    """Adjust text, cover image or its position based on user input"""
    
    if not "texts" in metadata:
        LOG.error(f"Key 'texts' missing in metadata -> {metadata}, post -> '{elements.post_url}'")
        return None
    
    # Currently supports only text change and background position
    for text_id, text in enumerate(metadata["texts"]):
        try:
            elements.texts[text_id].text = text
        except KeyError as ke:
            LOG.exception(f"Index '{text_id}' out of the range in 'elements.texts'. Text -> '{text}', Post -> '{elements.post_url}'")
            return None
        except Exception as e:
            LOG.exception(f"Unexpected error while adjusting text '{text}' for '{elements.post_url}'")
            return None
    
    if not "image_position_x" in metadata:
        LOG.error(f"Key 'image_position_x' missing in metadata -> {metadata}, post -> '{elements.post_url}'")
        return None
    
    elements.background.position[0] = int(metadata["image_position_x"])
    
    # Escape HTML characters in the post url before sending it via requests
    elements.post_url = quote(elements.post_url)
        
    return elements.model_dump()