#!/usr/bin/env python3
"""Verify SBV Pipeline installation and setup."""
import sys
from pathlib import Path


def check_file(path: Path, description: str) -> bool:
    """Check if file exists."""
    exists = path.exists()
    status = "✓" if exists else "✗"
    print(f"{status} {description}: {path}")
    return exists


def check_directory(path: Path, description: str) -> bool:
    """Check if directory exists."""
    exists = path.is_dir()
    status = "✓" if exists else "✗"
    print(f"{status} {description}: {path}")
    return exists


def check_import(module_name: str) -> bool:
    """Check if module can be imported."""
    try:
        __import__(module_name)
        print(f"✓ Module import: {module_name}")
        return True
    except ImportError as e:
        print(f"✗ Module import: {module_name} - {e}")
        return False


def main():
    """Run verification checks."""
    print("=" * 60)
    print("SBV Pipeline Installation Verification")
    print("=" * 60)
    print()
    
    checks_passed = 0
    checks_total = 0
    
    # Check project structure
    print("Project Structure:")
    print("-" * 60)
    
    root = Path(__file__).parent
    
    structure_checks = [
        (root / "src", "Source directory"),
        (root / "src" / "analysis", "Analysis module"),
        (root / "src" / "research", "Research module"),
        (root / "src" / "storage", "Storage module"),
        (root / "src" / "orchestrator", "Orchestrator module"),
        (root / "src" / "api", "API module"),
        (root / "src" / "dashboard", "Dashboard module"),
        (root / "src" / "export", "Export module"),
        (root / "src" / "input", "Input module"),
        (root / "data", "Data directory"),
        (root / "data" / "input", "Input data directory"),
        (root / "data" / "output", "Output data directory"),
        (root / "schemas", "Schemas directory"),
        (root / "tests", "Tests directory"),
        (root / "notebooks", "Notebooks directory"),
    ]
    
    for path, desc in structure_checks:
        checks_total += 1
        if check_directory(path, desc):
            checks_passed += 1
    
    print()
    
    # Check key files
    print("Key Files:")
    print("-" * 60)
    
    file_checks = [
        (root / "src" / "config.py", "Configuration"),
        (root / "src" / "main.py", "CLI entry point"),
        (root / "src" / "analysis" / "protocol.py", "SBV protocol"),
        (root / "src" / "research" / "researcher.py", "Researcher"),
        (root / "src" / "storage" / "database.py", "Database setup"),
        (root / "src" / "api" / "app.py", "API application"),
        (root / "src" / "dashboard" / "app.py", "Dashboard application"),
        (root / "schemas" / "sbv_tiny_schema.json", "JSON schema"),
        (root / "requirements.txt", "Requirements"),
        (root / "README.md", "README"),
        (root / "QUICKSTART.md", "Quick start guide"),
        (root / "ARCHITECTURE.md", "Architecture doc"),
        (root / "Dockerfile", "Dockerfile"),
        (root / "docker-compose.yml", "Docker Compose"),
    ]
    
    for path, desc in file_checks:
        checks_total += 1
        if check_file(path, desc):
            checks_passed += 1
    
    print()
    
    # Check Python modules
    print("Python Modules:")
    print("-" * 60)
    
    module_checks = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pydantic",
        "pandas",
        "numpy",
        "plotly",
        "streamlit",
        "click",
    ]
    
    for module in module_checks:
        checks_total += 1
        if check_import(module):
            checks_passed += 1
    
    print()
    
    # Check environment
    print("Environment:")
    print("-" * 60)
    
    env_file = root / ".env"
    if env_file.exists():
        print("✓ .env file exists")
        checks_passed += 1
        
        # Check for API keys
        content = env_file.read_text()
        if "OPENAI_API_KEY" in content or "ANTHROPIC_API_KEY" in content:
            print("✓ API key configured (OPENAI or ANTHROPIC)")
            checks_passed += 1
        else:
            print("⚠ Warning: No API key found in .env")
            print("  Add OPENAI_API_KEY or ANTHROPIC_API_KEY to .env")
        checks_total += 2
    else:
        print("✗ .env file not found")
        print("  Run: cp env.example .env")
        checks_total += 2
    
    print()
    
    # Summary
    print("=" * 60)
    print(f"Verification Complete: {checks_passed}/{checks_total} checks passed")
    print("=" * 60)
    
    if checks_passed == checks_total:
        print()
        print("✅ All checks passed! Your installation is ready.")
        print()
        print("Next steps:")
        print("  1. Add your API key to .env (if not already done)")
        print("  2. Run: python -m src.main analyze data/input/example_companies.csv")
        print("  3. View results: python -m src.main dashboard")
        return 0
    else:
        print()
        print("⚠️  Some checks failed. Please review the output above.")
        print()
        print("To fix issues:")
        print("  1. Run setup script: ./setup.sh")
        print("  2. Install missing dependencies: pip install -r requirements.txt")
        print("  3. Check documentation: README.md, QUICKSTART.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())

