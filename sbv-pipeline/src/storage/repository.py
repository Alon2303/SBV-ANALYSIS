"""Repository for database operations."""
import json
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from .db_models import Company, Analysis, Bottleneck, Citation


class AnalysisRepository:
    """Repository for SBV analysis operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_or_create_company(self, name: str, homepage: Optional[str] = None) -> Company:
        """Get existing company or create new one."""
        company = self.db.query(Company).filter(Company.name == name).first()
        if not company:
            company = Company(name=name, homepage=homepage)
            self.db.add(company)
            self.db.commit()
            self.db.refresh(company)
        elif homepage and not company.homepage:
            company.homepage = homepage
            self.db.commit()
        return company
    
    def create_analysis(
        self,
        company: Company,
        analysis_run_id: str,
        config_hash: str,
        as_of_date: str
    ) -> Analysis:
        """Create a new analysis record."""
        analysis = Analysis(
            company_id=company.id,
            analysis_run_id=analysis_run_id,
            config_hash=config_hash,
            as_of_date=as_of_date,
            status="pending"
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis
    
    def update_analysis(self, analysis: Analysis, data: Dict[str, Any]) -> Analysis:
        """Update analysis with calculated metrics."""
        for key, value in data.items():
            if hasattr(analysis, key):
                setattr(analysis, key, value)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis
    
    def add_bottlenecks(self, analysis: Analysis, bottlenecks: List[Dict[str, Any]]):
        """Add bottlenecks to analysis."""
        for bn_data in bottlenecks:
            bottleneck = Bottleneck(
                analysis_id=analysis.id,
                bottleneck_id=bn_data["id"],
                type=bn_data["type"],
                location=bn_data["location"],
                severity_raw=bn_data["severity_raw"],
                severity_adj=bn_data["severity_adj"],
                verified=bn_data["verified"],
                owner=bn_data["owner"],
                timeframe=bn_data["timeframe"],
                evidence_strength=bn_data.get("evidence_strength"),
                citations_list=bn_data.get("citations", [])
            )
            self.db.add(bottleneck)
        self.db.commit()
    
    def add_citations(self, analysis: Analysis, citations: List[Dict[str, Any]]):
        """Add citations to analysis."""
        for cit_data in citations:
            citation = Citation(
                analysis_id=analysis.id,
                claim=cit_data["claim"],
                url=cit_data["url"],
                date_seen=cit_data["date_seen"]
            )
            self.db.add(citation)
        self.db.commit()
    
    def mark_completed(self, analysis: Analysis):
        """Mark analysis as completed."""
        analysis.status = "completed"
        self.db.commit()
    
    def mark_failed(self, analysis: Analysis, error: str):
        """Mark analysis as failed."""
        analysis.status = "failed"
        analysis.error_message = error
        self.db.commit()
    
    def get_analysis(self, analysis_id: int) -> Optional[Analysis]:
        """Get analysis by ID."""
        return self.db.query(Analysis).filter(Analysis.id == analysis_id).first()
    
    def get_analysis_by_run_id(self, run_id: str) -> Optional[Analysis]:
        """Get analysis by run ID."""
        return self.db.query(Analysis).filter(Analysis.analysis_run_id == run_id).first()
    
    def list_analyses(self, limit: int = 100, offset: int = 0) -> List[Analysis]:
        """List all analyses."""
        return self.db.query(Analysis).order_by(Analysis.created_at.desc()).limit(limit).offset(offset).all()
    
    def get_company_analyses(self, company_id: int) -> List[Analysis]:
        """Get all analyses for a company."""
        return self.db.query(Analysis).filter(Analysis.company_id == company_id).order_by(Analysis.created_at.desc()).all()
    
    def export_to_json(self, analysis: Analysis) -> Dict[str, Any]:
        """Export analysis to JSON format matching sbv_tiny_schema.json."""
        company = analysis.company
        
        # Build bottlenecks array
        bottlenecks = []
        for bn in analysis.bottlenecks:
            bn_dict = {
                "id": bn.bottleneck_id,
                "type": bn.type,
                "location": bn.location,
                "severity_raw": bn.severity_raw,
                "severity_adj": bn.severity_adj,
                "verified": bn.verified,
                "owner": bn.owner,
                "timeframe": bn.timeframe,
            }
            if bn.evidence_strength is not None:
                bn_dict["evidence_strength"] = bn.evidence_strength
            if bn.citations_list:
                bn_dict["citations"] = bn.citations_list
            bottlenecks.append(bn_dict)
        
        # Build citations array
        citations = [
            {
                "claim": cit.claim,
                "url": cit.url,
                "date_seen": cit.date_seen
            }
            for cit in analysis.citations
        ]
        
        # Build complete JSON
        result = {
            "company": company.name,
            "homepage": company.homepage or "",
            "as_of_date": analysis.as_of_date,
            "analysis_run_id": analysis.analysis_run_id,
            "config_hash": analysis.config_hash,
            "constriction": {
                "k": analysis.k,
                "S": analysis.S,
                "Md": analysis.Md,
                "Mx": analysis.Mx,
                "Cx": analysis.Cx,
                "S_norm_fix": analysis.S_norm_fix,
                "Md_norm_fix": analysis.Md_norm_fix,
                "Mx_norm_fix": analysis.Mx_norm_fix,
                "Cx_norm_fix": analysis.Cx_norm_fix,
                "CI_fix": analysis.CI_fix,
                "CI_mode": analysis.CI_mode,
                "CI_cohort": analysis.CI_cohort
            },
            "readiness": {
                "TRL_raw": analysis.TRL_raw,
                "IRL_raw": analysis.IRL_raw,
                "ORL_raw": analysis.ORL_raw,
                "RCL_raw": analysis.RCL_raw,
                "TRL_adj": analysis.TRL_adj,
                "IRL_adj": analysis.IRL_adj,
                "ORL_adj": analysis.ORL_adj,
                "RCL_adj": analysis.RCL_adj,
                "RI": analysis.RI,
                "EP": analysis.EP,
                "RI_skeptical": analysis.RI_skeptical,
                "RAR": analysis.RAR
            },
            "likely_lovely": {
                "E": analysis.E,
                "T": analysis.T,
                "SP": analysis.SP,
                "LS_norm": analysis.LS_norm,
                "LV": analysis.LV,
                "LV_norm": analysis.LV_norm,
                "CCF": analysis.CCF
            },
            "bottlenecks": bottlenecks,
            "citations": citations,
            "wayback": {
                "snapshot_url": analysis.wayback_snapshot_url,
                "snapshot_datetime": analysis.wayback_snapshot_datetime,
                "note": analysis.wayback_note
            }
        }
        
        # Add funding if present
        if analysis.funding_total_usd is not None:
            result["funding_since_snapshot"] = {
                "total_usd": analysis.funding_total_usd,
                "items": analysis.funding_items or []
            }
        
        return result
    
    @staticmethod
    def generate_config_hash(config_data: Dict[str, Any]) -> str:
        """Generate reproducible hash of configuration."""
        config_str = json.dumps(config_data, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()

