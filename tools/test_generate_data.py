import json
import unittest
from unittest.mock import patch
from collections import Counter
from pathlib import Path

import generate_data as g


class SongDataTests(unittest.TestCase):
    def test_catalog_matches_approved_tables(self):
        records = json.loads((g.ROOT / '歌单表格核对/核对资料/review_records.json').read_text(encoding='utf-8'))
        expected = Counter()
        for row in records:
            if row['kind'] == '学歌':
                continue
            style = '歌手专属' if row['section'] in g.chinese_singers | g.western_singers else row['section']
            expected[(row['title'], row['artist'], style, row['kind'])] += 1
        actual = Counter((s['title'], s['artist'], s['style'], s['language']) for s in g.build_payload()['songs'])
        self.assertEqual(expected, actual)

    def test_all_non_game_songs_have_artists(self):
        songs = g.build_payload()['songs']
        self.assertEqual(len(songs), 765)
        self.assertNotIn('二游/电子', {s['style'] for s in songs})
        self.assertEqual(sum(s['style'] == '二游' for s in songs), 16)
        self.assertTrue(all(bool(s['artist']) == (s['style'] != '二游') for s in songs))

    def test_current_queue_order_and_requesters(self):
        queue = g.build_payload()['queue']
        self.assertEqual((len(queue['learned']), len(queue['queued'])), (47, 51))
        self.assertTrue(all(i['requester'] and i['title'] for v in queue.values() for i in v))
        self.assertEqual(queue['queued'][0], {'requester': '沐沐、404', 'title': 'Bling-Bang-Bang-Born（日语）'})
        self.assertEqual(queue['queued'][-1], {'requester': '终焉', 'title': '尘外客'})
        self.assertEqual(queue['queued'][-5], {'requester': '别吃谷', 'title': 'This is living'})

    def test_queue_format_and_song_hyphens(self):
        with patch.object(g, 'blocks', return_value=['【排队中】', '粉丝—Song-With-Hyphens — Remix']):
            self.assertEqual(g.parse_queue(None)['queued'][0], {'requester': '粉丝', 'title': 'Song-With-Hyphens — Remix'})
        with patch.object(g, 'blocks', return_value=['【排队中】', '缺少分隔符']):
            with self.assertRaises(ValueError):
                g.parse_queue(None)


if __name__ == '__main__':
    unittest.main()
