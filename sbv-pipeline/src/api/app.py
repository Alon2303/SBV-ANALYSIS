"""FastAPI application."""
import asyncio
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import settings
from ..storage import init_db, get_db_session, AnalysisRepository, Analysis
from ..orchestrator import JobManager


# Initialize database on startup
init_db()

# Create FastAPI app
app = FastAPI(
    title="SBV Analysis Pipeline API",
    description="API for Strategic Bottleneck Validation company analysis",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Job manager instance
job_manager = JobManager()


# Pydantic models
class CompanyInput(BaseModel):
    """Company input model."""
    company_name: str
    homepage: Optional[str] = None


class AnalyzeRequest(BaseModel):
    """Analysis request model."""
    companies: List[CompanyInput]


class JobResponse(BaseModel):
    """Job response model."""
    job_id: str
    status: str
    total: int
    completed: int
    failed: int
    processing: int
    pending: int
    percent: float


class AnalysisResponse(BaseModel):
    """Analysis response model."""
    id: int
    company_name: str
    homepage: Optional[str]
    analysis_run_id: str
    as_of_date: str
    CI_fix: float
    RI: float
    RI_skeptical: float
    CCF: float
    RAR: float
    status: str


def get_db():
    """FastAPI database dependency."""
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "SBV Analysis Pipeline API",
        "version": "1.0.0",
        "status": "running"
    }


@app.post("/api/analyze", response_model=JobResponse)
async def analyze_companies(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks
):
    """
    Submit companies for analysis.
    
    Returns job ID for tracking progress.
    """
    if not request.companies:
        raise HTTPException(status_code=400, detail="No companies provided")
    
    # Create job
    companies_data = [c.dict() for c in request.companies]
    job = job_manager.create_job(companies_data)
    
    # Process in background
    background_tasks.add_task(job_manager.process_job, job.job_id)
    
    progress = job.progress
    return JobResponse(
        job_id=job.job_id,
        status=job.status,
        **progress
    )


@app.get("/api/status/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """Get job status and progress."""
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    progress = job.progress
    return JobResponse(
        job_id=job.job_id,
        status=job.status,
        **progress
    )


@app.get("/api/companies", response_model=List[AnalysisResponse])
async def list_companies(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List all analyzed companies."""
    repo = AnalysisRepository(db)
    analyses = repo.list_analyses(limit=limit, offset=offset)
    
    return [
        AnalysisResponse(
            id=a.id,
            company_name=a.company.name,
            homepage=a.company.homepage,
            analysis_run_id=a.analysis_run_id,
            as_of_date=a.as_of_date,
            CI_fix=a.CI_fix or 0.0,
            RI=a.RI or 0.0,
            RI_skeptical=a.RI_skeptical or 0.0,
            CCF=a.CCF or 0.0,
            RAR=a.RAR or 0.0,
            status=a.status
        )
        for a in analyses
    ]


@app.get("/api/companies/{analysis_id}")
async def get_company_analysis(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """Get full analysis for a company."""
    repo = AnalysisRepository(db)
    analysis = repo.get_analysis(analysis_id)
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return repo.export_to_json(analysis)


@app.get("/api/companies/{analysis_id}/metrics")
async def get_company_metrics(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """Get specific metrics for a company."""
    repo = AnalysisRepository(db)
    analysis = repo.get_analysis(analysis_id)
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return {
        "company": analysis.company.name,
        "constriction": {
            "CI_fix": analysis.CI_fix,
            "k": analysis.k,
            "S": analysis.S,
            "Md": analysis.Md,
            "Mx": analysis.Mx
        },
        "readiness": {
            "RI": analysis.RI,
            "RI_skeptical": analysis.RI_skeptical,
            "EP": analysis.EP,
            "TRL": analysis.TRL_adj,
            "IRL": analysis.IRL_adj,
            "ORL": analysis.ORL_adj,
            "RCL": analysis.RCL_adj
        },
        "likely_lovely": {
            "E": analysis.E,
            "T": analysis.T,
            "SP": analysis.SP,
            "LV": analysis.LV,
            "CCF": analysis.CCF
        },
        "RAR": analysis.RAR
    }


@app.post("/api/export")
async def export_analyses(
    format: str = "csv",
    db: Session = Depends(get_db)
):
    """Export all analyses to CSV or JSON."""
    repo = AnalysisRepository(db)
    analyses = repo.list_analyses(limit=1000)
    
    if format == "json":
        return [repo.export_to_json(a) for a in analyses]
    elif format == "csv":
        # Return CSV data
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Company", "Homepage", "Date", "CI", "RI", "RI_Skeptical",
            "CCF", "RAR", "TRL", "IRL", "ORL", "RCL", "E", "T", "SP", "LV"
        ])
        
        # Rows
        for a in analyses:
            writer.writerow([
                a.company.name,
                a.company.homepage or "",
                a.as_of_date,
                f"{a.CI_fix:.3f}" if a.CI_fix else "",
                f"{a.RI:.3f}" if a.RI else "",
                f"{a.RI_skeptical:.3f}" if a.RI_skeptical else "",
                f"{a.CCF:.3f}" if a.CCF else "",
                f"{a.RAR:.3f}" if a.RAR else "",
                a.TRL_adj or "",
                a.IRL_adj or "",
                a.ORL_adj or "",
                a.RCL_adj or "",
                a.E or "",
                a.T or "",
                a.SP or "",
                a.LV or ""
            ])
        
        return {"csv": output.getvalue()}
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'json' or 'csv'")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

