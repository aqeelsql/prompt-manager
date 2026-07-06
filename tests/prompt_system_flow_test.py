"""Tests for loading saved prompts as system context before generation."""

from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import patch
from uuid import uuid4

from prompt_service.controllers.chat_controller import (
    _chat_messages_for_llm,
    execute_prompt_controller,
)


class PromptSystemFlowTest(IsolatedAsyncioTestCase):
    async def test_loading_prompt_creates_system_only_chat(self):
        prompt_id = uuid4()
        row = object()
        prompt = {"id": prompt_id, "name": "Coder", "content": "Use Python."}
        chat = {
            "id": uuid4(),
            "messages": [
                {
                    "role": "user",
                    "llm_role": "system",
                    "content": "Use Python.",
                }
            ],
        }

        with (
            patch(
                "prompt_service.controllers.chat_controller.prompt_model.get_prompt_by_id",
                return_value=row,
            ),
            patch(
                "prompt_service.controllers.chat_controller.row_to_prompt",
                return_value=prompt,
            ),
            patch(
                "prompt_service.controllers.chat_controller.chat_model.create_chat",
                return_value=chat,
            ) as create_chat,
        ):
            result = await execute_prompt_controller(prompt_id, data=None)

        self.assertIs(result, chat)
        create_chat.assert_called_once_with(
            prompt, None, initial_llm_role="system"
        )


class LlmRoleConversionTest(TestCase):
    def test_system_prompt_is_followed_by_user_message(self):
        chat = {
            "messages": [
                {"role": "user", "llm_role": "system", "content": "Use Python."},
                {"role": "user", "llm_role": "user", "content": "Write a loop."},
            ]
        }

        messages = _chat_messages_for_llm(chat)

        self.assertEqual([message["role"] for message in messages], ["system", "user"])