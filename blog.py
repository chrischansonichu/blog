from collections import Counter
from functools import reduce
from os import path, getenv
import time
from typing import Dict, List, Union

from async_lru import alru_cache
import markdown2
import quart
from quart import Quart, render_template, make_response, request

import db_conn
from utils.django_utils import truncate_html_words

ROOT_DIR = path.abspath(path.dirname(path.abspath(path.dirname(__file__))))

app = Quart(__name__,
            static_folder=path.join(ROOT_DIR, "static"),
            static_url_path="/static")
app.secret_key = getenv("SECRETKEY", "")


def markup(string: str, markup_=True) -> str:
    """
    Converts a MD string to HTML string, Markup safe or raw.
    :param string: Markdown string.
    :param markup_: bool determines whether or not to output as Markup safe
    :return: HTML string.
    """
    if string.startswith("<"):
        output = string
    else:
        output = markdown2.markdown(string, extras=["tables", "fenced-code-blocks"])
    if markup_:
        return quart.Markup(output)
    else:
        return output


def body_markup(post: Dict[str, str], markup_=True) -> Dict[str, str]:
    """
    Returns the post dict as one with the MD converted to potentially-Markup-safe HTML.
    :param post: Post dict from db_conn.get_post_by_id.
    :param markup_: bool determines whether or not to convert to Markup-safe HTML
    :return: Identical to the post dict passed as an arg, but with the MD as HTML.
    """
    return {**post, **{"body": markup(post["body"], markup_=markup_)}}


def truncate_post(post: Dict[str, str], words: int = 85) -> Dict[str, str]:
    """
    Truncates the HTML of a post to fit on the index page.
    :param post: Post dict from db_conn.get_post_by_id, with HTML text rather than MD.
    :param words: Number of words to truncate the post to. Default: 85.
    :return: Identical to the post dict passed as an arg, but with the HTML truncated to the specified number of words.
    """
    return {**post, **{"body": quart.Markup(truncate_html_words(post["body"], words))}}


def preview_posts(posts: List[Dict], num_posts: int = 3):
    """
    Returns a subset of the list of posts, with the post body truncated
    :param posts: List of post dicts
    :param num_posts: Number of posts to truncate and return.
    :return: num_posts number of posts, with the body truncated and marked Markup-safe.
    """
    last_x_posts = posts[:num_posts]
    rendered_posts = (body_markup(x, False) for x in last_x_posts)
    truncated_posts = map(truncate_post, rendered_posts)
    return truncated_posts


def category_counter(d: List[Dict]) -> List[Dict[str, Union[str, int]]]:
    count: Counter = Counter(reduce(lambda x, y: x+y["categories"], d, []))
    return [{"name": x, "count": y} for x, y in count.items()]


async def get_all_posts_by_date():
    return sorted(await db_conn.get_all_posts(), key=lambda x: x["date"], reverse=True)


@app.template_filter("env")
def env(key: str) -> str:
    """
    Template filter that allows retrieving environ vars in the Jinja2 template.
    :param key: Environ var key
    :return: the environ var value; empty string if not found.
    """
    return getenv(key, "")


@app.template_filter('ctime')
def time_ctime(timestamp: int) -> str:
    """
    Template filter to convert a UNIX Epoch timestamp to a nice readable datetime string.
    :param timestamp: UNIX Epoch timestamp
    :return: Weekday Month Day HH:MM:ss Year
    """
    return time.ctime(int(timestamp))


@app.route("/")
async def index():
    """
    Index page.
    :return: Response object containing HTML string of the Index (/) page.
    """
    all_posts = await get_all_posts_by_date()
    truncated_posts = preview_posts(all_posts)
    counted_categories = category_counter(all_posts)
    return await make_response(await render_template("main.html",
                                                     title="Main",
                                                     posts=truncated_posts,
                                                     categories=counted_categories,
                                                     include_sidebar=True))


# @cached(cache=TTLCache(maxsize=128, ttl=6000))
@app.route("/post/<string:post_id>")
async def get_post(post_id: str):
    """
    Returns a blog post page for a given post ID.
    :param post_id: post ID.
    :return: Response object containing an HTML string.
    """
    try:
        post = await db_conn.get_post_by_id(post_id=post_id)
        marked_up_post = body_markup(post)
        return await make_response(
            await render_template("post.html", **marked_up_post)
        )
    except (AttributeError, TypeError):
        return quart.abort(404)


@app.route("/latest")
async def latest():
    """
    Redirects to the most recent blog post page.
    :return: Most recent blog post, 404 page if no posts exist.
    """
    all_posts = await get_all_posts_by_date()
    try:
        latest_post = all_posts[0]
        return quart.redirect(f"/post/{latest_post['postId']}")
    except IndexError:
        return quart.abort(404)


@app.route("/write_post")
async def write_post():
    """
    Not yet implemented.
    """
    return await make_response(await render_template("write_post.html"))


@app.route("/submit_post", methods=["POST"])
async def submit_post():
    """
    Returns the data passed to it in JSON format. For the not-yet-implemented write_post function to hit.
    :return: JSON of data passed to it.
    """
    data = await request.form
    body = data.get("post_body")
    return quart.jsonify(data)


@app.route("/categories/<string:category>")
async def categories(category):
    """
    Retrieves the posts in the specified category.
    :param category: category of the post
    :return: main.html template, rendered with the up-to-five most recent posts from the category
    """
    posts = await db_conn.get_posts_by_attr_containing("categories", category)
    truncated_posts = preview_posts(posts["Items"], 5)
    return await render_template("main.html",
                                 subtitle=f"Posts in category: {category}",
                                 posts=truncated_posts)


@app.route("/tags/<string:tag>")
async def tags(tag):
    """
    Retrieves the posts tagged with the specified tag.
    :param tag: tag of the post
    :return: main.html template, rendered with the up-to-five most recent posts from the tag
    """
    posts = await db_conn.get_posts_by_attr_containing("tags", tag)
    truncated_posts = preview_posts(posts["Items"], 5)
    return await render_template("main.html",
                                 subtitle=f"Posts tagged as: {tag}",
                                 posts=truncated_posts)


@alru_cache()
@app.route("/favicon.ico")
async def favicon():
    return await app.send_static_file("favicon.ico")


@app.errorhandler(404)
async def page_not_found(e):
    """
    404 page
    """
    return await make_response(
        await render_template("error.html",
                              title=e,
                              error="Unable to locate that page. Check the URL.")
    )


if __name__ == '__main__':
    app.run(host="localhost", port=8080, debug=True)
