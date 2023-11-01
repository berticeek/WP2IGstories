import requests
from datetime import datetime, timedelta
from typing import List, Set

current_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
previous_date = current_date - timedelta(days=1)

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
        