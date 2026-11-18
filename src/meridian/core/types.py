"""Canonical immutable message, content block, and completion types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping, Sequence


class Role(StrEnum):
    """Participant role in a multi-turn model conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class FinishReason(StrEnum):
    """Reason a model generation stopped."""

    STOP = "stop"
    TOOL_CALLS = "tool_calls"
    MAX_TOKENS = "max_tokens"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class CitationSpan:
    """Character-offset attribution linking generated text back to a source chunk."""

    chunk_id: str
    document_id: str
    start_char: int
    end_char: int
    quote: str = ""

    def __post_init__(self) -> None:
        if not self.chunk_id.strip():
            raise ValueError("chunk_id must be non-empty")
        if not self.document_id.strip():
            raise ValueError("document_id must be non-empty")
        if self.start_char < 0 or self.end_char < self.start_char:
            raise ValueError(
                f"Invalid span bounds: start_char={self.start_char}, end_char={self.end_char}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "citation",
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "quote": self.quote,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CitationSpan:
        return cls(
            chunk_id=str(data["chunk_id"]),
            document_id=str(data["document_id"]),
            start_char=int(data["start_char"]),
            end_char=int(data["end_char"]),
            quote=str(data.get("quote", "")),
        )


@dataclass(frozen=True, slots=True)
class TextBlock:
    """Plain or cited text content block."""

    text: str
    citations: tuple[CitationSpan, ...] = ()

    def __init__(self, text: str, citations: Sequence[CitationSpan] = ()) -> None:
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "citations", tuple(citations))

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "text",
            "text": self.text,
            "citations": [c.to_dict() for c in self.citations],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> TextBlock:
        raw_citations = data.get("citations", ())
        return cls(
            text=str(data["text"]),
            citations=[CitationSpan.from_dict(c) for c in raw_citations],
        )


@dataclass(frozen=True, slots=True)
class ToolCallBlock:
    """Structured tool invocation requested by an assistant turn."""

    call_id: str
    name: str
    arguments: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.call_id.strip():
            raise ValueError("call_id must be non-empty")
        if not self.name.strip():
            raise ValueError("tool name must be non-empty")
        object.__setattr__(self, "arguments", dict(self.arguments))

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "tool_call",
            "call_id": self.call_id,
            "name": self.name,
            "arguments": dict(self.arguments),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ToolCallBlock:
        args = data.get("arguments", {})
        if not isinstance(args, Mapping):
            raise TypeError("ToolCallBlock arguments must be a mapping")
        return cls(
            call_id=str(data["call_id"]),
            name=str(data["name"]),
            arguments=dict(args),
        )


@dataclass(frozen=True, slots=True)
class ToolResultBlock:
    """Result returned from executing a tool call."""

    call_id: str
    content: str
    is_error: bool = False

    def __post_init__(self) -> None:
        if not self.call_id.strip():
            raise ValueError("call_id must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "tool_result",
            "call_id": self.call_id,
            "content": self.content,
            "is_error": self.is_error,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ToolResultBlock:
        return cls(
            call_id=str(data["call_id"]),
            content=str(data["content"]),
            is_error=bool(data.get("is_error", False)),
        )


ContentBlock = TextBlock | ToolCallBlock | ToolResultBlock


def block_from_dict(data: Mapping[str, Any]) -> ContentBlock:
    """Deserialize a polymorphic ContentBlock from a dictionary."""
    block_type = data.get("type")
    if block_type == "text":
        return TextBlock.from_dict(data)
    if block_type == "tool_call":
        return ToolCallBlock.from_dict(data)
    if block_type == "tool_result":
        return ToolResultBlock.from_dict(data)
    raise ValueError(f"Unknown content block type: {block_type!r}")


@dataclass(frozen=True, slots=True)
class Message:
    """Immutable conversation message composed of ordered content blocks."""

    role: Role
    blocks: tuple[ContentBlock, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        role: Role | str,
        content: str | Sequence[ContentBlock],
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        resolved_role = role if isinstance(role, Role) else Role(role)
        if isinstance(content, str):
            resolved_blocks: tuple[ContentBlock, ...] = (TextBlock(text=content),)
        else:
            resolved_blocks = tuple(content)
        if not resolved_blocks:
            raise ValueError("Message must contain at least one content block")
        if resolved_role == Role.TOOL and not all(
            isinstance(b, ToolResultBlock) for b in resolved_blocks
        ):
            raise ValueError("TOOL messages may only contain ToolResultBlock items")

        object.__setattr__(self, "role", resolved_role)
        object.__setattr__(self, "blocks", resolved_blocks)
        object.__setattr__(self, "metadata", dict(metadata or {}))

    @property
    def text(self) -> str:
        """Concatenate all text blocks in order."""
        return "".join(b.text for b in self.blocks if isinstance(b, TextBlock))

    @property
    def tool_calls(self) -> tuple[ToolCallBlock, ...]:
        """Return all tool calls emitted in this message."""
        return tuple(b for b in self.blocks if isinstance(b, ToolCallBlock))

    @property
    def tool_results(self) -> tuple[ToolResultBlock, ...]:
        """Return all tool results carried in this message."""
        return tuple(b for b in self.blocks if isinstance(b, ToolResultBlock))

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role.value,
            "blocks": [b.to_dict() for b in self.blocks],
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Message:
        raw_blocks = data.get("blocks", ())
        return cls(
            role=Role(str(data["role"])),
            content=[block_from_dict(b) for b in raw_blocks],
            metadata=dict(data.get("metadata") or {}),
        )


@dataclass(frozen=True, slots=True)
class TokenUsage:
    """Token accounting for a single completion or aggregated run."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_prompt_tokens: int = 0

    def __post_init__(self) -> None:
        if self.prompt_tokens < 0 or self.completion_tokens < 0 or self.cached_prompt_tokens < 0:
            raise ValueError("Token counts must be non-negative")
        if self.cached_prompt_tokens > self.prompt_tokens:
            raise ValueError("cached_prompt_tokens cannot exceed prompt_tokens")

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            cached_prompt_tokens=self.cached_prompt_tokens + other.cached_prompt_tokens,
        )

    def to_dict(self) -> dict[str, int]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cached_prompt_tokens": self.cached_prompt_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass(frozen=True, slots=True)
class CompletionResponse:
    """Normalized model response returned by any Meridian provider adapter."""

    model: str
    message: Message
    finish_reason: FinishReason
    usage: TokenUsage = field(default_factory=TokenUsage)
    latency_ms: float = 0.0
    provider_request_id: str | None = None

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise ValueError("model identifier must be non-empty")
        if self.message.role != Role.ASSISTANT:
            raise ValueError("CompletionResponse message must have ASSISTANT role")
        if self.latency_ms < 0:
            raise ValueError("latency_ms must be non-negative")
