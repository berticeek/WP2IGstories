import logging
import os
import sys
from pathlib import Path

from app import LOG

SCRIPT_FOLDER = Path(__file__).parent
PROJECT_FOLDER = SCRIPT_FOLDER.parent


def delete_story_file(metadata, site):
    """Deletes png file and all stored data related to the selected story"""
    
    stories_dir = PROJECT_FOLDER / "stories" / site
    file_path = stories_dir / (str(metadata["number"]) + ".png")
    
    # Check if file exist
    if not file_path.exists():
        LOG.error(f"File '{file_path}' does not exists and will not be removed")
        return None
    
    # Delete file
    LOG.info(f"Removing file: '{file_path}'")
    try:
        os.remove(file_path)
    except IOError as e:
        LOG.exception(f"File '{file_path}' can not be deleted.")
        return(None)
    
    return True
            