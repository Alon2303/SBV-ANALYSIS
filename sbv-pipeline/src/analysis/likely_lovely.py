"""Likely & Lovely metrics calculation."""
from typing import Dict, Any


def calculate_likely_lovely(
    E: int,  # Evidence (1-5)
    T: int,  # Theory (1-5)
    SP: int,  # Social Proof (1-5)
    LV: int  # Lovely value (1-5)
) -> Dict[str, Any]:
    """
    Calculate Likely & Lovely metrics and Claim Confidence Factor.
    
    Args:
        E: Evidence rating (1-5)
          1 = no public evidence
          3 = some third-party mention
          5 = independent demo/production data
        T: Theory rating (1-5) - plausibility from peer-review/standards
        SP: Social Proof rating (1-5) - credible accelerators, grants, customers
        LV: Lovely value (1-5) - desirability/impact if true
    
    Returns:
        Dict with E, T, SP, LS_norm, LV, LV_norm, CCF
    """
    # Validate inputs
    for val, name in [(E, "E"), (T, "T"), (SP, "SP"), (LV, "LV")]:
        if not (1 <= val <= 5):
            raise ValueError(f"{name} must be between 1 and 5, got {val}")
    
    # Calculate Likely Score (LS) - weighted blend
    # Evidence matters most (0.5), Theory and Social Proof each 0.25
    LS_norm = (0.5 * E + 0.25 * T + 0.25 * SP) / 5.0
    
    # Normalize Lovely
    LV_norm = LV / 5.0
    
    # Claim Confidence Factor = Likely × Lovely
    CCF = LS_norm * LV_norm
    
    return {
        "E": E,
        "T": T,
        "SP": SP,
        "LS_norm": LS_norm,
        "LV": LV,
        "LV_norm": LV_norm,
        "CCF": CCF
    }

