"""Constriction Index (CI) calculation."""
from typing import List, Dict, Any
import statistics


def calculate_constriction_index(
    bottlenecks: List[Dict[str, Any]],
    mode: str = "fixed"
) -> Dict[str, Any]:
    """
    Calculate Constriction Index from bottlenecks.
    
    Args:
        bottlenecks: List of bottleneck dicts with severity_adj
        mode: "fixed" for fixed-scale normalization
    
    Returns:
        Dict with k, S, Md, Mx, Cx, normalized values, and CI_fix
    """
    if not bottlenecks:
        return {
            "k": 0,
            "S": 0.0,
            "Md": 0.0,
            "Mx": 0.0,
            "Cx": 0.0,
            "S_norm_fix": 0.0,
            "Md_norm_fix": 0.0,
            "Mx_norm_fix": 0.0,
            "Cx_norm_fix": 0.0,
            "CI_fix": 0.0,
            "CI_mode": mode,
            "CI_cohort": None
        }
    
    # Extract adjusted severities
    severities = [bn["severity_adj"] for bn in bottlenecks]
    
    # Core metrics
    k = len(severities)  # count
    S = sum(severities)  # sum
    Md = statistics.median(severities)  # median
    Mx = max(severities)  # max
    Cx = Mx - Md  # complexity
    
    # Fixed-scale normalization (assuming 0-5 severity scale, max 7 bottlenecks typical)
    # Based on SBV protocol: S can be up to 35 (7 bottlenecks × 5 severity)
    S_norm_fix = S / 35.0
    Md_norm_fix = Md / 5.0
    Mx_norm_fix = Mx / 5.0
    Cx_norm_fix = Cx / 5.0  # Cx can be 0-5
    
    # Calculate CI_fix as weighted average
    # Weight: S (severity sum) is most important, then Mx, Md, Cx
    # Using weights: 0.4, 0.3, 0.2, 0.1
    CI_fix = (
        0.4 * S_norm_fix +
        0.3 * Mx_norm_fix +
        0.2 * Md_norm_fix +
        0.1 * Cx_norm_fix
    )
    
    return {
        "k": k,
        "S": S,
        "Md": Md,
        "Mx": Mx,
        "Cx": Cx,
        "S_norm_fix": S_norm_fix,
        "Md_norm_fix": Md_norm_fix,
        "Mx_norm_fix": Mx_norm_fix,
        "Cx_norm_fix": Cx_norm_fix,
        "CI_fix": CI_fix,
        "CI_mode": mode,
        "CI_cohort": None  # Can be calculated later with cohort data
    }

