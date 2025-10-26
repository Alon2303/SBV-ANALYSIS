"""JSON Schema validation for SBV results."""
import json
from pathlib import Path
from typing import Dict, Any
from jsonschema import validate, ValidationError

from ..config import settings


def load_schema() -> Dict[str, Any]:
    """Load the SBV tiny schema."""
    schema_path = settings.schema_dir / "sbv_tiny_schema.json"
    if not schema_path.exists():
        # Try to load from project root
        schema_path = settings.project_root.parent / "sbv_tiny_schema.json"
    
    with open(schema_path, "r") as f:
        return json.load(f)


def validate_sbv_result(result: Dict[str, Any]) -> bool:
    """
    Validate SBV result against schema.
    
    Args:
        result: The SBV analysis result dict
    
    Returns:
        True if valid
    
    Raises:
        ValidationError: If validation fails
    """
    schema = load_schema()
    validate(instance=result, schema=schema)
    return True

