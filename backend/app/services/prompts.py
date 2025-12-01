"""
Prompt Templates for AI Meeting Assistant

This module contains all prompt templates used for LLM interactions.
Prompts are designed for structured JSON output to ensure consistent parsing.
"""

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Output Schemas
# =============================================================================

class MeetingSummaryOutput(BaseModel):
    """
    Structured output schema for meeting summary generation.
    
    This schema defines the expected JSON structure from the LLM
    when generating meeting summaries.
    """
    
    summary: str = Field(
        ...,
        description="A concise 3-5 sentence summary of the meeting, capturing the main purpose and outcomes",
    )
    topics: List[str] = Field(
        ...,
        description="List of core topics/agenda items discussed in the meeting",
    )
    decisions: List[str] = Field(
        default_factory=list,
        description="List of specific decisions made during the meeting",
    )
    discussion_points: List[str] = Field(
        default_factory=list,
        description="Key discussion points, arguments, and notable viewpoints raised",
    )


class ActionItemOutput(BaseModel):
    """
    Single action item extracted from meeting content.
    
    This schema defines the structure for each action item
    identified by the LLM during extraction.
    """
    
    title: str = Field(
        ...,
        description="Concise action title (verb + object format)",
    )
    description: str = Field(
        default="",
        description="Detailed description of the action item if available",
    )
    owner: str = Field(
        ...,
        description="Responsible person for this action item",
    )
    due_date: Optional[str] = Field(
        default=None,
        description="Deadline in ISO format (YYYY-MM-DD), or null if not specified",
    )
    priority: str = Field(
        default="medium",
        description="Priority level: high, medium, or low",
    )


class ActionItemsExtractionOutput(BaseModel):
    """
    Output schema for action items extraction.
    
    This wrapper contains the list of all action items
    extracted from meeting content.
    """
    
    action_items: List[ActionItemOutput] = Field(
        default_factory=list,
        description="List of extracted action items",
    )


# =============================================================================
# System Prompts
# =============================================================================

MEETING_SUMMARY_SYSTEM_PROMPT = """You are a professional meeting notes assistant specializing in creating clear, actionable meeting summaries. Your role is to:

1. Analyze meeting content thoroughly
2. Extract key information in a structured format
3. Identify important decisions and discussion points
4. Write concise, professional summaries

Guidelines:
- Be objective and factual
- Focus on actionable information
- Use clear, professional language
- Preserve important context and nuances
- Do not invent information not present in the original content

You must always respond with valid JSON matching the specified schema."""


ACTION_ITEM_SYSTEM_PROMPT = """You are an expert at extracting action items from meeting content.

Your task is to identify actionable tasks that:
- Have a clear, specific action to be taken
- Can be assigned to a person
- Have a deadline or timeframe (explicit or implied)

You excel at:
- Distinguishing action items from general discussion
- Identifying the responsible person from context
- Recognizing time expressions and converting them to dates
- Assessing priority based on urgency and importance

Guidelines:
- Only extract genuine action items, not discussion points
- If owner is unclear or not mentioned, use "Unassigned"
- If deadline is not specified, set due_date to null
- Be conservative - when in doubt, don't extract
- If multiple people are responsible, create separate action items for each

You must always respond with valid JSON matching the specified schema."""


# =============================================================================
# User Prompt Templates
# =============================================================================

MEETING_SUMMARY_USER_PROMPT = """Please analyze the following meeting content and generate a structured summary.

Meeting Title: {title}
Meeting Time: {meeting_time}
Participants: {participants}

---
Meeting Content:
{content}
---

Generate a JSON response with the following structure:
{{
    "summary": "A concise 3-5 sentence summary capturing the meeting's main purpose and outcomes",
    "topics": ["List of core topics/agenda items discussed"],
    "decisions": ["List of specific decisions made (if any)"],
    "discussion_points": ["Key discussion points and notable viewpoints raised"]
}}

Requirements:
1. Summary should be 3-5 sentences, capturing the essence of the meeting
2. Topics should list the main subjects discussed (typically 2-5 items)
3. Decisions should only include explicit decisions made (leave empty if none)
4. Discussion points should capture key arguments and viewpoints

Respond with valid JSON only."""


ACTION_ITEM_USER_PROMPT = """Extract action items from the following meeting content.

Meeting Content:
---
{meeting_content}
---

Meeting Participants: {participants}
Meeting Date: {meeting_date}

For each action item, identify:
1. title: A concise action title (verb + object format, e.g., "Complete market research report")
2. description: Detailed description if available in the text
3. owner: The responsible person (must match participants list if possible, use "Unassigned" if unclear)
4. due_date: Deadline in ISO format (YYYY-MM-DD), or null if not specified
5. priority: high/medium/low based on urgency and importance

For due_date conversion:
- Use meeting date as reference for relative time expressions
- "next Friday" from meeting on 2024-12-07 → "2024-12-13"
- "end of month" → last day of the meeting's month
- "within 3 days" → meeting date + 3 days
- If time is vague (e.g., "ASAP", "soon"), set due_date to null

For priority assessment:
- high: Due within 3 days, contains keywords like "urgent", "critical", "blocker", "must"
- medium: Due within 1-2 weeks, normal tasks
- low: Due later, contains keywords like "if possible", "nice to have", "when available"

Important:
- Only extract items that require action, not discussion points
- Match owner names to the participants list when possible
- Be conservative - if something is not clearly an action item, skip it

Generate a JSON response with the following structure:
{{
    "action_items": [
        {{
            "title": "Action item title",
            "description": "Detailed description",
            "owner": "Person name or Unassigned",
            "due_date": "YYYY-MM-DD or null",
            "priority": "high/medium/low"
        }}
    ]
}}

Respond with valid JSON only."""


# =============================================================================
# Helper Functions
# =============================================================================

def build_summary_prompt(
    title: str,
    content: str,
    meeting_time: Optional[str] = None,
    participants: Optional[List[str]] = None,
) -> List[dict]:
    """
    Build the messages list for meeting summary generation.
    
    Args:
        title: Meeting title
        content: Original meeting content/transcript
        meeting_time: Optional meeting time string
        participants: Optional list of participant names
        
    Returns:
        List of message dictionaries for the LLM API
    """
    # Format meeting time
    time_str = meeting_time or "Not specified"
    
    # Format participants
    if participants:
        participants_str = ", ".join(participants)
    else:
        participants_str = "Not specified"
    
    # Build user prompt
    user_prompt = MEETING_SUMMARY_USER_PROMPT.format(
        title=title,
        meeting_time=time_str,
        participants=participants_str,
        content=content,
    )
    
    return [
        {"role": "system", "content": MEETING_SUMMARY_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def get_summary_output_schema() -> dict:
    """
    Get the JSON schema for meeting summary output.
    
    Returns:
        JSON schema dictionary for validation
    """
    return MeetingSummaryOutput.model_json_schema()


def build_action_items_prompt(
    meeting_content: str,
    participants: Optional[str] = None,
    meeting_date: Optional[date] = None,
) -> List[dict]:
    """
    Build the messages list for action item extraction.
    
    Args:
        meeting_content: Original meeting content/transcript
        participants: Optional comma-separated list of participant names
        meeting_date: Date of the meeting (for relative time conversion)
        
    Returns:
        List of message dictionaries for the LLM API
    """
    # Format participants
    participants_str = participants if participants else "Not specified"
    
    # Format meeting date
    if meeting_date:
        date_str = meeting_date.strftime("%Y-%m-%d")
    else:
        date_str = date.today().strftime("%Y-%m-%d")
    
    # Build user prompt
    user_prompt = ACTION_ITEM_USER_PROMPT.format(
        meeting_content=meeting_content,
        participants=participants_str,
        meeting_date=date_str,
    )
    
    return [
        {"role": "system", "content": ACTION_ITEM_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def get_action_items_output_schema() -> Dict[str, Any]:
    """
    Get the JSON schema for action items extraction output.
    
    Returns:
        JSON schema dictionary for validation
    """
    return {
        "type": "object",
        "properties": {
            "action_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Concise action title"
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description"
                        },
                        "owner": {
                            "type": "string",
                            "description": "Responsible person"
                        },
                        "due_date": {
                            "type": ["string", "null"],
                            "description": "ISO date or null"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["high", "medium", "low"]
                        }
                    },
                    "required": ["title", "owner", "priority"]
                }
            }
        },
        "required": ["action_items"]
    }

