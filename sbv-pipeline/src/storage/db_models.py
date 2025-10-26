"""SQLAlchemy models for SBV analysis data."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from .database import Base


class Company(Base):
    """Company entity."""
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    homepage = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    analyses = relationship("Analysis", back_populates="company", cascade="all, delete-orphan")


class Analysis(Base):
    """SBV analysis result."""
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    analysis_run_id = Column(String, unique=True, index=True, nullable=False)
    config_hash = Column(String, nullable=False)
    as_of_date = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    
    # Constriction metrics
    k = Column(Integer)  # number of bottlenecks
    S = Column(Float)  # severity sum
    Md = Column(Float)  # median severity
    Mx = Column(Float)  # max severity
    Cx = Column(Float)  # complexity (Mx - Md)
    S_norm_fix = Column(Float)
    Md_norm_fix = Column(Float)
    Mx_norm_fix = Column(Float)
    Cx_norm_fix = Column(Float)
    CI_fix = Column(Float)  # Constriction Index
    CI_mode = Column(String, default="fixed")
    CI_cohort = Column(Float, nullable=True)
    
    # Readiness metrics
    TRL_raw = Column(Float)
    IRL_raw = Column(Float)
    ORL_raw = Column(Float)
    RCL_raw = Column(Float)
    TRL_adj = Column(Float)
    IRL_adj = Column(Float)
    ORL_adj = Column(Float)
    RCL_adj = Column(Float)
    RI = Column(Float)  # Readiness Index
    EP = Column(Float)  # Evidence Penalty
    RI_skeptical = Column(Float)
    RAR = Column(Float)  # Readiness-Adjusted Risk
    
    # Likely & Lovely metrics
    E = Column(Integer)  # Evidence (1-5)
    T = Column(Integer)  # Theory (1-5)
    SP = Column(Integer)  # Social Proof (1-5)
    LS_norm = Column(Float)  # Likely Score normalized
    LV = Column(Float)  # Lovely value (1-5)
    LV_norm = Column(Float)
    CCF = Column(Float)  # Claim Confidence Factor
    
    # Wayback data
    wayback_snapshot_url = Column(String, nullable=True)
    wayback_snapshot_datetime = Column(String, nullable=True)
    wayback_note = Column(Text, nullable=True)
    
    # Funding since snapshot (optional)
    funding_total_usd = Column(Float, nullable=True)
    funding_items = Column(JSON, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="analyses")
    bottlenecks = relationship("Bottleneck", back_populates="analysis", cascade="all, delete-orphan")
    citations = relationship("Citation", back_populates="analysis", cascade="all, delete-orphan")


class Bottleneck(Base):
    """Identified bottleneck for a company."""
    __tablename__ = "bottlenecks"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    
    bottleneck_id = Column(String, nullable=False)  # e.g., "B1", "B2"
    type = Column(String, nullable=False)  # technical, market, regulatory, etc.
    location = Column(String, nullable=False)
    severity_raw = Column(Float, nullable=False)
    severity_adj = Column(Float, nullable=False)
    verified = Column(String, nullable=False)  # verified, partial, unverified
    owner = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    evidence_strength = Column(Integer, nullable=True)
    citations_list = Column(JSON, nullable=True)  # List of citation URLs
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="bottlenecks")


class Citation(Base):
    """Citation/source for analysis."""
    __tablename__ = "citations"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    
    claim = Column(Text, nullable=False)
    url = Column(String, nullable=False)
    date_seen = Column(String, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="citations")

