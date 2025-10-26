"""Job manager for concurrent company analysis."""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field

from ..analysis import SBVProtocol
from ..storage import get_db, AnalysisRepository
from ..config import settings

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CompanyTask:
    """Individual company analysis task."""
    company_name: str
    homepage: Optional[str] = None
    status: JobStatus = JobStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class AnalysisJob:
    """Analysis job tracking multiple companies."""
    job_id: str
    companies: List[CompanyTask]
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def progress(self) -> Dict[str, Any]:
        """Get job progress."""
        total = len(self.companies)
        completed = sum(1 for c in self.companies if c.status == JobStatus.COMPLETED)
        failed = sum(1 for c in self.companies if c.status == JobStatus.FAILED)
        processing = sum(1 for c in self.companies if c.status == JobStatus.PROCESSING)
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "processing": processing,
            "pending": total - completed - failed - processing,
            "percent": (completed / total * 100) if total > 0 else 0
        }


class JobManager:
    """Manages concurrent analysis jobs."""
    
    def __init__(self):
        self.jobs: Dict[str, AnalysisJob] = {}
        self.protocol = SBVProtocol()
    
    def create_job(
        self,
        companies: List[Dict[str, str]]
    ) -> AnalysisJob:
        """
        Create a new analysis job.
        
        Args:
            companies: List of dicts with 'company_name' and optional 'homepage'
        
        Returns:
            AnalysisJob instance
        """
        job_id = str(uuid.uuid4())
        
        tasks = [
            CompanyTask(
                company_name=c["company_name"],
                homepage=c.get("homepage")
            )
            for c in companies
        ]
        
        job = AnalysisJob(
            job_id=job_id,
            companies=tasks
        )
        
        self.jobs[job_id] = job
        logger.info(f"Created job {job_id} with {len(tasks)} companies")
        
        return job
    
    def get_job(self, job_id: str) -> Optional[AnalysisJob]:
        """Get job by ID."""
        return self.jobs.get(job_id)
    
    async def process_job(self, job_id: str) -> AnalysisJob:
        """
        Process all companies in a job concurrently.
        
        Args:
            job_id: Job ID to process
        
        Returns:
            Updated AnalysisJob
        """
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now()
        
        logger.info(f"Processing job {job_id} with {len(job.companies)} companies")
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(settings.max_concurrent_analyses)
        
        # Process all companies concurrently
        tasks = [
            self._process_company(job, task, semaphore)
            for task in job.companies
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update job status
        job.completed_at = datetime.now()
        job.status = JobStatus.COMPLETED if all(
            c.status == JobStatus.COMPLETED for c in job.companies
        ) else JobStatus.FAILED
        
        logger.info(f"Job {job_id} completed: {job.progress}")
        
        return job
    
    async def _process_company(
        self,
        job: AnalysisJob,
        task: CompanyTask,
        semaphore: asyncio.Semaphore
    ):
        """Process a single company analysis."""
        async with semaphore:
            task.status = JobStatus.PROCESSING
            task.started_at = datetime.now()
            
            try:
                logger.info(f"Analyzing {task.company_name}...")
                
                # Run SBV analysis
                result = await self.protocol.analyze_company(
                    task.company_name,
                    task.homepage
                )
                
                # Save to database
                with get_db() as db:
                    repo = AnalysisRepository(db)
                    
                    # Get or create company
                    company = repo.get_or_create_company(
                        task.company_name,
                        task.homepage
                    )
                    
                    # Create analysis record
                    analysis = repo.create_analysis(
                        company=company,
                        analysis_run_id=result["analysis_run_id"],
                        config_hash=result["config_hash"],
                        as_of_date=result["as_of_date"]
                    )
                    
                    # Update with metrics
                    update_data = {
                        "status": "completed",
                        # Constriction
                        "k": result["constriction"]["k"],
                        "S": result["constriction"]["S"],
                        "Md": result["constriction"]["Md"],
                        "Mx": result["constriction"]["Mx"],
                        "Cx": result["constriction"]["Cx"],
                        "S_norm_fix": result["constriction"]["S_norm_fix"],
                        "Md_norm_fix": result["constriction"]["Md_norm_fix"],
                        "Mx_norm_fix": result["constriction"]["Mx_norm_fix"],
                        "Cx_norm_fix": result["constriction"]["Cx_norm_fix"],
                        "CI_fix": result["constriction"]["CI_fix"],
                        "CI_mode": result["constriction"]["CI_mode"],
                        "CI_cohort": result["constriction"]["CI_cohort"],
                        # Readiness
                        "TRL_raw": result["readiness"]["TRL_raw"],
                        "IRL_raw": result["readiness"]["IRL_raw"],
                        "ORL_raw": result["readiness"]["ORL_raw"],
                        "RCL_raw": result["readiness"]["RCL_raw"],
                        "TRL_adj": result["readiness"]["TRL_adj"],
                        "IRL_adj": result["readiness"]["IRL_adj"],
                        "ORL_adj": result["readiness"]["ORL_adj"],
                        "RCL_adj": result["readiness"]["RCL_adj"],
                        "RI": result["readiness"]["RI"],
                        "EP": result["readiness"]["EP"],
                        "RI_skeptical": result["readiness"]["RI_skeptical"],
                        "RAR": result["readiness"]["RAR"],
                        # Likely & Lovely
                        "E": result["likely_lovely"]["E"],
                        "T": result["likely_lovely"]["T"],
                        "SP": result["likely_lovely"]["SP"],
                        "LS_norm": result["likely_lovely"]["LS_norm"],
                        "LV": result["likely_lovely"]["LV"],
                        "LV_norm": result["likely_lovely"]["LV_norm"],
                        "CCF": result["likely_lovely"]["CCF"],
                        # Wayback
                        "wayback_snapshot_url": result["wayback"]["snapshot_url"],
                        "wayback_snapshot_datetime": result["wayback"]["snapshot_datetime"],
                        "wayback_note": result["wayback"]["note"],
                    }
                    
                    repo.update_analysis(analysis, update_data)
                    
                    # Add bottlenecks
                    repo.add_bottlenecks(analysis, result["bottlenecks"])
                    
                    # Add citations
                    repo.add_citations(analysis, result["citations"])
                    
                    repo.mark_completed(analysis)
                    
                    # Export to JSON file
                    output_path = settings.output_dir / f"{result['analysis_run_id']}.json"
                    import json
                    with open(output_path, "w") as f:
                        json.dump(result, f, indent=2)
                    
                    logger.info(f"Saved analysis for {task.company_name} to {output_path}")
                
                task.result = result
                task.status = JobStatus.COMPLETED
                task.completed_at = datetime.now()
                
            except Exception as e:
                logger.error(f"Error analyzing {task.company_name}: {str(e)}", exc_info=True)
                task.error = str(e)
                task.status = JobStatus.FAILED
                task.completed_at = datetime.now()

