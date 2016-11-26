"""
Copyright: (c) 2016 William Forde (willforde+kodi@gmail.com)
License: GPLv3, see LICENSE for more details

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import re
import urlparse
import codequick as plugin

plugin.strings.update(video_of_the_day=30104, watching_now=30105, random_video=30103,
                      top_videos=30102, select_top=30101)


def fetch_query(url, key):
    """Parses a url and return the vid parameter"""
    href = urlparse.urlsplit(url)
    return urlparse.parse_qs(href.query)[key][0]


@plugin.route("/")
def root():
    # Fetch HTML Source
    url = u"http://metalvideo.com/mobile/category.html"
    html = plugin.requests_session().get(url, headers={"Cookie": "COOKIE_DEVICE=mobile", "x-max-age": 604800}).text
    icon = plugin.get_info("icon")

    # Run SpeedForce to attempt to strip Out any unneeded html tags
    stripper = plugin.utils.ETBuilder(u"ul", attrs={u"id": u"category_listing"})
    root_elem = stripper.run(html)
    for elem in root_elem.iterfind("li"):
        a_tag = elem.find("a")
        item = plugin.ListItem()
        item.art["thumb"] = icon

        # Set label with video count added
        item.label = u"%s (%s)" % (a_tag.text, elem.find("span").text)

        # Fetch category
        item.url["cat"] = fetch_query(a_tag.get("href"), "cat")
        yield item.get(video_list)

    yield plugin.ListItem.add_recent(recent_videos)
    yield plugin.ListItem.add_item(play_video, plugin.localize("video_of_the_day"), icon, url=u"index.html")
    yield plugin.ListItem.add_item(party_play, plugin.localize("random_video"), icon, url=u"randomizer.php")
    yield plugin.ListItem.add_item(top_videos, plugin.localize("top_videos"), icon)
    yield plugin.ListItem.add_item(watching_now, plugin.localize("watching_now"), icon)
    yield plugin.ListItem.add_search(video_list, url=u"search.php?keywords=%s")


@plugin.route("/recent_videos")
def recent_videos():
    # Fetch HTML Source
    url = u"http://metalvideo.com/%s" % plugin.params.get(u"url", u"newvideos.php")
    html = plugin.requests_session().get(url).text

    # Run SpeedForce to atempt to strip Out any unneeded html tags
    stripper = plugin.utils.ETBuilder(u"div", attrs={u"id": u"browse_main"})
    root_elem = stripper.run(html)
    node = root_elem.find("./div[@id='newvideos_results']")[0]
    for elem in node.iterfind("./tr"):
        if not elem.attrib:
            item = plugin.ListItem()
            item.art["thumb"] = elem.find(".//img").get("src")

            artist = elem[1].text
            track = elem[1][0][0].text
            item.label = u"%s - %s" % (artist, track)
            item.info["artist"] = [artist]

            # Fetch video id
            videoid = fetch_query(elem.find(".//a").get("href"), "vid")
            item.url["videoid"] = videoid

            # Add related video context item
            item.context.related(related, videoid=videoid)
            yield item.get(play_video)

    # Fetch next page url
    next_tag = root_elem.find("./div[@class='pagination']").findall("./a")[-1]
    if next_tag.text.startswith("next"):
        yield plugin.ListItem.add_next(url=next_tag.get("href"))


@plugin.route("/watching_now")
def watching_now():
    # Fetch HTML Source
    url = u"http://metalvideo.com/index.html"
    html = plugin.requests_session().get(url).text

    # Run SpeedForce to atempt to strip Out any unneeded html tags
    stripper = plugin.utils.ETBuilder(u"ul", attrs={u"id": u"mycarousel"})
    root_elem = stripper.run(html)
    for elem in root_elem.iterfind("li"):
        a_tag = elem.find(".//a[@title]")
        item = plugin.ListItem()

        item.label = a_tag.text
        item.art["thumb"] = elem.find(".//img").get("src")

        # Fetch video id from url
        videoid = fetch_query(a_tag.get("href"), "vid")
        item.url["videoid"] = videoid

        # Add related video context item
        item.context.related(related, videoid=videoid)
        yield item.get(play_video)


@plugin.route("/topvideos")
def top_videos():
    # Fetch HTML Source
    url = u"http://metalvideo.com/topvideos.html"
    html = plugin.requests_session().get(url, headers={"x-max-age": 604800}).text
    titles = []
    urls = []

    # Parse categories
    flash = plugin.utils.ETBuilder(u"select", attrs={u"name": u"categories"})
    root_elem = flash.run(html)
    for group in root_elem.iterfind("optgroup"):
        for elem in group:
            urls.append(elem.get("value"))
            titles.append(elem.text)

    import xbmcgui
    # Display list for Selection
    dialog = xbmcgui.Dialog()
    ret = dialog.select(plugin.localize("select_top"), titles)
    if ret >= 0:
        # Fetch HTML Source
        url = urls[ret]
        html = plugin.requests_session().get(url).text

        # Parse top videos
        flash = plugin.utils.ETBuilder(u"div", attrs={u"id": u"topvideos_results"})
        root_elem = flash.run(html)
        for elem in root_elem.iterfind(".//tr"):
            if not elem.attrib:
                item = plugin.ListItem()
                a_tag = elem[3][0]

                artist = elem[2].text
                item.label = u"%s %s - %s" % (elem[0].text, artist, a_tag.text)
                item.art["thumb"] = elem.find(".//img").get("src")
                item.info["count"] = elem[4].text.replace(u",", u"")
                item.info["artist"] = [artist]

                # Fetch videoid
                videoid = fetch_query(a_tag.get("href"), "vid")
                item.url["videoid"] = videoid

                # Add related video context item
                item.context.related(related, videoid=videoid)
                yield item.get(play_video)


@plugin.route("/related")
def related():
    # Fetch HTML Source
    url = u"http://metalvideo.com/relatedclips.php?vid=%(videoid)s" % plugin.params
    xml = plugin.requests_session().get(url).text

    # Parse the xml
    import xml.etree.ElementTree as ElementTree
    root_elem = ElementTree.fromstring(xml)
    for elem in root_elem.iterfind(u"video"):
        item = plugin.ListItem()
        item.label = elem.findtext(u"title")
        item.art["thumb"] = elem.findtext(u"thumb")

        # Fetch video id
        videoid = fetch_query(elem.findtext(u"url"), "vid")
        item.url["videoid"] = videoid

        # Add related video context item
        item.context.related(related, videoid=videoid)
        yield item.get(play_video)


@plugin.route("/videos")
def video_list():
    # Fetch HTML Source
    if u"url" in plugin.params:
        url = u"http://metalvideo.com/%(url)s" % plugin.params
    else:
        sortby = {0: u"date", 1: u"artist", 2: u"rating", 3: u"views"}[plugin.get_setting("sort")]
        url = u"http://metalvideo.com/category.php?cat=%s&sortby=%s" % (plugin.params["cat"], sortby)
    html = plugin.requests_session().get(url).text

    # Run SpeedForce to atempt to strip Out any unneeded html tags
    stripper = plugin.utils.ETBuilder(u"div", attrs={u"id": u"browse_main"})
    root_elem = stripper.run(html)
    for elem in root_elem.iterfind(u".//div[@class='video_i']"):
        a_tag = elem.findall("a")[-1]
        item = plugin.ListItem()
        item.art["thumb"] = elem.find(".//img").get("src")

        # Fetch title
        span_tags = tuple([node.text for node in a_tag.findall("span")])
        item.label = "%s - %s" % span_tags
        item.info["artist"] = [span_tags[0]]

        # Fetch videoid
        videoid = fetch_query(a_tag.get("href"), "vid")
        item.url["videoid"] = videoid

        # Add related video context item
        item.context.related(related, videoid=videoid)
        yield item.get(play_video)

    # Fetch next page url
    next_tag = root_elem.find(".//div[@class='pagination']").findall("./a")[-1]
    if next_tag.text.startswith("next"):
        yield plugin.ListItem.add_next(url=next_tag.get("href"))


@plugin.resolve("/playvideo")
def play_video():
    # Fetch HTML Source
    if u"url" in plugin.params:
        url = u"http://metalvideo.com/%(url)s" % plugin.params
    else:
        url = u"http://metalvideo.com/musicvideo.php?vid=%(videoid)s" % plugin.params
    html = plugin.requests_session().get(url).text

    # Look for Youtube Video First
    try:
        search_regx = 'src="(http://www.youtube.com/embed/\S+?)"|file:\s+\'(\S+?)\''
        match = re.findall(search_regx, html)[0]
        url = filter(None, match)[0]
    except IndexError:
        pass
    else:
        if u"metalvideo.com" in url:
            return url
        elif u"youtube.com" in url:
            return plugin.youtube.parse_url(url)


@plugin.resolve("/partymode")
def party_play(tools):
    url = play_video()
    return tools.create_loopback(url)


# Initiate Startup
if __name__ == "__main__":
    plugin.run(True)
