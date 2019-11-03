# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# noinspection PyUnresolvedReferences
from codequick import Route, Resolver, Listitem, run
from codequick.utils import urljoin_partial, bold
import urlquick
import xbmcgui

# Localized string Constants
VIDEO_OF_THE_DAY = 30004
POPULAR_VIDEOS = 30002
SELECT_TOP = 30001

BASE_URL = "https://metalvideo.com"
url_constructor = urljoin_partial(BASE_URL)


# noinspection PyUnusedLocal
@Route.register
def root(plugin, content_type="video"):
    """
    :param Route plugin: The plugin parent object.
    :param str content_type: The type of content being listed e.g. video, music. This is passed in from kodi and
                             we have no use for it as of yet.
    """
    yield Listitem.recent(video_list, url="newvideos.html")
    yield Listitem.from_dict(video_list, bold(plugin.localize(POPULAR_VIDEOS)), params={"url": "topvideos.html"})
    yield Listitem.search(search_videos)

    # List Categories
    resp = urlquick.get(url_constructor("/browse.html"))
    root_elem = resp.parse("ul", attrs={"class": "pm-ul-browse-categories list-unstyled thumbnails"})
    for elem in root_elem.iterfind("li/div"):
        url_tag = elem.find("a")
        item = Listitem()

        item.label = url_tag.find("h3").text
        item.art["thumb"] = url_tag.find(".//img").get("src")

        url = url_tag.get("href")
        item.set_callback(video_list, url=url)
        yield item

    # Video of the day
    bold_text = bold(plugin.localize(VIDEO_OF_THE_DAY))
    yield Listitem.from_dict(play_video, bold_text, params={"url": "/index.html"})


@Route.register
def search_videos(plugin, search_query):
    url = url_constructor("/search.php?keywords={}&video-id=".format(search_query))
    return video_list(plugin, url)


@Route.register
def video_list(_, url, related_mode=False):
    """
    List all videos

    :param Route _: The plugin parent object.
    :param str url: The url resource containing recent videos.
    :param bool related_mode: Switch for related video or normal videos.
    """
    resp = urlquick.get(url_constructor(url))
    # Filter results depending on related mode
    if related_mode:
        root_elem = resp.parse("ul", attrs={"class": "pm-ul-sidelist-videos list-unstyled"})
        results = root_elem.iterfind("li")
    else:
        root_elem = resp.parse("div", attrs={"class": "col-md-12"})
        results = root_elem.iterfind("ul/li/div")

    # Process the videos
    for elem in results:
        item = Listitem()

        # Duration
        duration = elem.find("div/span[@class='pm-label-duration']")
        if duration is not None:
            item.info["duration"] = duration.text.strip()

        # Date
        date = elem.find(".//time").get("datetime")
        date = date.split("T", 1)[0]
        item.info.date(date, "%Y-%m-%d")  # 2018-10-19

        # Video url
        url_tag = elem.find(".//a[@class='ellipsis']")
        url = url_tag.get("href")

        # Title & image
        item.label = url_tag.get("title")

        img = elem.find(".//img").attrib
        item.art["thumb"] = img.get("data-echo" if "data-echo" in img else "src")

        item.context.related(video_list, url=url, related_mode=True)
        item.set_callback(play_video, url=url)
        yield item

    # Fetch next page url
    if related_mode is False:
        next_tag = root_elem.find(".//ul[@class='pagination pagination-sm pagination-arrows']")
        if next_tag is not None:
            next_tag = next_tag.findall("li[@class='']/a")
            next_tag.reverse()
            for node in next_tag:
                if node.text == u"\xbb":
                    yield Listitem.next_page(url=node.get("href"), callback=video_list)
                    break


@Route.register
def top_videos(plugin):
    """:param Route plugin: The plugin parent object."""
    # Fetch HTML Source
    url = url_constructor("/topvideos.html")
    resp = urlquick.get(url)
    titles = []
    urls = []

    # Parse categories
    root_elem = resp.parse("select", attrs={"name": "categories"})
    for group in root_elem.iterfind("optgroup[@label]"):
        if group.get("label").lower().startswith("by"):
            for node in group:
                urls.append(node.get("value"))
                titles.append(node.text.strip())

    # Display list for Selection
    dialog = xbmcgui.Dialog()
    ret = dialog.select("[B]{}[/B]".format(plugin.localize(SELECT_TOP)), titles)
    if ret >= 0:
        return video_list(plugin, url=urls[ret])
    else:
        return False


@Resolver.register
def play_video(plugin, url):
    """
    :param Resolver plugin: The plugin parent object.
    :param str url: The url of a video.
    """
    url = url_constructor(url)
    return plugin.extract_source(url)
