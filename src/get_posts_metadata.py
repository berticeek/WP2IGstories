import requests
from datetime import datetime, timedelta
from typing import List, Set, Dict
from pydantic import BaseModel
import yaml
import os
from urllib.parse import urlparse, urljoin
from html import unescape

from file_paths import template_path, predef_posts_file


POSTS_NUMBER = 5


def get_api_url(site: str) -> str:
    """get url for api connection from template.yaml"""
    with open(template_path(site)) as template:
        template = yaml.safe_load(template)
    return template["url"]


class Posts:
    """Contains functions sending requests to the wordpress api"""
    
    def __init__(self, url):
        self.api_url = url
        
    def has_wrong_tag(self, post_tags: List, exclude_tags: List) -> bool:
        """Check if the post has some tag which is in the ignore list"""
        
        for tag_id in post_tags:
            # Get a tag name by its ID
            tag_api_url = f"{self.api_url}/tags/{tag_id}"
            response = requests.get(tag_api_url)
            if response.status_code != 200:
                continue
            
            # Then check if the tag name is in ignore list
            tag = response.json()
            if tag["name"] in exclude_tags:
                return True
        return False


    def get_latest_posts(self) -> List:
        """
        Retrieve list of the posts posted on previous day (max 20)
        Returns all data retrieved from wordpress API
        """
        
        posts_api_url = f"{self.api_url}/posts"
        
        # Extend by user-selected date on the web
        current_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        previous_date = current_date - timedelta(days=1)
        params = {
            "per_page": 20,
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


def get_valid_posts(api_url: str, pre_posts_len: int, number_posts: int) -> List:
    """
    Get posts published on previous day (later any selected date)
    Then filter out only posts that meet criteria
    """
    
    # Create list of tag names that should be excluded
    exclude_tags = None
    
    posts = Posts(api_url)
    
    # Get all posts from previous day
    posts_list = posts.get_latest_posts()
    if not posts_list:
        raise Exception("Nepodarilo sa získať články")
    
    # Filter out posts with unwanted tags
    for post in reversed(posts_list):
        if exclude_tags == None:
            break
        
        if posts.has_wrong_tag(post["tags"], exclude_tags):
            posts_list.remove(post)
    
    # Return selected number of posts or all of them
    if number_posts != 0:        
        return posts_list[:number_posts - pre_posts_len]
    else:
        return posts_list

class PostData(BaseModel):
    """Basic data retrieved from wordpress used in image"""
    
    title: str
    link: str
    cover: str


def _get_post_cover(api_url: str) -> str:
    """Get link of the post cover image"""
    
    response = requests.get(api_url)
    if response.status_code == 200:
        result = response.json()
        return result["link"]
    else:
        # raise Exception(response.text, response.status_code)
        return None


def get_single_post(api_url: str, post_url: str) -> Dict:
    """Retrieve data of single post defined by its url
    Used for predefined posts"""
    
    # create post api url by its slug
    slug = urlparse(post_url).path.strip("/")
    slug_api_url = os.path.join(api_url, f"posts?slug={slug}")

    response = requests.get(slug_api_url)
    if response.status_code == 200:
        return response.json()[0]
    else:
        return None
    

def get_post_data(url: str, post: Dict) -> PostData:
    """Create PostData object from post data retrieved by api request"""
    
    # Get link of the cover image by its media id
    media_id = post["featured_media"]
    media_api_url = f"{url}/media/{media_id}"
    post_cover = _get_post_cover(media_api_url)
    
    # Unescape special characters which sometimes occurs in title
    if "&#" in post["title"]["rendered"]:
        title = unescape(post["title"]["rendered"])
    else:
        title = post["title"]["rendered"]
    
    # if some of the elements couldn't be retrieved, skip for current post
    if None in [title, post_cover]:
        return None
    
    return PostData(
        title = title,
        link = post["link"],
        cover = post_cover
    ).model_dump()


def get_posts_metadata(site: str, links: List, number_posts: int) -> List[PostData]:
    """Retrieve posts data by api request and create list of metadata objects"""
    
    api_url = get_api_url(site)
    
    pre_posts = []
    
    # If any post links were defined on web, get their data first
    if links:
        for link in links:
            pre_posts.append(get_single_post(api_url, link))
     
    # Append data of remaining posts (either all posts or up to max number)
    posts = pre_posts + get_valid_posts(api_url, len(pre_posts), number_posts)
    posts_data = []  
    
    # Get needed data from posts request responses 
    for post in posts:
        post_data = get_post_data(api_url, post)
        if post_data:
            posts_data.append(post_data)
    return posts_data    
         

def modify_posts_metadata(metadata):
    """Create new list of PostData objects based on modified valus on recreate"""
    
    posts = []
    for post_data in metadata:
        posts.append(
            PostData(
                title = "",
                link = post_data["url"],
                cover = post_data["image"]
        ).model_dump())
    return posts