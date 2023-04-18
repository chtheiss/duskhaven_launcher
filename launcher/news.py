import json
import re
import time
from datetime import datetime

import pytz
import requests


def convert_timestamp_to_local_time(timestamp):
    local_time = datetime.fromtimestamp(
        timestamp / 1000, tz=pytz.timezone("UTC")
    ).astimezone()
    formatted_time = local_time.strftime("%B %e at %#I:%M %p").replace("  ", " ")
    return formatted_time


def fetch_announcements():
    url = "https://duskhaven-news.glitch.me/announcements"
    try:
        news = fetch_news(url)
    except requests.exceptions.ConnectionError:
        return []
    return news


def fetch_changelog():
    url = "https://duskhaven-news.glitch.me/changelog"
    try:
        news = fetch_news(url)
    except requests.exceptions.ConnectionError:
        return []
    return news


def fetch_news(url):
    try:
        response = requests.get(url, timeout=0.5)
    except requests.exceptions.Timeout:
        return []
    try:
        news = response.json()
    except json.decoder.JSONDecodeError:
        return []

    news = [n for n in news if n["content"] != "[Original Message Deleted]"]
    news = [
        {
            "timestamp": convert_timestamp_to_local_time(n["createdTimestamp"]),
            "content": n["content"],
        }
        for n in news
    ]
    for n in news:
        n["content"] = n["content"].replace("@everyone", "")
        n["content"] = n["content"].replace("@here", "")
        n["content"] = n["content"].replace("@Updates", "")
        n["content"] = n["content"].replace("@Notify: Updates", "")

        pattern = r"\d{2}\.\d{2}\.\d{4}"
        n["content"] = re.sub(pattern, "", n["content"], flags=re.MULTILINE)

        pattern = r"\*\*(\w+)\*\*"  # Matches "**<word>**"
        n["content"] = re.sub(pattern, r"<b>\1</b>", n["content"], flags=re.MULTILINE)

        n["content"] = n["content"].strip()

    return news


def get_release_notes():
    # Construct the URL for the GitHub API request
    url = "https://api.github.com/repos/chtheiss/duskhaven_launcher/releases"

    # Make the API request and parse the response as JSON
    response = requests.get(url)
    data = response.json()

    if "message" in data and data["message"].startswith("API rate limit exceeded for"):
        return []

    release_notes = [
        {
            "content": release["name"] + "\n\n" + release["body"],
            "timestamp": convert_timestamp_to_local_time(
                int(
                    time.mktime(
                        datetime.strptime(
                            release["created_at"], "%Y-%m-%dT%H:%M:%SZ"
                        ).timetuple()
                    )
                )
                * 1000
            ),
        }
        for release in data
    ]

    # Return the results as a tuple
    return release_notes
