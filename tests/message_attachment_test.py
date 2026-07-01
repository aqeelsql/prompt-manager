"""Tests for attachment metadata stored inside existing message content."""

from unittest import TestCase

from prompt_service.models.chat_model import (
    decode_message_content,
    encode_message_content,
)


class MessageAttachmentTest(TestCase):
    def test_attachment_round_trip_keeps_visible_prompt_clean(self):
        attachment = {
            "id": "59643813-f34e-414a-b18d-af71579ec530",
            "filename": "Attention is all you need.pdf",
            "file_type": "pdf",
            "character_count": 39625,
        }

        stored = encode_message_content(
            "Explain the attention mechanism.", attachment
        )
        content, attachments = decode_message_content(stored)

        self.assertEqual(content, "Explain the attention mechanism.")
        self.assertEqual(attachments, [attachment])

    def test_regular_message_is_unchanged(self):
        content, attachments = decode_message_content("Hello")

        self.assertEqual(content, "Hello")
        self.assertEqual(attachments, [])