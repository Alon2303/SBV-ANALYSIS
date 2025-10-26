"""Google Sheets export functionality."""
import logging
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class GoogleSheetsExporter:
    """Export SBV analysis results to Google Sheets."""
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Google Sheets exporter.
        
        Args:
            credentials_path: Path to Google service account JSON credentials
        """
        self.credentials_path = credentials_path
        self.client = None
        
        if credentials_path and Path(credentials_path).exists():
            try:
                import gspread
                from google.oauth2.service_account import Credentials
                
                scopes = [
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
                
                creds = Credentials.from_service_account_file(
                    credentials_path,
                    scopes=scopes
                )
                self.client = gspread.authorize(creds)
                logger.info("Google Sheets client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Google Sheets client: {e}")
    
    def export_analyses(
        self,
        analyses_data: List[dict],
        spreadsheet_name: str = "SBV Analysis Results",
        share_email: Optional[str] = None
    ) -> Optional[str]:
        """
        Export analyses to Google Sheets.
        
        Args:
            analyses_data: List of analysis dictionaries
            spreadsheet_name: Name for the spreadsheet
            share_email: Optional email to share with
        
        Returns:
            Spreadsheet URL if successful, None otherwise
        """
        if not self.client:
            logger.error("Google Sheets client not initialized")
            return None
        
        try:
            # Create or open spreadsheet
            try:
                sheet = self.client.open(spreadsheet_name)
            except:
                sheet = self.client.create(spreadsheet_name)
                logger.info(f"Created new spreadsheet: {spreadsheet_name}")
            
            # Summary worksheet
            self._create_summary_sheet(sheet, analyses_data)
            
            # Detailed metrics worksheet
            self._create_detailed_sheet(sheet, analyses_data)
            
            # Share if email provided
            if share_email:
                sheet.share(share_email, perm_type='user', role='reader')
                logger.info(f"Shared spreadsheet with {share_email}")
            
            return sheet.url
        
        except Exception as e:
            logger.error(f"Error exporting to Google Sheets: {e}")
            return None
    
    def _create_summary_sheet(self, spreadsheet, analyses_data):
        """Create summary worksheet."""
        try:
            worksheet = spreadsheet.worksheet("Summary")
        except:
            worksheet = spreadsheet.add_worksheet("Summary", rows=1000, cols=20)
        
        # Headers
        headers = [
            "Company", "Homepage", "Date", "CI", "RI", "RI_Skeptical",
            "CCF", "RAR", "Bottlenecks", "Status"
        ]
        
        # Data rows
        rows = [headers]
        for a in analyses_data:
            rows.append([
                a.get("company", ""),
                a.get("homepage", ""),
                a.get("as_of_date", ""),
                f"{a.get('constriction', {}).get('CI_fix', 0):.3f}",
                f"{a.get('readiness', {}).get('RI', 0):.3f}",
                f"{a.get('readiness', {}).get('RI_skeptical', 0):.3f}",
                f"{a.get('likely_lovely', {}).get('CCF', 0):.3f}",
                f"{a.get('readiness', {}).get('RAR', 0):.3f}",
                a.get('constriction', {}).get('k', 0),
                "Completed"
            ])
        
        # Update worksheet
        worksheet.clear()
        worksheet.update('A1', rows)
        
        # Format header
        worksheet.format('A1:J1', {
            "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.6},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })
    
    def _create_detailed_sheet(self, spreadsheet, analyses_data):
        """Create detailed metrics worksheet."""
        try:
            worksheet = spreadsheet.worksheet("Detailed Metrics")
        except:
            worksheet = spreadsheet.add_worksheet("Detailed Metrics", rows=1000, cols=30)
        
        # Headers
        headers = [
            "Company", "CI", "S", "Md", "Mx", "k",
            "TRL", "IRL", "ORL", "RCL", "RI", "EP", "RI_Skeptical",
            "E", "T", "SP", "LV", "CCF", "RAR"
        ]
        
        # Data rows
        rows = [headers]
        for a in analyses_data:
            c = a.get('constriction', {})
            r = a.get('readiness', {})
            ll = a.get('likely_lovely', {})
            
            rows.append([
                a.get("company", ""),
                f"{c.get('CI_fix', 0):.3f}",
                c.get('S', 0),
                c.get('Md', 0),
                c.get('Mx', 0),
                c.get('k', 0),
                f"{r.get('TRL_adj', 0):.1f}",
                f"{r.get('IRL_adj', 0):.1f}",
                f"{r.get('ORL_adj', 0):.1f}",
                f"{r.get('RCL_adj', 0):.1f}",
                f"{r.get('RI', 0):.3f}",
                f"{r.get('EP', 0):.3f}",
                f"{r.get('RI_skeptical', 0):.3f}",
                ll.get('E', 0),
                ll.get('T', 0),
                ll.get('SP', 0),
                ll.get('LV', 0),
                f"{ll.get('CCF', 0):.3f}",
                f"{r.get('RAR', 0):.3f}",
            ])
        
        # Update worksheet
        worksheet.clear()
        worksheet.update('A1', rows)
        
        # Format header
        worksheet.format('A1:S1', {
            "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.6},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

