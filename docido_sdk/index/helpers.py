
import requests


def push_thumbnails_from_links(index_api, thumbnails):
    def dl_url(id_, url):
        r = requests.get(url)
        if r.status_code == 200:
            encoded_bytes = r.content.encode("base64")
            return id_, encoded_bytes, r.headers['content-type']
    index_api.add_thumbnails(map(dl_url, thumbnails))
