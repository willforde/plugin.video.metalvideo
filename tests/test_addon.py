from addondev import testing
import unittest

# Testing specific imports
from addon import main as addon


class Tester(unittest.TestCase):
    def test_root(self):
        data = addon.root.test("video")
        self.assertGreaterEqual(len(data), 30)

    def test_root_no_content_type(self):
        data = addon.root.test()
        self.assertGreaterEqual(len(data), 30)

    def test_recent(self):
        data = addon.video_list.test("/newvideos.html")
        self.assertGreaterEqual(len(data), 20)

    def test_recent_next(self):
        data = addon.video_list.test("/newvideos.html?&page=2")
        self.assertGreaterEqual(len(data), 20)

    def test_related(self):
        data = addon.video_list.test("/the-ancient-track-blindpoint-official-video-lyric_179ccf245.html", filter_mode=1)
        self.assertEqual(len(data), 30)

    def test_video_list_cat(self):
        data = addon.video_list.test("/browse-alternative-videos-1-date.html")
        self.assertGreaterEqual(len(data), 25)

    def test_video_list_next(self):
        data = addon.video_list.test("/browse-alternative-videos-2-date.html")
        self.assertGreaterEqual(len(data), 25)

    def test_video_list_search(self):
        data = addon.search_videos.test(search_query="rock")
        self.assertGreaterEqual(len(data), 25)

    def test_top_all(self):
        with testing.mock_select_dialog(0):
            data = addon.top_videos.test()
        self.assertGreaterEqual(len(data), 30)

    def test_top_death_metal(self):
        with testing.mock_select_dialog(5):
            data = addon.top_videos.test()
        self.assertGreaterEqual(len(data), 15)

    def test_top_alternative(self):
        with testing.mock_select_dialog(2):
            data = addon.top_videos.test()
        self.assertGreaterEqual(len(data), 30)

    def test_top_skip(self):
        with testing.mock_select_dialog(-1):
            data = addon.top_videos.test()
        self.assertFalse(data)
