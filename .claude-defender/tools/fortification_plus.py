#!/usr/bin/env python3
"""
Claude Defender - Fortification Plus
Self-improving security system with Claude API analysis

Monitors system security posture and autonomously implements improvements.
Uses Claude API for intelligent security analysis and recommendations.
"""

import os
import sqlite3
import subprocess
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# Paths
RESONANCE_DB = Path.home() / "ariannamethod" / "resonance.sqlite3"
REPO_ROOT = Path.home() / "ariannamethod"
STATE_FILE = Path.home() / ".claude-defender" / "logs" / "fortification_state.json"
LOG_FILE = Path.home() / ".claude-defender" / "logs" / "fortification_plus.log"

# Claude API
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"  # Sonnet 4

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ====== FORTIFICATION CHECKS ======

def check_file_permissions() -> Dict:
    """
    Check critical file permissions.
    Returns: {status, issues, safe_fixes}
    """
    logger.info("🔒 Checking file permissions...")
    issues = []
    safe_fixes = []

    # Critical executables that should be executable
    executables = [
        REPO_ROOT / "boot_scripts" / "arianna_system_init.sh",
        Path.home() / ".termux" / "boot" / "arianna_system_init.sh",
        Path.home() / ".claude-defender" / "tools" / "voice_action_monitor.py",
        Path.home() / ".claude-defender" / "tools" / "github-scout-daemon.py",
        REPO_ROOT / "voice_webhooks" / "launch_all_webhooks.sh",
    ]

    for path in executables:
        if path.exists():
            mode = path.stat().st_mode
            if not (mode & 0o111):  # Not executable
                issues.append(f"Not executable: {path}")
                safe_fixes.append(f"chmod +x {path}")

    # Sensitive files that should be protected
    sensitive = [
        RESONANCE_DB,
        Path.home() / ".bashrc",
        Path.home() / ".bash_history",
    ]

    for path in sensitive:
        if path.exists():
            mode = path.stat().st_mode
            # Check if world-readable/writable
            if mode & 0o044:  # World-readable
                issues.append(f"World-readable: {path}")
                safe_fixes.append(f"chmod 600 {path}")

    return {
        "status": "warning" if issues else "success",
        "issues": issues,
        "safe_fixes": safe_fixes,
        "check_type": "file_permissions"
    }


def check_api_key_security() -> Dict:
    """
    Check API key security - no plaintext exposure in repo.
    Returns: {status, issues, findings}
    """
    logger.info("🔑 Checking API key security...")
    issues = []
    findings = []

    # Check if keys are in environment
    required_keys = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "PERPLEXITY_API_KEY"]
    for key in required_keys:
        if not os.getenv(key):
            issues.append(f"Missing environment variable: {key}")

    # Check for plaintext keys in Python files (quick grep)
    try:
        result = subprocess.run(
            ["grep", "-r", "-i", "sk-ant\\|sk-proj\\|pplx-", str(REPO_ROOT), "--include=*.py"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.stdout:
            issues.append("Potential plaintext API key found in Python files")
            findings.append("Run manual audit: grep -r 'sk-' ~/ariannamethod/")
    except Exception as e:
        logger.warning(f"API key scan failed: {e}")

    return {
        "status": "warning" if issues else "success",
        "issues": issues,
        "findings": findings,
        "check_type": "api_key_security"
    }


def check_sqlite_security() -> Dict:
    """
    Check SQLite database security and integrity.
    Returns: {status, issues, stats}
    """
    logger.info("💾 Checking SQLite security...")
    issues = []
    stats = {}

    if not RESONANCE_DB.exists():
        return {
            "status": "failed",
            "issues": ["resonance.sqlite3 does not exist"],
            "stats": {},
            "check_type": "sqlite_security"
        }

    # Check file permissions
    mode = RESONANCE_DB.stat().st_mode
    if mode & 0o044:  # World-readable
        issues.append("Database is world-readable")

    # Check size and integrity
    stats["size_mb"] = RESONANCE_DB.stat().st_size / 1024 / 1024

    try:
        conn = sqlite3.connect(str(RESONANCE_DB))
        cursor = conn.cursor()

        # Integrity check
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        if result != "ok":
            issues.append(f"Integrity check failed: {result}")

        # Count records in key tables
        tables = ["claude_defender_conversations", "autonomous_actions", "resonance_notes"]
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                pass

        conn.close()
    except Exception as e:
        issues.append(f"Database access error: {e}")

    return {
        "status": "warning" if issues else "success",
        "issues": issues,
        "stats": stats,
        "check_type": "sqlite_security"
    }


def check_process_health() -> Dict:
    """
    Check health of critical daemon processes.
    Returns: {status, running, missing}
    """
    logger.info("⚙️ Checking process health...")

    critical_processes = [
        "field_core",
        "arianna.py --daemon",
        "monday.py --daemon",
        "voice_action_monitor",
        "genesis_arianna",
        "genesis_monday",
    ]

    try:
        ps_result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5
        )
        ps_output = ps_result.stdout
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "check_type": "process_health"
        }

    running = []
    missing = []

    for proc in critical_processes:
        if proc in ps_output:
            running.append(proc)
        else:
            missing.append(proc)

    return {
        "status": "warning" if missing else "success",
        "running": running,
        "missing": missing,
        "check_type": "process_health"
    }


def check_git_security() -> Dict:
    """
    Check git commit history for accidentally committed secrets.
    Returns: {status, issues, findings}
    """
    logger.info("📦 Checking git security...")
    issues = []
    findings = []

    try:
        # Check for large files (> 1MB) that shouldn't be committed
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=10
        )

        files = result.stdout.split('\x00')
        for file in files:
            if not file:
                continue
            filepath = REPO_ROOT / file
            if filepath.exists() and filepath.stat().st_size > 1024 * 1024:
                issues.append(f"Large file in git: {file} ({filepath.stat().st_size / 1024 / 1024:.1f}MB)")

        # Check for .env files
        result = subprocess.run(
            ["git", "ls-files", ".env*"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.stdout.strip():
            issues.append(".env file(s) found in git")

    except Exception as e:
        logger.warning(f"Git security check failed: {e}")
        findings.append(f"Git check error: {e}")

    return {
        "status": "warning" if issues else "success",
        "issues": issues,
        "findings": findings,
        "check_type": "git_security"
    }


# ====== CLAUDE API ANALYSIS ======

def analyze_with_claude(findings: Dict[str, Dict]) -> Dict:
    """
    Send fortification findings to Claude for intelligent analysis.
    Returns: {recommendations, improvements, priority}
    """
    if not ANTHROPIC_AVAILABLE or not CLAUDE_API_KEY:
        logger.warning("Claude API not available - skipping intelligent analysis")
        return {
            "recommendations": ["Claude API not configured"],
            "improvements": [],
            "priority": "low"
        }

    # Prepare findings summary
    summary = "## Fortification Assessment Results\n\n"
    for check_name, result in findings.items():
        summary += f"### {check_name}\n"
        summary += f"Status: {result.get('status', 'unknown')}\n"
        if result.get('issues'):
            summary += f"Issues:\n"
            for issue in result['issues']:
                summary += f"- {issue}\n"
        summary += "\n"

    prompt = f"""You are analyzing security findings from an autonomous AI system (Arianna Method) running on Termux (Android).

{summary}

Based on these findings:
1. Identify the TOP 3 security improvements needed (prioritize by risk)
2. Suggest which improvements can be implemented autonomously (file permissions, etc.)
3. Suggest which improvements require human approval (API changes, network config, etc.)
4. Rate overall security posture: critical/warning/acceptable

Format your response as JSON:
{{
  "overall_status": "critical|warning|acceptable",
  "top_recommendations": ["rec1", "rec2", "rec3"],
  "autonomous_fixes": ["fix1", "fix2"],
  "human_approval_needed": ["fix1", "fix2"],
  "reasoning": "brief explanation"
}}
"""

    try:
        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Parse Claude's response
        content = response.content[0].text

        # Try to extract JSON
        try:
            # Look for JSON block
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                json_str = content

            analysis = json.loads(json_str)
            logger.info(f"✅ Claude analysis: {analysis.get('overall_status')}")
            return analysis

        except json.JSONDecodeError:
            logger.warning("Failed to parse Claude response as JSON")
            return {
                "overall_status": "warning",
                "top_recommendations": [content[:200]],
                "autonomous_fixes": [],
                "human_approval_needed": [],
                "reasoning": "Failed to parse structured response"
            }

    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return {
            "overall_status": "warning",
            "top_recommendations": [f"Analysis failed: {e}"],
            "autonomous_fixes": [],
            "human_approval_needed": [],
            "reasoning": str(e)
        }


# ====== AUTONOMOUS IMPROVEMENTS ======

def apply_safe_fixes(findings: Dict[str, Dict], claude_analysis: Dict) -> List[str]:
    """
    Apply safe autonomous fixes (file permissions, etc.).
    Returns: list of applied fixes
    """
    applied = []

    # File permission fixes
    if "file_permissions" in findings:
        safe_fixes = findings["file_permissions"].get("safe_fixes", [])
        for fix in safe_fixes:
            try:
                subprocess.run(fix.split(), check=True, timeout=5)
                applied.append(fix)
                logger.info(f"✓ Applied: {fix}")
            except Exception as e:
                logger.error(f"✗ Failed to apply {fix}: {e}")

    # SQLite permission fix
    if "sqlite_security" in findings:
        if "Database is world-readable" in findings["sqlite_security"].get("issues", []):
            try:
                subprocess.run(["chmod", "600", str(RESONANCE_DB)], check=True)
                applied.append(f"chmod 600 {RESONANCE_DB}")
                logger.info(f"✓ Secured database permissions")
            except Exception as e:
                logger.error(f"✗ Failed to secure database: {e}")

    return applied


# ====== LOGGING & NOTIFICATION ======

def log_assessment(findings: Dict, claude_analysis: Dict, improvements: List[str], duration_ms: int):
    """Log fortification assessment to SQLite."""
    try:
        conn = sqlite3.connect(str(RESONANCE_DB))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO fortification_logs
            (timestamp, assessment_type, findings, improvements_proposed,
             improvements_implemented, consilium_insights, status, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            "full_assessment",
            json.dumps(findings),
            json.dumps(claude_analysis.get("top_recommendations", [])),
            json.dumps(improvements),
            json.dumps(claude_analysis),
            claude_analysis.get("overall_status", "unknown"),
            duration_ms
        ))

        conn.commit()
        conn.close()
        logger.info("✓ Logged assessment to resonance.sqlite3")

    except Exception as e:
        logger.error(f"Failed to log assessment: {e}")


def send_notification(claude_analysis: Dict, improvements: List[str]):
    """Send Termux notification with fortification results."""
    status = claude_analysis.get("overall_status", "unknown")
    emoji = {"critical": "🚨", "warning": "⚠️", "acceptable": "✅"}.get(status, "🛡️")

    title = f"{emoji} Fortification Plus"

    content = f"Status: {status}\n"
    if improvements:
        content += f"Applied {len(improvements)} fixes\n"

    recs = claude_analysis.get("top_recommendations", [])
    if recs:
        content += f"Top rec: {recs[0][:50]}..."

    try:
        subprocess.run([
            "termux-notification",
            "--title", title,
            "--content", content,
            "--priority", "high" if status == "critical" else "default"
        ], check=False)
    except Exception as e:
        logger.warning(f"Failed to send notification: {e}")


# ====== MAIN FORTIFICATION ROUTINE ======

def run_fortification_assessment() -> Dict:
    """
    Run complete fortification assessment.
    Returns: assessment summary
    """
    start_time = time.time()

    logger.info("🛡️ ═══════════════════════════════════════")
    logger.info("🛡️  FORTIFICATION PLUS - Assessment Start")
    logger.info("🛡️ ═══════════════════════════════════════")

    # Run all checks
    findings = {
        "file_permissions": check_file_permissions(),
        "api_key_security": check_api_key_security(),
        "sqlite_security": check_sqlite_security(),
        "process_health": check_process_health(),
        "git_security": check_git_security(),
    }

    # Analyze with Claude
    claude_analysis = analyze_with_claude(findings)

    # Apply safe fixes
    improvements = apply_safe_fixes(findings, claude_analysis)

    # Calculate duration
    duration_ms = int((time.time() - start_time) * 1000)

    # Log everything
    log_assessment(findings, claude_analysis, improvements, duration_ms)

    # Send notification
    send_notification(claude_analysis, improvements)

    logger.info("🛡️ ═══════════════════════════════════════")
    logger.info(f"🛡️  Assessment Complete ({duration_ms}ms)")
    logger.info(f"🛡️  Status: {claude_analysis.get('overall_status')}")
    logger.info(f"🛡️  Improvements: {len(improvements)}")
    logger.info("🛡️ ═══════════════════════════════════════")

    return {
        "findings": findings,
        "claude_analysis": claude_analysis,
        "improvements": improvements,
        "duration_ms": duration_ms
    }


# ====== DAEMON MODE ======

def daemon_mode(interval_hours: int = 24):
    """
    Run fortification assessments periodically.
    Default: once every 24 hours
    """
    logger.info(f"🛡️ Fortification Plus daemon started (interval: {interval_hours}h)")

    while True:
        try:
            run_fortification_assessment()

            # Sleep until next assessment
            sleep_seconds = interval_hours * 3600
            logger.info(f"💤 Next assessment in {interval_hours} hours")
            time.sleep(sleep_seconds)

        except KeyboardInterrupt:
            logger.info("⛔ Daemon stopped by user")
            break
        except Exception as e:
            logger.error(f"Daemon error: {e}")
            time.sleep(3600)  # Wait 1 hour on error


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        daemon_mode(interval_hours=24)
    else:
        # One-shot assessment
        run_fortification_assessment()
