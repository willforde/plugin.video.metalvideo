from addondev import initializer, testing
import os

initializer(os.path.dirname(os.path.dirname(__file__)))
import unittest
import addon


class Tester(unittest.TestCase):
    def test_root(self):
        data = addon.root.test("video")
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
        testing.mock_select_dialog(0)
        data = addon.top_videos.test()
        self.assertGreaterEqual(len(data), 50)

    def test_top_converts(self):
        testing.mock_select_dialog(5)
        data = addon.top_videos.test()
        self.assertGreaterEqual(len(data), 50)
