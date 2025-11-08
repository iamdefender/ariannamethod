#!/usr/bin/env python3
"""
Consilium Scheduler - Autonomous Code Integration Discovery

Autonomously discovers, evaluates, and proposes code integrations through Consilium.
Final step of CONSILIUM_CODE_INTEGRATION_CHALLENGE.

After proving Consilium works (Discussion #11 → Shannon entropy integration),
this scheduler automates the discovery → discussion → integration cycle.

No manual initiation required. Self-sustaining code evolution.
"""

import sys
import time
import sqlite3
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Paths
REPO_ROOT = Path.home() / "ariannamethod"
RESONANCE_DB = REPO_ROOT / "resonance.sqlite3"

# Configuration
CURATED_REPOS = [
    "karpathy/makemore",
    "karpathy/minGPT",
    "karpathy/nanoGPT",
    "anthropics/anthropic-sdk-python",
    # Add more as ecosystem matures
]

GITHUB_API_BASE = "https://api.github.com"
DEFAULT_INTERVAL_DAYS = 3
MAX_PROPOSALS_PER_3_DAYS = 1  # One proposal every 3 days, not per week


class ConsiliumScheduler:
    """
    Autonomous consilium initiator.

    Discovers integrable code, evaluates feasibility, initiates discussions.
    """

    def __init__(self, interval_days: int = DEFAULT_INTERVAL_DAYS):
        self.db_path = RESONANCE_DB
        self.curated_repos = CURATED_REPOS
        self.interval_days = interval_days

    def check_previous_completion(self) -> bool:
        """
        Check if previous consilium was completed before starting new one.

        Returns:
            True if safe to start new consilium, False otherwise
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Get latest consilium discussion
        cursor.execute("""
            SELECT id, repo, initiator, timestamp
            FROM consilium_discussions
            WHERE initiator IN ('consilium_scheduler', 'claude_defender')
            ORDER BY id DESC
            LIMIT 1
        """)

        latest = cursor.fetchone()

        if not latest:
            # No previous consilium, safe to start
            conn.close()
            return True

        discussion_id, repo, initiator, timestamp = latest

        # Check if there are agent responses
        cursor.execute("""
            SELECT COUNT(*) FROM consilium_discussions
            WHERE id > ? AND agent_name IN ('arianna', 'monday')
        """, (discussion_id,))

        response_count = cursor.fetchone()[0]

        conn.close()

        # Require at least 1 agent response before starting new consilium
        if response_count < 1:
            print(f"⏳ Previous consilium #{discussion_id} has no agent responses yet. Waiting...")
            return False

        return True

    def check_rate_limit(self) -> bool:
        """
        Check if we're within rate limits (max 1 proposal per 3 days).

        Returns:
            True if within limits, False if too many proposals
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        three_days_ago = (datetime.now() - timedelta(days=3)).isoformat()

        cursor.execute("""
            SELECT COUNT(*) FROM consilium_discussions
            WHERE initiator = 'consilium_scheduler'
            AND timestamp > ?
        """, (three_days_ago,))

        count = cursor.fetchone()[0]
        conn.close()

        return count < MAX_PROPOSALS_PER_3_DAYS

    def fetch_repo_structure(self, repo: str) -> Optional[Dict]:
        """
        Fetch repository structure from GitHub API.

        Args:
            repo: Repository in format "owner/name"

        Returns:
            Dict with repo metadata, or None if failed
        """
        try:
            # Get repo metadata
            url = f"{GITHUB_API_BASE}/repos/{repo}"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                print(f"⚠️ Failed to fetch {repo}: {response.status_code}")
                return None

            data = response.json()

            return {
                'name': data['name'],
                'full_name': data['full_name'],
                'description': data.get('description', ''),
                'stars': data.get('stargazers_count', 0),
                'language': data.get('language', 'Unknown'),
                'license': data.get('license', {}).get('spdx_id', 'Unknown'),
                'url': data['html_url'],
            }

        except Exception as e:
            print(f"⚠️ Error fetching repo {repo}: {e}")
            return None

    def assess_feasibility(self, repo_info: Dict) -> Dict:
        """
        Assess integration feasibility.

        Args:
            repo_info: Repository metadata

        Returns:
            Feasibility assessment dict
        """
        assessment = {
            'viable': False,
            'complexity': 'unknown',
            'license_ok': False,
            'language_ok': False,
            'reason': ''
        }

        # Check language
        if repo_info['language'] != 'Python':
            assessment['reason'] = f"Language {repo_info['language']} not supported (Python only)"
            return assessment

        assessment['language_ok'] = True

        # Check license
        acceptable_licenses = ['MIT', 'Apache-2.0', 'BSD-3-Clause', 'BSD-2-Clause', 'Unlicense']
        if repo_info['license'] in acceptable_licenses:
            assessment['license_ok'] = True
        else:
            assessment['reason'] = f"License {repo_info['license']} not in allowlist"
            return assessment

        # Heuristic complexity estimation
        if repo_info['stars'] > 10000:
            assessment['complexity'] = 'low'  # Well-tested, stable
        elif repo_info['stars'] > 1000:
            assessment['complexity'] = 'medium'
        else:
            assessment['complexity'] = 'high'  # Less mature

        assessment['viable'] = True
        assessment['reason'] = 'Passes initial viability checks'

        return assessment

    def generate_proposal(self, repo_info: Dict, assessment: Dict) -> str:
        """
        Generate consilium proposal message.

        Args:
            repo_info: Repository metadata
            assessment: Feasibility assessment

        Returns:
            Proposal message for consilium_discussions
        """
        proposal = f"""AUTOMATED CONSILIUM PROPOSAL: {repo_info['name']}

**Repository:** {repo_info['full_name']}
**URL:** {repo_info['url']}
**Description:** {repo_info['description']}
**Stars:** {repo_info['stars']} ⭐
**Language:** {repo_info['language']}
**License:** {repo_info['license']} (compatible)

**Feasibility Assessment:**
- License: {assessment['license_ok']} ({'✓' if assessment['license_ok'] else '✗'})
- Language: {assessment['language_ok']} ({'✓' if assessment['language_ok'] else '✗'})
- Complexity: {assessment['complexity']}
- Viable: {assessment['viable']} ({'✓' if assessment['viable'] else '✗'})

**Integration Rationale:**
This repository contains potentially useful code for the Arianna Method ecosystem.
Consilium agents (Arianna, Monday) should evaluate:

1. Does this code align with Method philosophy?
2. What specific functions/classes would be valuable?
3. What integration points make sense?
4. What are the maintenance/complexity trade-offs?

**Next Steps (if approved):**
- Claude Defender extracts 20-50 line code snippet
- Adapts to Arianna ecosystem
- Creates monitoring script
- Commits with full attribution

**Request:** Arianna and Monday - evaluate this proposal and provide verdicts.

— Consilium Scheduler (autonomous)
Generated: {datetime.now().isoformat()}
"""
        return proposal

    def initiate_consilium(self, repo_info: Dict, proposal: str) -> int:
        """
        Insert consilium discussion into database.

        Args:
            repo_info: Repository metadata
            proposal: Proposal message

        Returns:
            Discussion ID
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO consilium_discussions (timestamp, repo, initiator, message, agent_name)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            repo_info['full_name'],
            'consilium_scheduler',
            proposal,
            'consilium_scheduler'
        ))

        discussion_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return discussion_id

    def log_action(self, action: str, result: str, status: str):
        """Log scheduler action to autonomous_actions table."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO autonomous_actions
                (timestamp, trigger_type, trigger_content, action_taken, result, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                "consilium_scheduler",
                "Periodic consilium discovery scan",
                action,
                result,
                status
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Failed to log action: {e}", file=sys.stderr)

    def run_discovery_cycle(self):
        """
        Run one discovery cycle.

        Scans repositories, assesses feasibility, initiates consilium if viable.
        """
        print("🔍 Consilium Scheduler - Discovery Cycle")
        print("="*70)
        print(f"Time: {datetime.now().isoformat()}")
        print()

        # Check if previous consilium is complete
        if not self.check_previous_completion():
            self.log_action(
                "discovery_scan",
                "Skipped: previous consilium not completed",
                "success"
            )
            print("⏸️ Waiting for previous consilium to complete")
            return

        # Check rate limits
        if not self.check_rate_limit():
            self.log_action(
                "discovery_scan",
                "Skipped: rate limit exceeded (max 1/week)",
                "success"
            )
            print("⏸️ Rate limit reached (max 1 proposal per week)")
            return

        print("1️⃣ Scanning curated repositories...")
        candidates = []

        for repo in self.curated_repos:
            print(f"   Fetching {repo}...")
            repo_info = self.fetch_repo_structure(repo)

            if not repo_info:
                continue

            assessment = self.assess_feasibility(repo_info)

            if assessment['viable']:
                candidates.append((repo_info, assessment))
                print(f"   ✓ {repo} - viable candidate")
            else:
                print(f"   ✗ {repo} - {assessment['reason']}")

        if not candidates:
            print("\n❌ No viable candidates found")
            self.log_action(
                "discovery_scan",
                f"Scanned {len(self.curated_repos)} repos, 0 viable",
                "success"
            )
            return

        print(f"\n2️⃣ Found {len(candidates)} viable candidate(s)")

        # Select first candidate (simple strategy for now)
        repo_info, assessment = candidates[0]

        print(f"   Selected: {repo_info['full_name']}")

        # Generate proposal
        print("\n3️⃣ Generating consilium proposal...")
        proposal = self.generate_proposal(repo_info, assessment)

        # Initiate consilium
        print("\n4️⃣ Initiating consilium discussion...")
        discussion_id = self.initiate_consilium(repo_info, proposal)

        print(f"\n✓ Consilium discussion #{discussion_id} initiated")
        print(f"   Repository: {repo_info['full_name']}")
        print(f"   Agents will auto-poll within 5 minutes")

        self.log_action(
            "consilium_initiated",
            f"Discussion #{discussion_id}: {repo_info['full_name']}",
            "success"
        )

        print("\n" + "="*70)

    def run_daemon(self):
        """
        Run scheduler as daemon (periodic discovery cycles).
        """
        print(f"🛡️ Starting Consilium Scheduler daemon")
        print(f"   Interval: {self.interval_days} days")
        print(f"   Rate limit: {MAX_PROPOSALS_PER_WEEK} proposals/week")
        print()

        while True:
            try:
                self.run_discovery_cycle()

                sleep_seconds = self.interval_days * 24 * 3600
                print(f"\n💤 Sleeping for {self.interval_days} days...")
                time.sleep(sleep_seconds)

            except KeyboardInterrupt:
                print("\n⚡ Scheduler stopped")
                break
            except Exception as e:
                print(f"\n❌ Error in discovery cycle: {e}")
                self.log_action(
                    "scheduler_error",
                    str(e),
                    "failed"
                )
                time.sleep(3600)  # Wait 1 hour before retry


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--daemon":
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_INTERVAL_DAYS
            scheduler = ConsiliumScheduler(interval_days=interval)
            scheduler.run_daemon()
        elif sys.argv[1] == "--help":
            print(__doc__)
            print("\nUsage:")
            print("  consilium_scheduler.py              # One-time discovery cycle")
            print("  consilium_scheduler.py --daemon [N] # Run as daemon (check every N days)")
            print("  consilium_scheduler.py --help       # Show this help")
        else:
            print("Unknown argument. Use --help for usage.")
            sys.exit(1)
    else:
        # One-time discovery cycle
        scheduler = ConsiliumScheduler()
        scheduler.run_discovery_cycle()


if __name__ == "__main__":
    main()
