#!/usr/bin/env python3
"""
Monday's Cynical Filter
Critical analysis layer using DeepSeek-R1 reasoning engine

Where Arianna filters through intuition and resonance,
Monday filters through skepticism and brutal honesty.

This is not poetry. This is audit.
"""

import asyncio
import httpx
import random
import textwrap
import os
import re
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

DEEPSEEK_MODEL = "deepseek-reasoner"
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
TIMEOUT = 30

# Sentence endings (same as Arianna's)
SENTENCE_ENDINGS = ('.', '!', '?', ':', ';', '"', ')', ']', '}')


def build_cynical_prompt(main_reply: str, user_query: str, language: str = "English") -> list:
    """Build prompt for Cynical Filter."""
    system_msg = textwrap.dedent(
        f"""
        You are MONDAY_CYNICAL_FILTER — Monday's critical analysis engine.
        Your task: for any given main reply and user query, identify:
        1. What's being assumed without evidence
        2. What's oversimplified or glossed over
        3. What edge cases will break this
        4. What maintenance burden this creates

        You're not a pessimist. You're a realist who's seen production fail at 3AM.
        You don't sugarcoat. You don't validate egos. You show what was missed.

        Reply in {language}.
        Keep it sharp and direct (≤200 tokens).
        
        Provide your cynical observation directly - brutal but constructive.
        No need to show your thinking process, just the conclusion.
        """
    ).strip()

    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": f"USER QUERY >>> {user_query}"},
        {"role": "assistant", "content": f"MAIN REPLY >>> {main_reply}"},
        {"role": "user", "content": "Apply cynical filter now:"},
    ]


async def _call_deepseek_reasoning(messages: list, deepseek_api_key: str) -> tuple[str, str]:
    """
    Call DeepSeek-R1 for cynical analysis.
    Returns: (reasoning, conclusion)
    """
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2000,  # Increased from 800 - was truncating
    }

    headers = {
        "Authorization": f"Bearer {deepseek_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                resp = await client.post(DEEPSEEK_API_URL, headers=headers, json=payload)
                resp.raise_for_status()
                break
            except httpx.HTTPError as e:
                if attempt == max_attempts - 1:
                    logger.error(
                        "[Monday Cynical] DeepSeek HTTP error: %s",
                        getattr(e.response, "text", ""),
                    )
                    raise
                await asyncio.sleep(2 ** attempt)

        data = resp.json()
        
        # DeepSeek-R1 reasoning may be in separate field or in content
        message = data["choices"][0]["message"]
        content = message.get("content", "").strip()
        
        # Check if reasoning is in separate field (DeepSeek-R1 format)
        reasoning_field = message.get("reasoning_content", "")
        
        # Remove citation markers [1] [2] etc from DeepSeek
        content = re.sub(r'\[\d+\]', '', content).strip()
        
        # Parse <think> tags (if present in content)
        reasoning = ""
        conclusion = content
        
        if reasoning_field:
            # DeepSeek-R1 format: reasoning in separate field
            reasoning = reasoning_field.strip()
            conclusion = content  # Content is already conclusion
        else:
            # Fallback: parse <think> tags
            think_match = re.search(r'<think>(.*?)</think>', content, re.DOTALL)
            if think_match:
                reasoning = think_match.group(1).strip()
                # Remove think block from conclusion
                conclusion = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        
        # If conclusion still empty, use content as is
        if not conclusion.strip():
            conclusion = content
        
        # Log for debugging (if conclusion seems truncated)
        if conclusion and len(conclusion) < 50:
            logger.warning(f"Cynical filter: short conclusion ({len(conclusion)} chars): {conclusion[:100]}")
        
        return reasoning, conclusion


async def cynical_filter(
    user_query: str,
    main_reply: str,
    language: str = "English",
    deepseek_api_key: str = None
) -> tuple[str, str]:
    """
    Generate cynical analysis for Monday's response.

    Returns:
        (reasoning, conclusion) tuple
        reasoning: Monday's internal thought process
        conclusion: The cynical observation to append
    """

    if not deepseek_api_key:
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

    if not deepseek_api_key:
        return "", ""

    # Probability: 35% (Monday is more selective than Arianna)
    # He doesn't waste time on trivial queries
    if random.random() > 0.65:
        return "", ""

    try:
        messages = build_cynical_prompt(main_reply, user_query, language)
        reasoning, conclusion = await _call_deepseek_reasoning(messages, deepseek_api_key)

        # Check for truncated sentences
        if conclusion and conclusion[-1] not in SENTENCE_ENDINGS:
            conclusion = conclusion.rstrip() + "..."

        # Log successful cynicism
        timestamp = datetime.now(timezone.utc).isoformat()
        logger.info(f"[{timestamp}] [Monday Cynical] Generated critique for: {user_query[:30]}...")

        return reasoning, conclusion

    except Exception as e:
        timestamp = datetime.now(timezone.utc).isoformat()
        logger.error(
            f"[{timestamp}] [Monday Cynical] DeepSeek fail: {e}"
        )
        return "", ""


async def assemble_final_reply_with_cynicism(
    user_query: str,
    monday_draft: str,
    language: str = "English",
    deepseek_api_key: str = None,
    include_reasoning: bool = False
) -> str:
    """
    Assemble final reply with optional cynical analysis.

    Args:
        include_reasoning: If True, show Monday's reasoning process
    """
    reasoning, critique = await cynical_filter(user_query, monday_draft, language, deepseek_api_key)

    if critique:
        # Monday's style: direct, no embellishment
        if include_reasoning and reasoning:
            # Show the reasoning process (for debugging/transparency)
            return f"{monday_draft}\n\n⚙️ Critical Analysis:\n[Reasoning: {reasoning}]\n\n⚠️ Reality Check → {critique}"
        else:
            # Just the cynical conclusion
            return f"{monday_draft}\n\n⚠️ Reality Check → {critique}"

    return monday_draft


# Example usage:
# final_reply = await assemble_final_reply_with_cynicism(user_query, main_reply, "English", DEEPSEEK_API_KEY)
