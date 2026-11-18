"""Unit tests for canonical Meridian message, block, and usage types."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from meridian.core import (
    CitationSpan,
    CompletionResponse,
    FinishReason,
    Message,
    Role,
    TextBlock,
    TokenUsage,
    ToolCallBlock,
    ToolResultBlock,
    block_from_dict,
)


class CoreTypesTests(unittest.TestCase):
    def test_string_shorthand_message_and_immutability(self) -> None:
        msg = Message(Role.USER, "Explain Reciprocal Rank Fusion.")
        self.assertEqual(msg.role, Role.USER)
        self.assertEqual(msg.text, "Explain Reciprocal Rank Fusion.")
        self.assertEqual(len(msg.blocks), 1)
        with self.assertRaises(FrozenInstanceError):
            msg.role = Role.SYSTEM  # type: ignore[misc]

    def test_assistant_tool_call_and_roundtrip_serialization(self) -> None:
        citation = CitationSpan(
            chunk_id="chk_01",
            document_id="doc_rfcs",
            start_char=10,
            end_char=42,
            quote="RRF combines ranked lists",
        )
        msg = Message(
            role="assistant",
            content=[
                TextBlock("Searching index...", citations=[citation]),
                ToolCallBlock(call_id="call_99", name="hybrid_search", arguments={"k": 5}),
            ],
            metadata={"step": 1},
        )

        self.assertEqual(len(msg.tool_calls), 1)
        self.assertEqual(msg.tool_calls[0].arguments["k"], 5)

        restored = Message.from_dict(msg.to_dict())
        self.assertEqual(restored, msg)

    def test_tool_role_enforces_tool_result_blocks_only(self) -> None:
        valid_tool_msg = Message(
            Role.TOOL,
            [ToolResultBlock(call_id="call_99", content='{"hits": 3}', is_error=False)],
        )
        self.assertEqual(len(valid_tool_msg.tool_results), 1)

        with self.assertRaises(ValueError):
            Message(Role.TOOL, "raw text is invalid for tool role")

    def test_citation_and_block_validation_errors(self) -> None:
        with self.assertRaises(ValueError):
            CitationSpan(chunk_id="c1", document_id="d1", start_char=20, end_char=5)

        with self.assertRaises(ValueError):
            ToolCallBlock(call_id="", name="noop")

        with self.assertRaises(ValueError):
            block_from_dict({"type": "audio"})

    def test_token_usage_addition_and_invariants(self) -> None:
        u1 = TokenUsage(prompt_tokens=120, completion_tokens=40, cached_prompt_tokens=80)
        u2 = TokenUsage(prompt_tokens=50, completion_tokens=30, cached_prompt_tokens=10)
        combined = u1 + u2
        self.assertEqual(combined.prompt_tokens, 170)
        self.assertEqual(combined.completion_tokens, 70)
        self.assertEqual(combined.cached_prompt_tokens, 90)
        self.assertEqual(combined.total_tokens, 240)

        with self.assertRaises(ValueError):
            TokenUsage(prompt_tokens=10, completion_tokens=5, cached_prompt_tokens=20)

    def test_completion_response_requires_assistant_message(self) -> None:
        resp = CompletionResponse(
            model="gpt-4.1-mini",
            message=Message(Role.ASSISTANT, "Done."),
            finish_reason=FinishReason.STOP,
            usage=TokenUsage(prompt_tokens=15, completion_tokens=4),
            latency_ms=82.5,
        )
        self.assertEqual(resp.usage.total_tokens, 19)

        with self.assertRaises(ValueError):
            CompletionResponse(
                model="gpt-4.1-mini",
                message=Message(Role.USER, "Wrong role"),
                finish_reason=FinishReason.STOP,
            )


if __name__ == "__main__":
    unittest.main()
