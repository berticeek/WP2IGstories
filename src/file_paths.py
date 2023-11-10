import os
from pathlib import Path


SCRIPT_FOLDER = Path(__file__).parent
PROJECT_FOLDER = SCRIPT_FOLDER.parent


def template_path(site: str) -> str:
    return PROJECT_FOLDER / "data" / site / "template.yaml"


def predef_posts_file(site: str) -> str:
    return PROJECT_FOLDER / "stories" / site / "stories.yaml"


def clear_files(site: str) -> None:
    ignore_files = ["metadata.yaml", "stories.yaml"]
    output_folder = PROJECT_FOLDER / "stories" / site
    for file in os.listdir(output_folder):
        if not file in ignore_files:
            os.remove(os.path.join(output_folder, file))