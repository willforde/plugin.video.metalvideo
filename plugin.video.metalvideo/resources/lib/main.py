# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# noinspection PyUnresolvedReferences
from codequick import Route, Resolver, Listitem, run
from codequick.utils import urljoin_partial, bold
import urlquick
import xbmcgui

# Localized string Constants
SELECT_TOP = 30001
TOP_VIDEOS = 30002
FEATURED = 30005
PARTY_MODE = 589

BASE_URL = "https://www.metalvideo.com"
url_constructor = urljoin_partial(BASE_URL)


# noinspection PyUnusedLocal
@Route.register
def root(plugin, content_type="video"):
    """
    :param Route plugin: The plugin parent object.
    :param str content_type: The type of content being listed e.g. video, music. This is passed in from kodi and
                             we have no use for it as of yet.
    """
    yield Listitem.recent(video_list, url="/newvideos.html")
    yield Listitem.from_dict(top_videos, bold(plugin.localize(TOP_VIDEOS)))
    yield Listitem.from_dict(video_list, bold(plugin.localize(FEATURED)), params={
        "url": "/index.html",
        "filter_mode": 2
    })
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

        # Add Context menu item to sort by Views, Ratings and/or Title
        for sort in ("views", "rating", "title"):
            sort_url = url.replace("date.html", "{}.html".format(sort))
            item.context.container(video_list, "By {}".format(sort), url=sort_url)

        item.set_callback(video_list, url=url)
        yield item

    # Video of the day
    yield Listitem.from_dict(party_play, plugin.localize(PARTY_MODE), params={"url": "/index.html"})


@Route.register
def search_videos(plugin, search_query):
    url = url_constructor("/search.php?keywords={}&video-id=".format(search_query))
    return video_list(plugin, url)


@Route.register
def top_videos(plugin):
    """:param Route plugin: The plugin parent object."""

    links = [
        ("All time", "https://www.metalvideo.com/topvideos.html"),
        ("Highest rated", "https://www.metalvideo.com/topvideos.html?do=rating"),
        ("Last 3 days", "https://www.metalvideo.com/topvideos.html?do=recent")
    ]

    resp = urlquick.get(url_constructor("/topvideos.html"))
    root_elem = resp.parse("ul", attrs={"role": "menu"})
    for link in root_elem.iterfind(".//a"):
        href = link.get("href")
        if "topvideos.html?c=" in href:
            links.append((link.text, href))

    # Display list for Selection
    dialog = xbmcgui.Dialog()
    titles, urls = zip(*links)
    ret = dialog.select("[B]{}[/B]".format(plugin.localize(SELECT_TOP)), titles)
    if ret >= 0:
        return video_list(plugin, url=urls[ret])
    else:
        return False


@Route.register
def video_list(_, url, filter_mode=0):
    """
    List all videos

    :param Route _: The plugin parent object.
    :param str url: The url resource containing recent videos.
    :param bool filter_mode: Switch to filter results by related video, normal videos or featured videos.
    """
    resp = urlquick.get(url_constructor(url))

    # Filter results depending on related mode
    if filter_mode == 0:  # Normal Videos
        root_elem = resp.parse("div", attrs={"class": "col-md-12"})
        results = root_elem.iterfind("ul/li/div")
    elif filter_mode == 1:  # Related videos
        root_elem = resp.parse("ul", attrs={"class": "pm-ul-sidelist-videos list-unstyled"})
        results = root_elem.iterfind("li")
    elif filter_mode == 2:  # Featured Videos
        root_elem = resp.parse("ul", attrs={"id": "pm-carousel_featured"})
        results = root_elem.iterfind("li/div")
    else:
        raise ValueError("unexpected filter_mode value: {}".format(filter_mode))

    # Process the videos
    for elem in results:
        item = Listitem()

        # Duration
        duration = elem.find("div/span[@class='pm-label-duration']")
        if duration is not None:
            item.info["duration"] = duration.text.strip()

        # Date
        date = elem.find(".//time")
        if date is not None:
            date = date.get("datetime").split("T", 1)[0]
            item.info.date(date, "%Y-%m-%d")  # 2018-10-19

        # Video url
        url_tag = elem.find(".//a[@class='ellipsis']")
        url = url_tag.get("href")

        # Title & image
        item.label = url_tag.get("title")

        img = elem.find(".//img").attrib
        item.art["thumb"] = img.get("data-echo" if "data-echo" in img else "src")

        item.context.related(video_list, url=url, filter_mode=1)
        item.set_callback(play_video, url=url)
        yield item

    # Fetch next page url
    if filter_mode == 0:
        next_tag = root_elem.find(".//ul[@class='pagination pagination-sm pagination-arrows']")
        if next_tag is not None:
            next_tag = next_tag.findall("li[@class='']/a")
            next_tag.reverse()
            for node in next_tag:
                if node.text == u"\xbb":
                    yield Listitem.next_page(url=node.get("href"), callback=video_list)
                    break


@Resolver.register
def play_video(plugin, url):
    """
    :param Resolver plugin: The plugin parent object.
    :param str url: The url of a video.
    """
    url = url_constructor(url)
    return plugin.extract_source(url)


@Resolver.register
def party_play(plugin, url):
    """
    :param Resolver plugin: The plugin parent object.
    :param str url: The url to a video.
    :return: A playlist with the first item been a playable video url and the seconde been a callback url that
             will fetch the next video url to play.
    """
    # Attempt to fetch a video url 3 times
    attempts = 0
    while attempts < 3:
        try:
            video_url = play_video(plugin, url)
        except Exception as e:
            # Raise the Exception if we are on the last run of the loop
            if attempts == 2:
                raise e
        else:
            if video_url:
                # Break from loop when we have a url
                return plugin.create_loopback(video_url)

        # Increment attempts counter
        attempts += 1
