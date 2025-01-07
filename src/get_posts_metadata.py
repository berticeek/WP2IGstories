import logging
import requests
import os
import sys
from datetime import datetime, timedelta
from html import unescape
from typing import List, Dict
from urllib.parse import urlparse

import yaml
from pydantic import BaseModel

from .file_paths import template_path, predef_posts_file

LOG = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
LOG.addHandler(handler)

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
                LOG.info(f"Tag: {tag['name']} with ID: {tag_id} found in post.")
                return True
        return False


    def get_latest_posts(self, posts_from: str) -> List:
        """
        Retrieve list of the posts posted on previous day (max 20)
        Returns all data retrieved from wordpress API
        """
        
        posts_api_url = f"{self.api_url}/posts"
        LOG.info(f"Getting posts data from: '{posts_api_url}'")
        
        # Get posts by user-selected date on the web
        from_date = datetime.strptime(posts_from, '%Y-%m-%d')
        to_date = from_date + timedelta(days=1)
        
        if not from_date < datetime.today():
            LOG.warning(f"Selected date is higher than today, setting date automatically for today...")
            from_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
            
        params = {
            "per_page": 20,
            "status": "publish",
            "before": to_date.isoformat(),
            "after": from_date.isoformat(),
        }

        LOG.info(f"Request parameters: {params}")

        try:
            response = requests.get(posts_api_url, params=params)
            if response.status_code == 200:
                posts = response.json()
                # Exclude post content from the response to not overwhelm log
                LOG.info(f"Posts retrieved:\n{[{k:v for k, v in post.items() if k != 'content'} for post in posts]}")
                return posts
            else:
                LOG.warning(f"Unexpected response: {response.text}")
                return None

            
        except:
            LOG.exception("Failed to retrieve posts.")


def get_valid_posts(api_url: str, pre_posts_len: int, number_posts: int, posts_from: str) -> List:
    """
    Get posts published on previous day (later any selected date)
    Then filter out only posts that meet criteria
    """
    
    # Create list of tag names that should be excluded
    exclude_tags = None
    
    posts = Posts(api_url)
    
    # Get all posts from previous day
    posts_list = posts.get_latest_posts(posts_from)
    if not posts_list:
        LOG.error("Nepodarilo sa získať články")
        return []
    
    # Filter out posts with unwanted tags
    for post in reversed(posts_list):
        if exclude_tags is None:
            break
        
        LOG.info(f"Filtering out posts with tags: {exclude_tags}")
        if posts.has_wrong_tag(post["tags"], exclude_tags):
            LOG.info(f"Post {post['link']} will be skipped.")
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
        LOG.warning(f"Cover image {api_url} cannot be retrieved:\n{response.text}")
        # raise Exception(response.text, response.status_code)
        return None


def get_single_post(api_url: str, post_url: str) -> Dict:
    """Retrieve data of single post defined by its url
    Used for predefined posts"""
    
    # create post api url by its slug
    slug = urlparse(post_url).path.strip("/")
    slug_api_url = os.path.join(api_url, f"posts?slug={slug}")

    LOG.info(f"Getting data for the post '{post_url}'")
    response = requests.get(slug_api_url)
    if response.status_code == 200:
        return response.json()[0]
    else:
        LOG.info(f"Post data couldn't be retrieved: {response.text}")
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
        LOG.warning("Cover image or title was not retrieved.")
        LOG.warning(f"Post {post['link']} will be skipped.")
        return None
    
    return PostData(
        title = title,
        link = post["link"],
        cover = post_cover
    ).model_dump()


def get_posts_metadata(site: str, links: List, number_posts: int, posts_from: str) -> List[PostData]:
    """Retrieve posts data by api request and create list of metadata objects"""
    
    api_url = get_api_url(site)
    
    pre_posts = []
    
    # If any post links were defined on web, get their data first
    if links:
        for link in links:
            pre_posts.append(get_single_post(api_url, link))
     
    # Append data of remaining posts (either all posts or up to max number)
    posts = pre_posts + get_valid_posts(api_url, len(pre_posts), number_posts, posts_from)
    if not posts:
        raise LookupError("No posts found by given criteria")

    posts_data = []
    
    # Get needed data from posts request responses 
    for post in posts:
        post_data = get_post_data(api_url, post)
        if post_data:
            LOG.info(f"Created PostData object: {post_data}")
            posts_data.append(post_data)
    
    if posts_data:
        return posts_data    
    else:
        raise ValueError("Posts data model cannot be obtained")
         

def modify_posts_metadata(metadata):
    """Create new list of PostData objects based on modified valus on recreate"""
    
    posts = []
    for post_data in metadata:
        LOG.info(f"New post data: {post_data}")
        posts.append(
            PostData(
                title = "",
                link = post_data["url"],
                cover = post_data["image"]
        ).model_dump())
    return posts