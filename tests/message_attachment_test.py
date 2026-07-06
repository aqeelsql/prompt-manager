"""Tests for attachment metadata stored inside existing message content."""

from unittest import TestCase

from prompt_service.models.chat_model import (
    decode_llm_role,
    decode_message_content,
    encode_llm_role,
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

    def test_system_prompt_role_round_trip(self):
        stored = encode_llm_role(
            "Always answer with concise Python.", "system"
        )

        content, llm_role = decode_llm_role(stored, "user")

        self.assertEqual(content, "Always answer with concise Python.")
        self.assertEqual(llm_role, "system")