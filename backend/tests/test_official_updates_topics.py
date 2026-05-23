"""Unit tests for Official Updates topic tagging and filters."""

from __future__ import annotations

import unittest

from app.services.official_updates_topics import (
    parse_topic_filter,
    primary_topic_for_ask,
    tag_topics,
    topic_label,
)


class OfficialUpdatesTopicsTests(unittest.TestCase):
    def test_tag_f1_from_title(self) -> None:
        tags = tag_topics("USCIS guidance on OPT for F-1 students")
        self.assertIn("f1_j1", tags)

    def test_tag_defaults_to_general(self) -> None:
        tags = tag_topics("Agency website maintenance notice")
        self.assertEqual(tags, ["general"])

    def test_parse_topic_filter_all_empty(self) -> None:
        self.assertEqual(parse_topic_filter(None), [])
        self.assertEqual(parse_topic_filter("all"), [])
        self.assertEqual(parse_topic_filter(""), [])

    def test_parse_topic_filter_ignores_unknown(self) -> None:
        self.assertEqual(sorted(parse_topic_filter("h1b,not_a_topic,family")), ["family", "h1b"])

    def test_topic_label_known(self) -> None:
        self.assertEqual(topic_label("h1b"), "H-1B & work visas")

    def test_primary_topic_for_ask_prefers_user_filter(self) -> None:
        label = primary_topic_for_ask(["general", "f1_j1"], "h1b")
        self.assertEqual(label, "H-1B & work visas")

    def test_primary_topic_for_ask_from_tags(self) -> None:
        label = primary_topic_for_ask(["general", "asylum"], None)
        self.assertEqual(label, "Asylum & protection")


if __name__ == "__main__":
    unittest.main()
