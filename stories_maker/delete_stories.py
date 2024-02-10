import logging
import os
import sys
from pathlib import Path

SCRIPT_FOLDER = Path(__file__).parent
PROJECT_FOLDER = SCRIPT_FOLDER.parent

LOG = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
LOG.addHandler(handler)


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


def reorder_stories(metadata: list, site: str) -> list:
    """Fixes order of files and metadatas after story was deleted"""
    
    stories_dir = PROJECT_FOLDER / "stories" / site
    
    # Rename files to keep correct (ascending) order
    files = [x for x in os.listdir(stories_dir) if os.path.splitext(x)[1] == ".png"]
    # Sort filenames in the correct way (so 10.png is not right after 1.png)
    files.sort(key=lambda f: int(''.join(filter(str.isdigit, f))))
    
    LOG.info("Reordering files and stored metadata...")
    
    for i, filename in enumerate(files):
        if os.path.splitext(filename)[0] == str(i):
            continue
        try:
            LOG.info(f"Renaming file '{str(stories_dir / filename)}' -> '{str(stories_dir / (str(i)+'.png'))}'")
            os.rename(stories_dir / filename, stories_dir / (str(i)+".png"))
        except IOError as e:
            LOG.exception(f"File '{filename}' can not be renamed to '{i}.png'")
            return None
        
    # Fix metadata numbers order
    for i, story_data in enumerate(metadata):
        if story_data["number"] == i:
            continue
        story_data["number"] = i
        
    return metadata
            