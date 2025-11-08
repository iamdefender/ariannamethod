#!/usr/bin/env python3
"""
Job Queue for Mac Daemon
Async task queue with state management
Inspired by jborkowski/claude-agent-daemon
"""

import asyncio
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, asdict

# Job states
class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Job:
    """Job in the queue"""
    job_id: str
    job_type: str  # 'think', 'sync', 'monitor', 'git_commit'
    payload: Dict
    status: JobStatus = JobStatus.PENDING
    created_at: str = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

class JobQueue:
    """Async job queue with SQLite persistence"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(exist_ok=True, parents=True)
        self._init_db()
        self.active_jobs: Dict[str, Job] = {}
    
    def _init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                job_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                result TEXT,
                error TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    async def enqueue(self, job: Job) -> None:
        """Add job to queue"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO jobs 
            (job_id, job_type, payload, status, created_at, started_at, completed_at, result, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job.job_id,
            job.job_type,
            json.dumps(job.payload),
            job.status.value,
            job.created_at,
            job.started_at,
            job.completed_at,
            json.dumps(job.result) if job.result else None,
            job.error
        ))
        conn.commit()
        conn.close()
        
        self.active_jobs[job.job_id] = job
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        job = Job(
            job_id=row[0],
            job_type=row[1],
            payload=json.loads(row[2]),
            status=JobStatus(row[3]),
            created_at=row[4],
            started_at=row[5],
            completed_at=row[6],
            result=json.loads(row[7]) if row[7] else None,
            error=row[8]
        )
        return job
    
    async def update_status(self, job_id: str, status: JobStatus, **kwargs) -> None:
        """Update job status"""
        job = self.active_jobs.get(job_id)
        if not job:
            return
        
        job.status = status
        
        if 'result' in kwargs:
            job.result = kwargs['result']
        if 'error' in kwargs:
            job.error = kwargs['error']
        
        if status == JobStatus.RUNNING and not job.started_at:
            job.started_at = datetime.now().isoformat()
        
        if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            job.completed_at = datetime.now().isoformat()
            # Remove from active
            self.active_jobs.pop(job_id, None)
        
        # Update DB
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE jobs 
            SET status = ?, started_at = ?, completed_at = ?, result = ?, error = ?
            WHERE job_id = ?
        """, (
            status.value,
            job.started_at,
            job.completed_at,
            json.dumps(job.result) if job.result else None,
            job.error,
            job_id
        ))
        conn.commit()
        conn.close()
    
    async def get_pending_jobs(self) -> List[Job]:
        """Get all pending jobs"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE status = ? ORDER BY created_at ASC", (JobStatus.PENDING.value,))
        rows = cursor.fetchall()
        conn.close()
        
        jobs = []
        for row in rows:
            job = Job(
                job_id=row[0],
                job_type=row[1],
                payload=json.loads(row[2]),
                status=JobStatus(row[3]),
                created_at=row[4],
                started_at=row[5],
                completed_at=row[6],
                result=json.loads(row[7]) if row[7] else None,
                error=row[8]
            )
            jobs.append(job)
        
        return jobs
    
    async def cleanup_old_jobs(self, days: int = 7) -> int:
        """Remove completed jobs older than N days"""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        cutoff_iso = datetime.fromtimestamp(cutoff).isoformat()
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM jobs 
            WHERE status IN (?, ?, ?) 
            AND completed_at < ?
        """, (
            JobStatus.COMPLETED.value,
            JobStatus.FAILED.value,
            JobStatus.CANCELLED.value,
            cutoff_iso
        ))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted

