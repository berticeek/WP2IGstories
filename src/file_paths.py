import os

def template_path(site: str) -> str:
    return os.path.join("data", site, "template.yaml")


def predef_posts_file(site: str) -> str:
    return os.path.join("stories", site, "stories.yaml")


def clear_files(site: str) -> None:
    ignore_files = ["metadata.yaml", "stories.yaml"]
    output_folder = os.path.join("stories", site)
    for file in os.listdir(output_folder):
        if not file in ignore_files:
            os.remove(os.path.join(output_folder, file))