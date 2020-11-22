import json
import os
import shutil
import time
from collections import defaultdict
from pathlib import Path
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
        if headline.text and "/opt/" in headline.text.lower():
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


def generate_html(posts):
    def process(value):
        value = str(value)
        if value.startswith("http://") or value.startswith("https://"):
            return f"""<a href="{value}">{value}</a>"""
        return value

    fields = [
        "replies",
        "com",
        "series_name",
        "md_url",
        "artist",
        "author",
    ]
    inner_html = ""
    for post in posts:
        details = "\n".join(
            [f"<br><b>{k}:</b> {process(v)}" for k, v in post.items() if k in fields]
        )
        img = f"""<a href="{post['md_url']}"><img src="{post['url']}"></a>"""
        inner_html += f"<div>{img} {details}</div><br>\n"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Spoonfeeder</title>
    <link rel="stylesheet" href="style.css">
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
{inner_html}
</body>
</html>"""


def main():
    no = find_one_page_thread_number()
    thread_url = f"https://a.4cdn.org/a/thread/{no}.json"
    thread = get_json(thread_url)

    # Filter to get posts with images only
    img_posts = defaultdict(lambda: {"replies": 0})
    for post in thread["posts"]:
        if not post.get("ext"):
            continue
        img_post = img_posts[post["no"]]
        img_post.update(
            {
                "com": post.get("com", ""),
                # "url": f"https://i.4cdn.org/a/{post['tim']}{post['ext']}",
                "url": f"https://is2.4chan.org/a/{post['tim']}{post['ext']}",
            }
        )

        # Count number of replies too
        com_soup = BeautifulSoup(img_post["com"], "html.parser")
        for a_tag in com_soup.find_all("a", class_="quotelink"):
            target_id = int(a_tag.attrs["href"][2:])
            if target_id in img_posts:
                img_posts[target_id]["replies"] += 1

    # Transform from dict to list, sort by descending number of (You)s
    img_posts_list = sorted(
        [{**data, "id": id} for id, data in img_posts.items()],
        key=lambda e: e["replies"],
        reverse=True,
    )[:50]

    # Run images through saucenao to get Mangadex id, only keeping those with matches.
    md_results = []
    for post in img_posts_list:
        print(post)
        url = post["url"]
        result = reverse_search(url)
        if result:
            post["series_name"] = result["data"]["source"]
            post["md_url"] = result["data"]["ext_urls"][0]
            post["artist"] = result["data"]["artist"]
            post["author"] = result["data"]["author"]
            md_results.append(post)
        # saucenao API rate limit is 6 requests per 30s
        if len(img_posts_list) > 5:
            time.sleep(5)

    print(md_results)
    # TODO: should dedupe by mangadex id too

    html: str = generate_html(md_results)

    outdir = Path(config["OUTPUT_PATH"])
    os.makedirs(outdir, exist_ok=True)
    with open(outdir / "index.html", "w") as outfile:
        outfile.write(html)
    shutil.copy("style.css", outdir / "style.css")


if __name__ == "__main__":
    main()
