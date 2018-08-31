from addondev import testing, plugin_data
import unittest

# Testing specific imports
import codequick
from addon import main as addon

# Check witch version of codequick we are running
framework_version = codequick.__dict__.get("__version__", (0, 9, 0))


class Tester(unittest.TestCase):
    def test_root(self):
        data = addon.root.test("video")
        self.assertGreaterEqual(len(data), 33)

    def test_root_no_content_type(self):
        data = addon.root.test()
        self.assertGreaterEqual(len(data), 33)

    def test_recent(self):
        data = addon.recent_videos.test()
        self.assertGreaterEqual(len(data), 50)

    def test_recent_next(self):
        data = addon.recent_videos.test("newvideos.html?&page=2")
        self.assertGreaterEqual(len(data), 50)

    def test_watching_now(self):
        data = addon.watching_now.test()
        self.assertGreaterEqual(len(data), 5)

    def test_related(self):
        data = addon.related.test("http://metalvideo.com/the-silenced/end-machine-video_b71b5fcca.html")
        self.assertEqual(len(data), 10)

    def test_video_list_cat(self):
        data = addon.video_list.test(cat="http://metalvideo.com/mobile/browse-concerts-videos-1-date.html")
        self.assertGreaterEqual(len(data), 25)

    def test_video_list_next(self):
        data = addon.video_list.test(url="browse-concerts-videos-2-date.html")
        self.assertGreaterEqual(len(data), 25)

    def test_video_list_search(self):
        data = addon.video_list.test(search_query="rock")
        self.assertGreaterEqual(len(data), 25)

    def test_top_all(self):
        with testing.mock_select_dialog(0):
            data = addon.top_videos.test()
        self.assertGreaterEqual(len(data), 50)

    def test_top_converts(self):
        with testing.mock_select_dialog(5):
            data = addon.top_videos.test()
        self.assertGreaterEqual(len(data), 50)

    def test_top_skip(self):
        with testing.mock_select_dialog(-1):
            data = addon.top_videos.test()
        self.assertEqual(len(data), 1)
        self.assertFalse(data[0])

    @unittest.skipUnless(framework_version >= (0, 9, 2), "Only work on v0.9.2 and up of codequick")
    def test_video_decode_youtube_iframe(self):
        data = addon.play_video.test(url="/megadeth/holy-wars-the-punishment-due-video_4b77ac7ad.html")
        self.assertEqual(data, "plugin://plugin.video.youtube/play/?video_id=9d4ui9q7eDM")

    @unittest.skipUnless(framework_version >= (0, 9, 2), "Only work on v0.9.2 and up of codequick")
    def test_video_decode_youtube_embed(self):
        data = addon.play_video.test(url="/rammstein/du-hast-video_126711d81.html")
        self.assertEqual(data, "plugin://plugin.video.youtube/play/?video_id=W3q8Od5qJio")

    @unittest.skipUnless(framework_version >= (0, 9, 2), "Only work on v0.9.2 and up of codequick")
    def test_video_decode_clips(self):
        data = addon.play_video.test(url="/buckcherry/crazy-bitch-video_6bf13e2a4.html")
        self.assertEqual(data, "http://metalvideo.com/videos.php?vid=6bf13e2a4")

    @unittest.skipUnless(framework_version >= (0, 9, 2), "Only work on v0.9.2 and up of codequick")
    def test_party_play(self):
        data = addon.party_play.test(url="/sanctification/storm-video_44f0b3076.html")
        self.assertEqual(data["path"], "plugin://plugin.video.youtube/play/?video_id=tUhkkYoeQK0")

        self.assertEqual(len(plugin_data["playlist"]), 2)
        self.assertEqual(plugin_data["playlist"][1].getLabel(), "_loopback_ - ")

    @unittest.skipUnless(framework_version >= (0, 9, 2), "Only work on v0.9.2 and up of codequick")
    def test_party_play_fail(self):
        data = addon.party_play.test(url="http://metalvideo.com/contact_us.html")
        self.assertIsNone(data)

    def test_party_play_error(self):
        with self.assertRaises(Exception):
            addon.party_play.test(url="http://metalvideo.ie")
