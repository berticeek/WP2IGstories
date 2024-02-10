"""Collects all neccessary data and calls function for creating image file out of them"""

import os
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote

from envyaml import EnvYAML
from pydantic import BaseModel

from app import LOG
from app.models.canvas import ImageElements
from app.utils.canvas import create_canvas, merge_elements
from app.utils.file_paths import clear_files, project_folder
from app.utils.stories_data import store_metadata
        

def create_stories(site: str, posts_elements: List[ImageElements]) -> List:
    """Call function for creating image for every single entry in the posts_elements 
    and return data about created images"""
    
    # remove all previously created stories
    # consider changing it with deleting them always after session's closed, 
    # or storing them in the tmp dir which is deleted at the session end
    clear_files(site)
    
    metadata = []
    
    # Check if stories folder exists and create it if not
    stories_dir = project_folder() / "stories"
    if not stories_dir.exists():
        LOG.info(f"Creating folder -> {str(stories_dir)}")
        try:
            os.mkdir(stories_dir)
        except PermissionError as e:
            LOG.exception(f"Error during folder creation -> {str(stories_dir)}")
            return None
    
    for elems in posts_elements:
        # Create single image
        if not create_story(elems, site):
            LOG.error(f"Image creation failed -> elements: {elems}")
            continue
        
        # Check if site specific story folder exists and create it if not
        output_folder = stories_dir / site
        if not os.path.isdir(output_folder):
            LOG.info(f"Creating output folder: {str(output_folder)}")
            try:
                os.mkdir(output_folder)
            except PermissionError as pe:
                LOG.exception("Failed creating output folder.")
                return None
            except Exception as e:
                LOG.exception(f"Error during folder creation -> {str(output_folder)}")
                return None
                
        
        # create file with links to posts
        # needed when downloading stories 
        with open(output_folder / "links.txt", "a") as links:
            links.write(f"{elems.number}: {elems.post_url}\n")

        metadata.append(store_metadata(elems))

    LOG.info(f"Successfully created {len(metadata)} images.")
    return metadata


def create_story(post_elements: ImageElements, site: str) -> Path:
    """Create and save image file. 
    Returns True if image was saved"""
    
    is_ok = True
    
    stories_site_dir = project_folder() / "stories" / site
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
        