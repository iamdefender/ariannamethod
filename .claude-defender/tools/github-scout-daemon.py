#!/usr/bin/env python3
"""
GitHub Scout Daemon - Autonomous Repository Discovery
Runs every 24 hours, discovers interesting repos, logs findings to resonance.sqlite3

Part of Arianna Method autonomous daemon ecosystem.
"""

import os
import sys
import time
import sqlite3
import requests
from datetime import datetime

# Paths - auto-detect repo root
from pathlib import Path
SCRIPT_DIR = Path(__file__).parent  # .claude-defender/tools/
REPO_ROOT = SCRIPT_DIR.parent.parent  # .claude-defender/../.. = repo root
RESONANCE_DB = str(REPO_ROOT / "resonance.sqlite3")
LOG_DIR = str(REPO_ROOT / "logs")

# GitHub API
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

# Scout config
SEARCH_QUERIES = [
    "transformer language:python stars:>100",
    "autonomous agent language:python stars:>50",
    "self-healing system language:python",
    "LLM orchestration language:python",
    "consciousness simulation language:python",
]

INTERVAL = 24 * 60 * 60  # 24 hours


def init_db():
    """Initialize github_scout_findings table if not exists"""
    conn = sqlite3.connect(RESONANCE_DB)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS github_scout_findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            repo_name TEXT,
            repo_url TEXT,
            description TEXT,
            stars INTEGER,
            language TEXT,
            query TEXT,
            relevance_score INTEGER
        )
    """)

    conn.commit()
    conn.close()


def search_github(query, max_results=5):
    """Search GitHub for repos matching query"""
    url = "https://api.github.com/search/repositories"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": max_results
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            return response.json().get("items", [])
        else:
            print(f"⚠️  GitHub API returned {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ GitHub API error: {e}")
        return []


def calculate_relevance(repo):
    """Calculate relevance score (0-100) based on repo characteristics"""
    score = 0

    # Stars weight (max 40 points)
    stars = repo.get("stargazers_count", 0)
    if stars > 1000:
        score += 40
    elif stars > 500:
        score += 30
    elif stars > 100:
        score += 20
    else:
        score += 10

    # Recent activity (max 20 points)
    updated = repo.get("updated_at", "")
    if "2025" in updated or "2024" in updated:
        score += 20
    elif "2023" in updated:
        score += 10

    # Description keywords (max 20 points)
    description = (repo.get("description") or "").lower()
    keywords = ["autonomous", "agent", "transformer", "llm", "consciousness", "self-healing"]
    matches = sum(1 for kw in keywords if kw in description)
    score += min(matches * 5, 20)

    # Language match (max 20 points)
    language = repo.get("language", "").lower()
    if language == "python":
        score += 20
    elif language in ["javascript", "typescript", "rust"]:
        score += 10

    return min(score, 100)


def save_finding(repo, query):
    """Save interesting repo to resonance.sqlite3"""
    conn = sqlite3.connect(RESONANCE_DB)
    c = conn.cursor()

    relevance = calculate_relevance(repo)

    c.execute("""
        INSERT INTO github_scout_findings
        (timestamp, repo_name, repo_url, description, stars, language, query, relevance_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        repo.get("full_name", ""),
        repo.get("html_url", ""),
        repo.get("description", "")[:500],  # limit length
        repo.get("stargazers_count", 0),
        repo.get("language", ""),
        query,
        relevance
    ))

    conn.commit()
    conn.close()


def scout_run():
    """Single scout run - search all queries and log findings"""
    print(f"\n🔍 GitHub Scout Run - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    total_found = 0
    high_relevance = 0

    for query in SEARCH_QUERIES:
        print(f"\n📊 Query: {query}")
        repos = search_github(query, max_results=5)

        if not repos:
            print("   No results")
            continue

        for repo in repos:
            relevance = calculate_relevance(repo)
            name = repo.get("full_name", "unknown")
            stars = repo.get("stargazers_count", 0)

            # Only save if relevance > 50
            if relevance >= 50:
                save_finding(repo, query)
                print(f"   ✅ {name} (⭐{stars}) - relevance: {relevance}/100")
                total_found += 1
                if relevance >= 70:
                    high_relevance += 1
            else:
                print(f"   ⏭️  {name} (⭐{stars}) - relevance too low: {relevance}/100")

        # Rate limiting courtesy
        time.sleep(2)

    print(f"\n📈 Summary: {total_found} repos found ({high_relevance} high-relevance)")
    print("=" * 60)


def daemon_mode():
    """Run scout every 24 hours"""
    print("🛡️ GitHub Scout Daemon STARTED")
    print(f"   Interval: {INTERVAL/3600:.0f} hours")
    print(f"   DB: {RESONANCE_DB}")
    print(f"   Queries: {len(SEARCH_QUERIES)}")

    init_db()

    while True:
        try:
            scout_run()
            print(f"\n⏰ Next run in {INTERVAL/3600:.0f} hours...")
            time.sleep(INTERVAL)
        except KeyboardInterrupt:
            print("\n🛑 GitHub Scout Daemon STOPPED (user interrupt)")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error in scout run: {e}")
            print(f"   Retrying in 1 hour...")
            time.sleep(3600)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Single run mode
        init_db()
        scout_run()
    else:
        # Daemon mode
        daemon_mode()


if __name__ == "__main__":
    main()
