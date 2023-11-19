import requests
from datetime import datetime, timedelta
from typing import List, Set, Dict
from pydantic import BaseModel
import yaml
import os
from urllib.parse import urlparse, urljoin

from file_paths import template_path, predef_posts_file


POSTS_NUMBER = 5


def get_api_url(site: str) -> str:
    with open(template_path(site)) as template:
        template = yaml.safe_load(template)
    return template["url"]


class Posts:
    def __init__(self, url):
        self.api_url = url
        
    def has_wrong_tag(self, post_tags, exclude_tags):
        for tag_id in post_tags:
            tag_api_url = f"{self.api_url}/tags/{tag_id}"
            response = requests.get(tag_api_url)
            if response.status_code != 200:
                continue
            
            tag = response.json()
            if tag["name"] in exclude_tags:
                return True
        return False


    def get_latest_posts(self):
        posts_api_url = f"{self.api_url}/posts"
        
        current_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        previous_date = current_date - timedelta(days=1)
        params = {
            "per_page": 15,
            "status": "publish",
            "before": current_date.isoformat(),
            "after": previous_date.isoformat(),
        }

        response = requests.get(posts_api_url, params=params)
        
        if response.status_code == 200:
            posts = response.json()
            return posts
            
        else:
            print("Failed to retrieve posts. Status code:", response.status_code)
            return None


def get_valid_posts(api_url: str, pre_posts_len: int) -> List:
    num_newest_posts = POSTS_NUMBER - pre_posts_len
    
    exclude_tags = "generaciarapu"
    
    posts = Posts(api_url)
    
    posts_list = posts.get_latest_posts()
    if not posts_list:
        raise Exception("Nepodarilo sa získať články")
    
    for post in reversed(posts_list):
        if posts.has_wrong_tag(post["tags"], exclude_tags):
            posts_list.remove(post)
            
    return posts_list[:num_newest_posts]


def check_predefined_posts(site: str, posts: List) -> List:
    api_url = get_api_url(site)
    
    with open(predef_posts_file(site), "r") as f:
        predef_posts = yaml.safe_load(f)
    
    for p_id, post in enumerate(predef_posts):
        if post["url"]:
            posts[p_id] = get_single_post(api_url, post["url"])
    
    return posts

class PostData(BaseModel):
    title: str
    link: str
    cover: str


def _get_post_cover(api_url):
    response = requests.get(api_url)
    if response.status_code == 200:
        result = response.json()
        return result["link"]
    else:
        raise Exception(response.text, response.status_code)


def get_single_post(api_url: str, post_url: str) -> Dict:
    slug = urlparse(post_url).path.strip("/")
    slug_api_url = os.path.join(api_url, f"posts?slug={slug}")

    response = requests.get(slug_api_url)
    if response.status_code == 200:
        return response.json()[0]
    else:
        return None
    

def get_post_data(url, post) -> PostData:
    media_id = post["featured_media"]
    media_api_url = f"{url}/media/{media_id}"
    post_cover = _get_post_cover(media_api_url)
    return PostData(
        title = post["title"]["rendered"],
        link = post["link"],
        cover = post_cover
    ).model_dump()


def get_posts_metadata(site: str, links: List) -> List[PostData]:
    api_url = get_api_url(site)
    
    pre_posts = []
    
    if links:
        for link in links:
            pre_posts.append(get_single_post(api_url, link))
    
    
    posts = pre_posts + get_valid_posts(api_url, len(pre_posts))
    # posts = check_predefined_posts(site, posts)
    posts_data = []  
    for post in posts:
        posts_data.append(get_post_data(api_url, post))
    return posts_data    
         

def modify_posts_metadata(metadata):
    posts = []
    for post_data in metadata:
        posts.append(
            PostData(
                title = "",
                link = post_data["url"],
                cover = post_data["image"]
        ).model_dump())
    return posts