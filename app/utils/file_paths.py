"""Retrieve absolute paths to the files used among different modules"""

import os
from pathlib import Path

from app import LOG


def project_folder() -> Path:
    """Project root path"""
    script_folder = Path(__file__).parent
    return script_folder.parent.parent


def template_path(site: str) -> str:
    """Path to stories template file"""
    return project_folder() / "data" / site / "template.yaml"


def predef_posts_file(site: str) -> str:
    """Path to the file with predefined posts links"""
    # Probably not needed anymore, predefined posts are entered on the web
    return project_folder() / "stories" / site / "stories.yaml"


def clear_files(site: str) -> None:
    """Remove created data"""
    
    ignore_files = ["metadata.yaml", "stories.yaml"]
    output_folder = project_folder() / "stories" / site
    
    if not output_folder.exists():
        return None
    
    try:
        for file in os.listdir(output_folder):
            if not file in ignore_files:
                os.remove(os.path.join(output_folder, file))
                
    except NotADirectoryError as nde:
        LOG.exception(f"'{output_folder.absolute}' was not found.")
        return None
    
    except PermissionError as pe:
        LOG.exception(f"Files couldn't be removed.")
        return None