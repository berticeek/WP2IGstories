import requests
from datetime import datetime, timedelta
from typing import List, Set

current_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
previous_date = current_date - timedelta(days=1)


def has_wrong_tag(post_tags, exclude_tags):
    for tag_id in post_tags:
        tag_api_url = f"https://hashtag.zoznam.sk/wp-json/wp/v2/tags/{tag_id}"
        response = requests.get(tag_api_url)
        if response.status_code != 200:
            continue
        
        tag = response.json()
        if tag["name"] in exclude_tags:
            return True
    return False


def get_latest_posts():
    posts_api_url = "https://hashtag.zoznam.sk/wp-json/wp/v2/posts"
    
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


def get_valid_posts():
    exclude_tags = "generaciarapu"
    posts = get_latest_posts()
    if not posts:
        raise Exception("Nepodarilo sa získať články")
    
    for post in reversed(posts):
        if has_wrong_tag(post["tags"], exclude_tags):
            posts.remove(post)
            
    return posts[:5]
        

posts = get_valid_posts()
print()