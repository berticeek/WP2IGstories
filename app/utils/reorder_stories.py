import os
from pathlib import Path

from app import LOG
from app.utils.file_paths import project_folder


def reorder_stories(metadata: list, site: str) -> list:
    """Fixes order of files and metadatas after story was deleted"""
    
    stories_dir = project_folder() / "stories" / site
    
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