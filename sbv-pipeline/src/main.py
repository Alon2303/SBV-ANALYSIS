"""Main CLI entry point for SBV Pipeline."""
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import click

from .config import settings
from .input import parse_company_file
from .orchestrator import JobManager
from .storage import init_db


# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """SBV Company Analysis Pipeline."""
    pass


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output-dir', type=click.Path(), default=None,
              help='Output directory for results (default: data/output)')
def analyze(input_file: str, output_dir: Optional[str]):
    """
    Analyze companies from input file.
    
    INPUT_FILE: CSV or TXT file with company names
    """
    logger.info(f"SBV Pipeline - Analyzing companies from {input_file}")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Parse input file
    try:
        companies = parse_company_file(input_file)
        logger.info(f"Loaded {len(companies)} companies")
    except Exception as e:
        logger.error(f"Error parsing input file: {e}")
        sys.exit(1)
    
    if not companies:
        logger.error("No companies found in input file")
        sys.exit(1)
    
    # Create and process job
    manager = JobManager()
    job = manager.create_job(companies)
    
    logger.info(f"Created job {job.job_id}")
    logger.info(f"Processing {len(companies)} companies with max {settings.max_concurrent_analyses} concurrent")
    
    # Run analysis
    try:
        asyncio.run(manager.process_job(job.job_id))
    except Exception as e:
        logger.error(f"Error processing job: {e}", exc_info=True)
        sys.exit(1)
    
    # Report results
    progress = job.progress
    logger.info("=" * 60)
    logger.info("ANALYSIS COMPLETE")
    logger.info(f"Total: {progress['total']}")
    logger.info(f"Completed: {progress['completed']}")
    logger.info(f"Failed: {progress['failed']}")
    logger.info(f"Success rate: {progress['percent']:.1f}%")
    logger.info("=" * 60)
    
    # Show output location
    logger.info(f"Results saved to: {settings.output_dir}")
    logger.info(f"Database: {settings.database_url}")
    
    if progress['failed'] > 0:
        logger.warning(f"{progress['failed']} companies failed analysis")
        for task in job.companies:
            if task.error:
                logger.warning(f"  {task.company_name}: {task.error}")


@cli.command()
def init():
    """Initialize database."""
    logger.info("Initializing database...")
    init_db()
    logger.info(f"Database initialized: {settings.database_url}")


@cli.command()
def dashboard():
    """Launch Streamlit dashboard."""
    import subprocess
    dashboard_path = Path(__file__).parent / "dashboard" / "app.py"
    subprocess.run(["streamlit", "run", str(dashboard_path)])


if __name__ == "__main__":
    cli()

