"""
Streamlit Cloud entry point for SBV Analysis Dashboard.

This file allows Streamlit Cloud to easily find and run the dashboard.
Point Streamlit Cloud to this file: streamlit_app.py
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the dashboard (this will execute it)
import src.dashboard.app

