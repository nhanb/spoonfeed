import json
from typing import Union

import urllib3
from bs4 import BeautifulSoup

with open("conf.json", "r") as conffile:
    config = json.load(conffile)

client = urllib3.PoolManager(
    headers={"User-Agent": "spoonfeed <https://git.sr.ht/~nhanb/spoonfeed>"}
)


def get_json(url, **kwargs) -> Union[list, dict]:
    resp = client.request("GET", url, **kwargs)
    assert resp.status == 200, resp.data
    return json.loads(resp.data)


def get_html(url) -> BeautifulSoup:
    resp = client.request("GET", url)
    assert resp.status == 200, resp.data
    return BeautifulSoup(resp.data, "html.parser")


def find_one_page_thread_number() -> int:
    # First try the catalog
    print("Checking catalog...")
    pages: list = get_json("https://a.4cdn.org/a/catalog.json")
    for page in pages:
        for thread in page["threads"]:
            if "/opt/" in thread.get("sub", "") or "/opt/" in thread.get("com", ""):
                return thread["no"]

    # If it's not there then try the archive.
    # AFAIK there's no 4chan API that lists all archived thread subjects so let's just
    # parse the html:
    print("Checking archive...")
    archive_html = get_html("https://boards.4channel.org/a/archive")
    for headline in archive_html.find_all("td", class_="teaser-col"):
        if headline.text:
            if "/opt/" in headline.text.lower():
                return int(headline.previous_sibling.text)


def reverse_search(url):
    resp = get_json(
        "https://saucenao.com/search.php",
        fields={
            "api_key": config["SAUCENAO_API_KEY"],
            "url": url,
            "output_type": 2,  # json
            "db": 37,  # mangadex
            # Although I only want the one best match, I can't simply use numres=1 param
            # here, because `numres` is applied _before_ filtering by `db`. This means
            # if we use `db=37&numres=1` and there are 2 results from mangaupdates and
            # mangadex respectively, numres=1 will filter out the latter, and db=37 will
            # filter out the former, leaving us with zero results.
        },
    )
    results = resp.get("results")
    if results:
        return results[0]


if __name__ == "__main__":
    no = find_one_page_thread_number()
    thread_url = f"https://a.4cdn.org/a/thread/{no}.json"
    thread = get_json(thread_url)
    img_urls = [
        f"https://i.4cdn.org/a/{post['tim']}{post['ext']}"
        for post in thread["posts"]
        if post.get("ext")
    ]
    for url in img_urls:
        # TODO: saucenao API rate limit is 6 requests per 30s. Gotta throttle this one.
        result = reverse_search(url)
        if result:
            print(result["data"]["source"])
