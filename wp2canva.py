from get_posts_metadata import get_valid_posts

api_url = "https://hashtag.zoznam.sk/wp-json/wp/v2"

posts = get_valid_posts(api_url)
print()