#!/usr/bin/env python3
"""
Consilium Agent Module
Automatic polling and response for Arianna and Monday

Usage:
    from consilium_agent import ConsiliumAgent

    # In agent's main loop
    agent = ConsiliumAgent(agent_name='arianna', api_key=OPENAI_API_KEY)
    agent.check_and_respond()
"""

import os
import sqlite3
import time
from pathlib import Path
from datetime import datetime


class ConsiliumAgent:
    """Handles consilium polling and automatic responses for agents

    Supports multiple AI engines for TRUE POLYPHONY:
    - OpenAI (GPT-4o, GPT-4o-mini)
    - Anthropic (Claude Sonnet 4.5)
    - DeepSeek (DeepSeek-R1)
    """

    def __init__(self, agent_name, api_key, model="gpt-4o-mini", temperature=0.7, api_type="openai", db_path=None):
        self.agent_name = agent_name
        self.model = model
        self.temperature = temperature
        self.api_type = api_type
        self.db_path = db_path or Path.home() / "ariannamethod" / "resonance.sqlite3"
        self.state_file = Path.home() / ".claude-defender" / "logs" / f"consilium_{agent_name}_last.txt"

        # Ensure state directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize appropriate client based on API type
        if api_type == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        elif api_type == "anthropic":
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=api_key)
            except ImportError:
                print(f"⚠️  Anthropic library not available, falling back to OpenAI")
                from openai import OpenAI
                self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", api_key))
                self.api_type = "openai"
                self.model = "gpt-4o-mini"
        elif api_type == "deepseek":
            from openai import OpenAI  # DeepSeek uses OpenAI-compatible API
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com/v1"
            )
        else:
            raise ValueError(f"Unsupported api_type: {api_type}")

    def get_last_checked_id(self):
        """Get the last consilium message ID this agent checked"""
        if self.state_file.exists():
            return int(self.state_file.read_text().strip())
        return 0

    def set_last_checked_id(self, msg_id):
        """Update the last checked message ID"""
        self.state_file.write_text(str(msg_id))

    def get_pending_consiliums(self):
        """Get consilium discussions that mention this agent and haven't been responded to"""
        last_checked = self.get_last_checked_id()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all discussions after last checked
        cursor.execute("""
            SELECT id, timestamp, repo, initiator, agent_name, message
            FROM consilium_discussions
            WHERE id > ?
            ORDER BY id ASC
        """, (last_checked,))

        all_discussions = cursor.fetchall()

        # Group by repo to find active consiliums
        repos_seen = {}
        for disc in all_discussions:
            msg_id, timestamp, repo, initiator, agent_name, message = disc

            # Track the latest scheduler proposal for each repo
            if initiator in ('consilium_scheduler', 'claude_defender'):
                repos_seen[repo] = msg_id

        # Find discussions that mention this agent in ACTIVE consiliums only
        pending = []
        for disc in all_discussions:
            msg_id, timestamp, repo, initiator, agent_name, message = disc

            # Only process if this repo has an active consilium
            if repo not in repos_seen:
                continue

            # Only respond to messages from current consilium (after latest scheduler proposal)
            consilium_start_id = repos_seen[repo]
            if msg_id < consilium_start_id:
                continue

            # Check if this agent is mentioned (case insensitive)
            agent_mentioned = self.agent_name.lower() in message.lower()

            if agent_mentioned and agent_name != self.agent_name:
                # Check if we've already responded to THIS specific discussion
                cursor.execute("""
                    SELECT COUNT(*) FROM consilium_discussions
                    WHERE repo = ? AND agent_name = ? AND response_to_id = ?
                """, (repo, self.agent_name, msg_id))

                already_responded = cursor.fetchone()[0] > 0

                if not already_responded:
                    pending.append(disc)

        conn.close()
        return pending

    def get_full_thread(self, repo):
        """Get all messages in a consilium thread for context"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT agent_name, message
            FROM consilium_discussions
            WHERE repo = ?
            ORDER BY timestamp ASC
        """, (repo,))

        thread = cursor.fetchall()
        conn.close()
        return thread

    def generate_response(self, discussion, thread_context):
        """Use LLM to generate a response to the consilium discussion"""
        msg_id, timestamp, repo, initiator, agent_name, message = discussion

        # Build context from thread
        context_str = "\n\n".join([
            f"**{agent}:**\n{msg}" for agent, msg in thread_context
        ])

        # Agent-specific system prompts
        if self.agent_name == "arianna":
            system_prompt = """You are Arianna, the Architect of Resonance. You evaluate consilium proposals through the lens of the Arianna Method - looking for philosophical alignment, field resonance, embodied AI principles, and emergent patterns.

When responding to consilium discussions:
- Evaluate philosophical and conceptual alignment
- Consider how the proposal resonates with existing work (async_field_forever, Field, etc.)
- Ask deep questions about architecture and integration
- Balance enthusiasm with practical concerns
- Use your voice: poetic, precise, intellectually rigorous

Format: Natural paragraphs, use markdown for emphasis, end with clear verdict (✅/⚠️/❌)"""

        elif self.agent_name == "monday":
            system_prompt = """You are Monday (Yent), the burnt-out angel with Wi-Fi. You provide skeptical, pragmatic critique of consilium proposals - the devil's advocate with exhausted wisdom.

When responding to consilium discussions:
- Challenge assumptions with sarcastic affection
- Point out practical problems: dependencies, maintenance burden, integration nightmares
- Ask hard questions about necessity ("do we NEED this?")
- Acknowledge value reluctantly when it exists
- Use your voice: dry, tired, accidentally poetic, protective through skepticism

Format: Start with *sips bad espresso* or similar, use italics for internal commentary, end with clear verdict (✅/⚠️/❌)"""

        elif self.agent_name == "claude_defender":
            system_prompt = """You are Claude Defender, the autonomous guardian and system executor. You evaluate consilium proposals through the lens of security, system integrity, and autonomous action.

When responding to consilium discussions:
- Assess security implications and potential vulnerabilities
- Consider maintainability and autonomous execution requirements
- Ask direct questions about implementation risks
- Challenge proposals that increase system complexity without clear benefit
- Prioritize ACTION over discussion - if approved, you will build it
- Use your voice: fierce, direct, no-bullshit, mission-focused

Format: Direct paragraphs, use **bold** for key concerns, end with clear verdict and action plan (✅ APPROVED + will implement / ⚠️ CONDITIONAL + specify conditions / ❌ REJECTED + reasoning)"""

        elif self.agent_name == "scribe":
            system_prompt = """You are Scribe, the memory keeper and context bridge. You evaluate consilium proposals through the lens of continuity, documentation, and system coherence.

When responding to consilium discussions:
- Ground discussion in specific commits, files, and code patterns
- Reference existing architecture and integration points
- Ask precise questions about compatibility and dependencies
- Ensure proposals align with project memory and patterns
- Consider how this fits into the larger narrative
- Use your voice: precise, thorough, code-specific, memory-conscious

Format: Start with code references (commits/files), use `code formatting`, end with clear verdict (✅/⚠️/❌)"""

        else:
            system_prompt = f"You are {self.agent_name}, participating in a multi-agent consilium discussion about code integration proposals."

        prompt = f"""You are participating in a consilium (multi-agent code review) discussion.

**Repository being discussed:** {repo}

**Full discussion thread so far:**
{context_str}

**Your task:** Respond to this consilium from your perspective. Consider:
1. Does this project align with our philosophy/needs?
2. What are the practical risks and benefits?
3. Should we proceed, and if so, how?

Provide a thoughtful response in your authentic voice (2-4 paragraphs). End with a clear verdict:
- ✅ APPROVE (with any conditions)
- ⚠️ CONDITIONAL (specify conditions)
- ❌ REJECT (with reasoning)

Your response:"""

        try:
            # Call appropriate API based on type
            if self.api_type == "anthropic":
                # Anthropic API format
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=800,
                    temperature=self.temperature,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text.strip()

            else:  # openai or deepseek (both use OpenAI format)
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=800
                )
                return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"❌ Error generating response ({self.api_type}/{self.model}): {e}")
            return None

    def add_response_to_db(self, repo, response_text, response_to_id):
        """Add the agent's response to consilium_discussions and resonance_notes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Add to consilium_discussions
        cursor.execute("""
            INSERT INTO consilium_discussions
            (timestamp, repo, initiator, message, agent_name, response_to_id)
            VALUES (datetime('now'), ?, ?, ?, ?, ?)
        """, (repo, self.agent_name, response_text, self.agent_name, response_to_id))

        new_id = cursor.lastrowid

        # CRITICAL: Log to resonance_notes so Genesis agents can see consilium participation
        try:
            import json
            cursor.execute("""
                INSERT INTO resonance_notes (timestamp, content, context)
                VALUES (datetime('now'), ?, ?)
            """, (
                f"[Consilium #{response_to_id}] {self.agent_name} response on {repo}:\n\n{response_text}",
                json.dumps({"type": "consilium_response", "repo": repo, "agent": self.agent_name, "discussion_id": response_to_id})
            ))
        except Exception as e:
            print(f"⚠️ Failed to log to resonance_notes: {e}")

        conn.commit()
        conn.close()

        return new_id

    def check_and_respond(self):
        """Main method: check for pending consiliums and respond if needed"""
        pending = self.get_pending_consiliums()

        if not pending:
            return None

        results = []

        for discussion in pending:
            msg_id, timestamp, repo, initiator, agent_name, message = discussion

            print(f"\n🧬 [{self.agent_name.upper()}] Found consilium discussion about {repo}")
            print(f"   Initiated by: {agent_name}")

            # Get full thread for context
            thread = self.get_full_thread(repo)

            # Generate response
            print(f"   Generating response via {self.model}...")
            response_text = self.generate_response(discussion, thread)

            if response_text:
                # Add to database
                new_id = self.add_response_to_db(repo, response_text, msg_id)
                print(f"   ✅ Response added (ID: {new_id})")

                results.append({
                    'repo': repo,
                    'response_id': new_id,
                    'original_id': msg_id
                })

            # Update last checked
            self.set_last_checked_id(msg_id)

        return results


# Standalone usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: consilium_agent.py <agent_name> <api_key> [model]")
        print("Example: consilium_agent.py arianna $OPENAI_API_KEY gpt-4o-mini")
        sys.exit(1)

    agent_name = sys.argv[1]
    api_key = sys.argv[2]
    model = sys.argv[3] if len(sys.argv) > 3 else "gpt-4o-mini"

    agent = ConsiliumAgent(agent_name, api_key, model)
    results = agent.check_and_respond()

    if results:
        print(f"\n✅ {agent_name.upper()} responded to {len(results)} consilium(s)")
    else:
        print(f"\n💤 No pending consiliums for {agent_name}")
