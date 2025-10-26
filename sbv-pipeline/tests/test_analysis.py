"""Tests for SBV analysis components."""
import pytest
from src.analysis import calculate_constriction_index, calculate_readiness_index, calculate_likely_lovely


def test_constriction_index_empty():
    """Test CI calculation with no bottlenecks."""
    result = calculate_constriction_index([])
    assert result["k"] == 0
    assert result["CI_fix"] == 0.0


def test_constriction_index_basic():
    """Test CI calculation with sample bottlenecks."""
    bottlenecks = [
        {"severity_adj": 5},
        {"severity_adj": 4},
        {"severity_adj": 3},
    ]
    
    result = calculate_constriction_index(bottlenecks)
    
    assert result["k"] == 3
    assert result["S"] == 12
    assert result["Md"] == 4
    assert result["Mx"] == 5
    assert result["Cx"] == 1
    assert 0 <= result["CI_fix"] <= 1


def test_readiness_index_basic():
    """Test RI calculation."""
    bottlenecks = [
        {"verified": "verified"},
        {"verified": "partial"},
    ]
    
    result = calculate_readiness_index(
        TRL_raw=5.0,
        IRL_raw=4.0,
        ORL_raw=3.0,
        RCL_raw=2.0,
        bottlenecks=bottlenecks,
        CI_fix=0.5
    )
    
    assert 0 <= result["RI"] <= 1
    assert 0 <= result["RI_skeptical"] <= 1
    assert result["RI_skeptical"] <= result["RI"]  # Skeptical should be lower
    assert 0 <= result["EP"] <= 1


def test_likely_lovely_basic():
    """Test Likely & Lovely calculation."""
    result = calculate_likely_lovely(
        E=3,
        T=4,
        SP=3,
        LV=4
    )
    
    assert result["E"] == 3
    assert result["T"] == 4
    assert result["SP"] == 3
    assert result["LV"] == 4
    assert 0 <= result["LS_norm"] <= 1
    assert 0 <= result["LV_norm"] <= 1
    assert 0 <= result["CCF"] <= 1


def test_likely_lovely_validation():
    """Test input validation."""
    with pytest.raises(ValueError):
        calculate_likely_lovely(E=6, T=3, SP=3, LV=3)  # E out of range
    
    with pytest.raises(ValueError):
        calculate_likely_lovely(E=3, T=0, SP=3, LV=3)  # T out of range


def test_likely_lovely_edge_cases():
    """Test edge cases."""
    # Minimum scores
    result_min = calculate_likely_lovely(E=1, T=1, SP=1, LV=1)
    assert result_min["CCF"] == 0.04  # (1/5) * (1/5)
    
    # Maximum scores
    result_max = calculate_likely_lovely(E=5, T=5, SP=5, LV=5)
    assert result_max["CCF"] == 1.0  # (5/5) * (5/5)
    
    # Mixed
    result_mixed = calculate_likely_lovely(E=5, T=1, SP=1, LV=5)
    assert result_mixed["LS_norm"] == 0.6  # (0.5*5 + 0.25*1 + 0.25*1) / 5
    assert result_mixed["CCF"] == 0.6  # 0.6 * 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

