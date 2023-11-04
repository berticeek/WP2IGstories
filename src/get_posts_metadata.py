import requests
from datetime import datetime, timedelta
from typing import List, Set
from pydantic import BaseModel


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


def get_valid_posts(api_url: str) -> List:
    exclude_tags = "generaciarapu"
    
    posts = Posts(api_url)
    
    posts_list = posts.get_latest_posts()
    if not posts_list:
        raise Exception("Nepodarilo sa získať články")
    
    for post in reversed(posts_list):
        if posts.has_wrong_tag(post["tags"], exclude_tags):
            posts_list.remove(post)
            
    return posts_list[:5]


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
    

def get_post_data(url, post) -> PostData:
    media_id = post["featured_media"]
    media_api_url = f"{url}/media/{media_id}"
    post_cover = _get_post_cover(media_api_url)
    return PostData(
        title = post["title"]["rendered"],
        link = post["link"],
        cover = post_cover
    )


def get_posts_metadata(api_url: str) -> List[PostData]:
    posts = get_valid_posts(api_url)
    posts_data = []  
    for post in posts:
        posts_data.append(get_post_data(api_url, post))
    return posts_data    
         