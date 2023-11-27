"""Retrieve absolute paths to the files used among different modules"""

import os
from pathlib import Path


SCRIPT_FOLDER = Path(__file__).parent
PROJECT_FOLDER = SCRIPT_FOLDER.parent


def project_folder() -> Path:
    """Project root path"""
    return PROJECT_FOLDER


def template_path(site: str) -> str:
    """Path to stories template file"""
    return PROJECT_FOLDER / "data" / site / "template.yaml"


def predef_posts_file(site: str) -> str:
    """Path to the file with predefined posts links"""
    # Probably not needed anymore, predefined posts are entered on the web
    return PROJECT_FOLDER / "stories" / site / "stories.yaml"


def clear_files(site: str) -> None:
    """Remove created data"""
    ignore_files = ["metadata.yaml", "stories.yaml"]
    output_folder = PROJECT_FOLDER / "stories" / site
    for file in os.listdir(output_folder):
        if not file in ignore_files:
            os.remove(os.path.join(output_folder, file))