"""Parse input files (CSV, TXT) with company names."""
import csv
from pathlib import Path
from typing import List, Dict, Any


def parse_company_file(file_path: str) -> List[Dict[str, str]]:
    """
    Parse company input file.
    
    Supports:
    - CSV with 'company_name' and optional 'homepage' columns
    - TXT with one company name per line
    
    Args:
        file_path: Path to input file
    
    Returns:
        List of dicts with 'company_name' and optional 'homepage'
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if path.suffix.lower() == '.csv':
        return parse_csv(path)
    elif path.suffix.lower() in ['.txt', '.text']:
        return parse_txt(path)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")


def parse_csv(path: Path) -> List[Dict[str, str]]:
    """Parse CSV file."""
    companies = []
    
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Check for required column
        if 'company_name' not in reader.fieldnames:
            raise ValueError("CSV must have 'company_name' column")
        
        for row in reader:
            company_name = row['company_name'].strip()
            if not company_name:
                continue
            
            entry = {
                'company_name': company_name,
                'homepage': row.get('homepage', '').strip() or None
            }
            companies.append(entry)
    
    return companies


def parse_txt(path: Path) -> List[Dict[str, str]]:
    """Parse TXT file (one company per line)."""
    companies = []
    
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            company_name = line.strip()
            if company_name and not company_name.startswith('#'):
                companies.append({
                    'company_name': company_name,
                    'homepage': None
                })
    
    return companies

