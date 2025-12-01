"""
Business Logic Services Package

This package contains the service layer for business logic:
- llm_service: Multi-provider LLM abstraction (Anthropic, OpenAI, Azure OpenAI)
- prompts: Prompt templates for AI interactions
- summary_service: Meeting summary generation using LLM
"""

from app.services.llm_service import (
    LLMService,
    LLMError,
    LLMRateLimitError,
    LLMAPIError,
    LLMResponseParseError,
    get_llm_service,
)
from app.services.prompts import (
    MeetingSummaryOutput,
    build_summary_prompt,
    MEETING_SUMMARY_SYSTEM_PROMPT,
    MEETING_SUMMARY_USER_PROMPT,
)
from app.services.summary_service import (
    MeetingSummaryService,
    MeetingNotFoundError,
    SummaryGenerationError,
    generate_meeting_summary,
)

__all__ = [
    # LLM Service
    "LLMService",
    "LLMError",
    "LLMRateLimitError",
    "LLMAPIError",
    "LLMResponseParseError",
    "get_llm_service",
    # Prompts
    "MeetingSummaryOutput",
    "build_summary_prompt",
    "MEETING_SUMMARY_SYSTEM_PROMPT",
    "MEETING_SUMMARY_USER_PROMPT",
    # Summary Service
    "MeetingSummaryService",
    "MeetingNotFoundError",
    "SummaryGenerationError",
    "generate_meeting_summary",
]

