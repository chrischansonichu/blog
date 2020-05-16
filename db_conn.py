import asyncio
from decimal import Decimal
import os
import time
from typing import Dict, List

from async_lru import alru_cache
from asyncache import cached
import boto3
from boto3.dynamodb.conditions import Key, Attr
from cachetools import TTLCache

dynamodb = boto3.resource("dynamodb")
blog_table_name = os.getenv("BLOGTABLE")
blog_table = dynamodb.Table(blog_table_name)


@alru_cache(maxsize=56)
async def get_post_by_id(post_id: str) -> Dict[str, str]:
    """
    Retrieves the entry from the DynamoDB based on the postId key.
    :param post_id: postId Key in the DynamoDB
    :return: Dict containing the DynamoDB Item entries
    """
    item = {"postId": post_id}
    response = blog_table.get_item(Key=item).get("Item")
    return response


@cached(cache=TTLCache(maxsize=128, ttl=600))
async def get_posts_by_attr_is_in(attr, value):
    return blog_table.scan(FilterExpression=Attr(attr).contains(value))


@cached(cache=TTLCache(maxsize=128, ttl=600))
async def get_all_posts():
    return blog_table.scan().get("Items", [])


@cached(cache=TTLCache(maxsize=128, ttl=6000))
async def query_table(key, value):
    response = blog_table.query(KeyConditionExpression=Key(key).eq(value))
    return response


async def add_new_post(
        post_id: str,
        title: str,
        body: str,
        categories: List[str],
        tags: List[str],
        post_thumbnail: str,
        author_name: str,
        author_email: str
):
    """
    Adds a new post to the blog database table.
    :param post_id: unique id for the post
    :param title: title of the post
    :param body: body (in MD or HTML) for the post
    :param categories: list of categories for the post
    :param tags: list of tags for the post
    :param post_thumbnail: thumbnail for the post
    :param author_name: post author's name
    :param author_email: post author's email address
    :return:
    """
    now = int(time.time())
    insert = blog_table.put_item(
        Item={
                "postId": post_id,
                "title": title,
                "body": body,
                "categories": categories,
                "tags": tags,
                "author": {
                    "name": author_name,
                    "email": author_email
                },
                "post_thumbnail": post_thumbnail,
                "date": Decimal(now)
    })
    return insert


if __name__ == '__main__':
    demo_title = asyncio.run(get_post_by_id("demo"))
    print(demo_title)
