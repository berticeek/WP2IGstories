from urllib.parse import unquote


def url_decode(value):
    return unquote(value)