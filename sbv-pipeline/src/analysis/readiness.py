"""Readiness Index (RI) calculation with Evidence Penalty."""
from typing import Dict, Any, List
import math


def calculate_readiness_index(
    TRL_raw: float,
    IRL_raw: float,
    ORL_raw: float,
    RCL_raw: float,
    bottlenecks: List[Dict[str, Any]],
    CI_fix: float,
    alpha: float = 0.25
) -> Dict[str, Any]:
    """
    Calculate Readiness Index with skeptical Evidence Penalty.
    
    Args:
        TRL_raw: Technology Readiness Level (1-9)
        IRL_raw: Integration Readiness Level (1-9)
        ORL_raw: Operations Readiness Level (1-9)
        RCL_raw: Regulatory/Compliance Level (1-9)
        bottlenecks: List of bottlenecks for verification scoring
        CI_fix: Constriction Index (for RAR calculation)
        alpha: Skeptical penalty factor (default 0.25)
    
    Returns:
        Dict with raw/adjusted readiness levels, RI, EP, RI_skeptical, RAR
    """
    # Apply verification score (VS) to adjust raw levels
    # VS: verified=1.0, partial=0.8, unverified=0.6
    verification_scores = {
        "verified": 1.0,
        "partial": 0.8,
        "unverified": 0.6
    }
    
    # For simplicity, if we have bottleneck verification data, use average VS
    # Otherwise assume partial verification (0.8)
    if bottlenecks:
        avg_vs = sum(
            verification_scores.get(bn.get("verified", "partial"), 0.8)
            for bn in bottlenecks
        ) / len(bottlenecks)
    else:
        avg_vs = 0.8
    
    # Adjusted levels (apply VS discount if claims are unverified)
    TRL_adj = TRL_raw * avg_vs
    IRL_adj = IRL_raw * avg_vs
    ORL_adj = ORL_raw * avg_vs
    RCL_adj = RCL_raw * avg_vs
    
    # Calculate RI using geometric mean (common for composite readiness indices)
    # Normalize to 0-1 scale (divide by 9)
    RI = math.pow(
        (TRL_adj / 9.0) * (IRL_adj / 9.0) * (ORL_adj / 9.0) * (RCL_adj / 9.0),
        0.25  # 4th root for 4 dimensions
    )
    
    # Calculate Evidence Penalty (EP) based on unverified critical claims
    # Count unverified/partial bottlenecks
    if bottlenecks:
        critical_count = len(bottlenecks)
        unverified_count = sum(
            1 for bn in bottlenecks
            if bn.get("verified", "partial") in ["unverified", "partial"]
        )
        p_unver = unverified_count / critical_count if critical_count > 0 else 0
    else:
        p_unver = 0.5  # Default assumption: 50% unverified
    
    EP = 1.0 - (alpha * p_unver)
    
    # Apply skeptical discount
    RI_skeptical = RI * EP
    
    # Readiness-Adjusted Risk (RAR) = RI × CI
    RAR = RI_skeptical * CI_fix
    
    return {
        "TRL_raw": TRL_raw,
        "IRL_raw": IRL_raw,
        "ORL_raw": ORL_raw,
        "RCL_raw": RCL_raw,
        "TRL_adj": TRL_adj,
        "IRL_adj": IRL_adj,
        "ORL_adj": ORL_adj,
        "RCL_adj": RCL_adj,
        "RI": RI,
        "EP": EP,
        "RI_skeptical": RI_skeptical,
        "RAR": RAR
    }

