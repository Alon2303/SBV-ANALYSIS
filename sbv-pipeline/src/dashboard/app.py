"""Streamlit dashboard for SBV Analysis Pipeline."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import asyncio
import tempfile
import csv
from datetime import datetime
import subprocess
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.storage import get_db, AnalysisRepository, Analysis, init_db
from src.config import settings
from src.input import parse_company_file
from src.orchestrator import JobManager


# Check if running on Streamlit Cloud
def is_streamlit_cloud() -> bool:
    """Detect if running on Streamlit Cloud."""
    import os
    return (
        os.getenv("STREAMLIT_RUNTIME_ENVIRONMENT") == "cloud" or
        os.getenv("STREAMLIT_SHARING_MODE") is not None or
        "/mount/src/" in os.getcwd()
    )


# Install Playwright browsers on first run (for Streamlit Cloud)
@st.cache_resource
def install_playwright_browsers():
    """Install Playwright browsers on first run. Cached so it only runs once."""
    try:
        # Check if playwright is available
        import playwright
        
        # Try to install browsers (will skip if already installed)
        result = subprocess.run(
            ["playwright", "install", "chromium"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        if result.returncode == 0:
            return "✅ Playwright browsers ready"
        else:
            return f"⚠️ Playwright install warning: {result.stderr[:200]}"
    except ImportError:
        return "⚠️ Playwright not installed - will use requests fallback"
    except Exception as e:
        return f"⚠️ Playwright setup error: {str(e)[:200]}"

# Run Playwright setup (cached, only runs once per deployment)
playwright_status = install_playwright_browsers()


# Page config
st.set_page_config(
    page_title="SBV Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)


@st.cache_data
def load_analyses():
    """Load all analyses from database."""
    with get_db() as db:
        repo = AnalysisRepository(db)
        analyses = repo.list_analyses(limit=1000)
        
        data = []
        for a in analyses:
            # Show all analyses, not just completed
            row = {
                "id": a.id,
                "Company": a.company.name,
                "Status": a.status.upper() if a.status else "UNKNOWN",
                "Date": a.as_of_date,
                "CI": a.CI_fix or 0.0,
                "RI": a.RI or 0.0,
                "RI_Skeptical": a.RI_skeptical or 0.0,
                "CCF": a.CCF or 0.0,
                "RAR": a.RAR or 0.0,
                "Bottlenecks": a.k or 0,
                "TRL": a.TRL_adj or 0.0,
                "IRL": a.IRL_adj or 0.0,
                "ORL": a.ORL_adj or 0.0,
                "RCL": a.RCL_adj or 0.0,
                "E": a.E or 0,
                "T": a.T or 0,
                "SP": a.SP or 0,
                "LV": a.LV or 0,
            }
            
            # Add error/warning indicators
            if a.status == "failed":
                error = a.error_message or "Unknown error"
                # Check for specific error types
                if "403" in error or "Forbidden" in error:
                    row["Notes"] = "🚫 Site blocked"
                elif "No content" in error or "could not be scraped" in error:
                    row["Notes"] = "⚠️ Scraping failed"
                else:
                    row["Notes"] = f"❌ Error: {error[:50]}"
            elif a.status == "completed" and a.k == 0:
                row["Notes"] = "⚠️ No bottlenecks found"
            else:
                row["Notes"] = "✅ OK"
            
            data.append(row)
        
        return pd.DataFrame(data)


def get_analysis_detail(analysis_id: int):
    """Get detailed analysis including bottlenecks and citations."""
    with get_db() as db:
        repo = AnalysisRepository(db)
        analysis = repo.get_analysis(analysis_id)
        if analysis:
            return repo.export_to_json(analysis)
    return None


def run_analysis(companies: list):
    """Run SBV analysis on a list of companies."""
    try:
        # Initialize database
        init_db()
        
        # Create and process job
        manager = JobManager()
        job = manager.create_job(companies)
        
        # Run analysis
        asyncio.run(manager.process_job(job.job_id))
        
        return job, None
    except Exception as e:
        return None, str(e)


def show_wiki_page():
    """Display comprehensive SBV Wiki and Metrics Guide."""
    st.title("📖 SBV Wiki & Metrics Reference Guide")
    st.markdown("### Strategic Bottleneck Validation - Complete Terminology & Formulas")
    
    # Table of contents
    st.markdown("---")
    st.markdown("**Quick Navigation:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("• [Core Metrics](#core-metrics)")
        st.markdown("• [Likely & Lovely](#likely-lovely-metrics)")
    with col2:
        st.markdown("• [Readiness Levels](#readiness-levels)")
        st.markdown("• [Constriction](#constriction-components)")
    with col3:
        st.markdown("• [Verification](#verification-and-penalties)")
        st.markdown("• [Bottlenecks](#bottlenecks)")
    
    st.markdown("---")
    
    # Core Metrics Section
    st.header("🎯 Core Metrics")
    
    with st.expander("**CCF - Claim Confidence Factor** (Range: 0.0 - 1.0)", expanded=True):
        st.markdown("""
        **Definition:** The overall confidence in the company's entrepreneurial claims, combining both plausibility (Likely) and value (Lovely).
        
        **Formula:**
        ```
        CCF = LS_norm × LV_norm
        ```
        
        **Components:**
        - `LS_norm`: Normalized Likely Score (plausibility)
        - `LV_norm`: Normalized Lovely Score (value/impact)
        
        **Interpretation:**
        - **0.7 - 1.0**: Very high confidence - strong evidence + high impact
        - **0.5 - 0.7**: Good confidence - solid basis with meaningful value
        - **0.3 - 0.5**: Moderate confidence - some concerns or limited evidence
        - **0.0 - 0.3**: Low confidence - weak evidence or low impact
        
        **Example:** A claim with perfect evidence and theory (LS=1.0) but modest impact (LV=0.6) yields CCF=0.6.
        """)
    
    with st.expander("**CI - Constriction Index** (Range: 0.0 - 1.0)"):
        st.markdown("""
        **Definition:** Measures how constrained/bottlenecked the company is. Higher = more friction.
        
        **Formula:**
        ```
        CI_fix = 0.40·(S/S_max) + 0.30·(Md/5) + 0.20·(Mx/5) + 0.10·Cx
        ```
        
        **Components:**
        - `S`: Total adjusted severity of all bottlenecks
        - `S_max`: Maximum possible severity (k × 5, where k = number of bottlenecks)
        - `Md`: Median severity (0-5)
        - `Mx`: Maximum severity (0-5)
        - `Cx`: Complexity factor (1.0 + 0.05 × number of cross-dependencies)
        
        **Interpretation:**
        - **0.8 - 1.0**: Severely constrained - many critical blockers
        - **0.6 - 0.8**: Moderately constrained - significant challenges ahead
        - **0.3 - 0.6**: Some friction - manageable bottlenecks
        - **0.0 - 0.3**: Low friction - clear path forward
        
        **Note:** This is a "bad is high" metric - you want LOW constriction.
        """)
    
    with st.expander("**RI_Skeptical - Skeptical Readiness Index** (Range: 0.0 - 1.0)"):
        st.markdown("""
        **Definition:** The company's readiness to execute, adjusted for unverified claims (skeptical discount).
        
        **Formula:**
        ```
        RI = 0.40·(TRL/9) + 0.25·(IRL/9) + 0.20·(ORL/9) + 0.15·(RCL/9)
        
        EP (Evidence Penalty) = 1 - α·p_unver
            where α = 0.25 (default)
            p_unver = fraction of critical claims that are unverified
        
        RI_skeptical = RI × EP
        ```
        
        **Components:**
        - `TRL`: Technology Readiness Level (1-9)
        - `IRL`: Integration Readiness Level (1-9)
        - `ORL`: Operations Readiness Level (1-9)
        - `RCL`: Regulatory/Compliance Readiness Level (1-9)
        - `EP`: Evidence Penalty for unverified claims
        
        **Interpretation:**
        - **0.7 - 1.0**: Highly ready - near deployment
        - **0.5 - 0.7**: Moderately ready - advanced development
        - **0.3 - 0.5**: Early stage - significant work remains
        - **0.0 - 0.3**: Very early - proof-of-concept stage
        """)
    
    with st.expander("**RAR - Readiness-Adjusted Risk** (Range: 0.0 - 1.0)"):
        st.markdown("""
        **Definition:** Overall risk metric combining bottlenecks and readiness. Higher = more risk.
        
        **Formula:**
        ```
        RAR = CI_fix × (1 - RI_skeptical)
        ```
        
        **Interpretation:**
        - **0.7 - 1.0**: Very high risk - constrained + not ready
        - **0.5 - 0.7**: High risk - significant challenges
        - **0.3 - 0.5**: Moderate risk - manageable concerns
        - **0.0 - 0.3**: Low risk - good position to execute
        
        **Example:** High constriction (CI=0.8) + low readiness (RI=0.2) → RAR = 0.8 × 0.8 = 0.64 (high risk)
        """)
    
    # Likely & Lovely Section
    st.header("🎲 Likely & Lovely Metrics")
    
    with st.expander("**E - Evidence Score** (Scale: 1-5)"):
        st.markdown("""
        **Definition:** Quality and quantity of independent evidence supporting the claims.
        
        **Scale:**
        - **5**: Independent production data, third-party performance curves, certifications
        - **4**: Pilot results, customer testimonials, credible third-party reports
        - **3**: Some third-party mentions, acceleration/grant awards
        - **2**: Company claims + ecosystem mentions only
        - **1**: No public evidence beyond company statements
        
        **Weight in Likely Score:** 50% (highest weight)
        """)
    
    with st.expander("**T - Theory Score** (Scale: 1-5)"):
        st.markdown("""
        **Definition:** Theoretical/scientific plausibility based on peer-reviewed research and standards.
        
        **Scale:**
        - **5**: Strong peer-reviewed support, proven mechanisms
        - **4**: Good theoretical basis, published research exists
        - **3**: Plausible mechanism, some academic work
        - **2**: Speculative but not impossible
        - **1**: Contradicts known physics/chemistry
        
        **Weight in Likely Score:** 25%
        
        **Note:** Always cite sources (papers, standards, textbooks)
        """)
    
    with st.expander("**SP - Social Proof Score** (Scale: 1-5)"):
        st.markdown("""
        **Definition:** Credibility signals from respected third parties.
        
        **Scale:**
        - **5**: Major customers/partners, top-tier VCs, government contracts
        - **4**: Reputable accelerator, significant grants, advisory board
        - **3**: Known accelerator, smaller grants, some partnerships
        - **2**: Local/regional support only
        - **1**: No notable third-party endorsements
        
        **Weight in Likely Score:** 25%
        """)
    
    with st.expander("**LV - Lovely Score** (Scale: 1-5)"):
        st.markdown("""
        **Definition:** How valuable/impactful the claim would be if true.
        
        **Scale:**
        - **5**: Transformative impact - major decarbonization, cost reduction, safety improvement
        - **4**: Significant value - meaningful improvement over incumbents
        - **3**: Moderate value - incremental but useful improvement
        - **2**: Minor value - marginal improvement
        - **1**: Negligible value - "me too" product
        
        **Note:** Lovely is independent of Likely - a claim can be very valuable but unlikely, or vice versa.
        """)
    
    with st.expander("**LS_norm - Normalized Likely Score** (Range: 0.0 - 1.0)"):
        st.markdown("""
        **Definition:** Composite plausibility score combining Evidence, Theory, and Social Proof.
        
        **Formula:**
        ```
        LS_norm = (0.5·E + 0.25·T + 0.25·SP) / 5
        ```
        
        **Interpretation:**
        - **0.8 - 1.0**: Highly likely - strong evidence across all dimensions
        - **0.6 - 0.8**: Likely - good support with minor gaps
        - **0.4 - 0.6**: Uncertain - mixed evidence
        - **0.2 - 0.4**: Unlikely - weak support
        - **0.0 - 0.2**: Very unlikely - little credible evidence
        """)
    
    with st.expander("**LV_norm - Normalized Lovely Score** (Range: 0.0 - 1.0)"):
        st.markdown("""
        **Definition:** Normalized version of the Lovely score.
        
        **Formula:**
        ```
        LV_norm = LV / 5
        ```
        """)
    
    # Readiness Levels Section
    st.header("🔧 Readiness Levels")
    
    with st.expander("**TRL - Technology Readiness Level** (Scale: 1-9)"):
        st.markdown("""
        **Definition:** Maturity of the core technology (NASA/DOE standard scale).
        
        **Scale:**
        - **9**: Actual system proven in operational environment
        - **7-8**: System prototype demonstration in operational environment
        - **5-6**: Technology/component validated in relevant environment
        - **3-4**: Proof of concept, lab validation
        - **1-2**: Basic principles observed, concept formulated
        
        **Weight in RI:** 40% (highest)
        """)
    
    with st.expander("**IRL - Integration Readiness Level** (Scale: 1-9)"):
        st.markdown("""
        **Definition:** How well the technology integrates with existing systems/infrastructure.
        
        **Scale:**
        - **9**: Fully integrated and field-proven
        - **7-8**: Integration demonstrated in operational environment
        - **5-6**: Integration validated in relevant environment
        - **3-4**: Integration paths identified and tested in lab
        - **1-2**: Integration not yet considered
        
        **Weight in RI:** 25%
        """)
    
    with st.expander("**ORL - Operations Readiness Level** (Scale: 1-9)"):
        st.markdown("""
        **Definition:** Readiness of manufacturing, supply chain, and operational processes.
        
        **Scale:**
        - **9**: Full-scale production, proven supply chain
        - **7-8**: Pilot production line operational
        - **5-6**: Manufacturing process validated at small scale
        - **3-4**: Manufacturing concept developed
        - **1-2**: No manufacturing plan yet
        
        **Weight in RI:** 20%
        """)
    
    with st.expander("**RCL - Regulatory/Compliance Readiness Level** (Scale: 1-9)"):
        st.markdown("""
        **Definition:** Progress toward required certifications, standards, and regulatory approvals.
        
        **Scale:**
        - **9**: All certifications obtained, fully compliant
        - **7-8**: Major certifications in progress or obtained
        - **5-6**: Standards identified, pre-certification testing
        - **3-4**: Regulatory pathway identified
        - **1-2**: No regulatory plan yet
        
        **Weight in RI:** 15%
        
        **Examples:** UL listing, IEC standards, UN 38.3 (batteries), FDA approval
        """)
    
    # Constriction Components
    st.header("🚧 Constriction Components")
    
    with st.expander("**Bottleneck Severity** (Scale: 0-5)"):
        st.markdown("""
        **Definition:** How critical each bottleneck is to progress.
        
        **Scale:**
        - **5**: Critical blocker - company cannot proceed without resolving
        - **4**: Major impediment - significant delays if not addressed
        - **3**: Moderate friction - workarounds exist but costly
        - **2**: Minor issue - manageable with current resources
        - **1**: Negligible - easily resolved
        - **0**: Not a real bottleneck
        
        **Adjustment:** Severity is reduced by verification score (VS) if claims are unverified.
        """)
    
    with st.expander("**k - Number of Bottlenecks**"):
        st.markdown("""
        **Definition:** Total count of identified bottlenecks.
        
        **Typical Categories:**
        - Technical (scale-up, performance validation)
        - Manufacturing (production readiness, supply chain)
        - Regulatory (certifications, standards compliance)
        - Market (customer acquisition, anchor pilots)
        - Financial (capital requirements, unit economics)
        - Integration (compatibility, system-level validation)
        
        **Impact:** More bottlenecks generally → higher CI (constriction)
        """)
    
    with st.expander("**Cx - Complexity Factor**"):
        st.markdown("""
        **Definition:** Adjustment for interdependencies between bottlenecks.
        
        **Formula:**
        ```
        Cx = 1.0 + 0.05 × (number of cross-dependencies)
        ```
        
        **Example:** If bottleneck A (manufacturing scale-up) depends on bottleneck B (unit economics proof), that's a cross-dependency.
        
        **Impact:** Cross-dependencies amplify constriction because resolving one bottleneck may not unblock progress.
        """)
    
    # Verification Section
    st.header("✅ Verification & Penalties")
    
    with st.expander("**VS - Verification Score** (Values: 1.0, 0.8, 0.6)"):
        st.markdown("""
        **Definition:** Discount factor applied to metrics based on verification status.
        
        **Values:**
        - **1.0**: Verified - independent third-party confirmation
        - **0.8**: Partial - some corroboration but not fully independent
        - **0.6**: Unverified - company claim only, no independent support
        
        **Applied to:** TRL, IRL, ORL, RCL, bottleneck severities
        
        **Purpose:** Implements "skeptical discounting" to avoid over-reliance on unverified claims.
        """)
    
    with st.expander("**EP - Evidence Penalty** (Range: 0.0 - 1.0)"):
        st.markdown("""
        **Definition:** Penalty applied to readiness when critical claims lack verification.
        
        **Formula:**
        ```
        EP = 1 - α·p_unver
        
        where:
            α = 0.25 (default penalty coefficient)
            p_unver = fraction of critical claims that are unverified
        ```
        
        **Example:**
        - If 3 of 4 critical claims are unverified: p_unver = 0.75
        - EP = 1 - 0.25×0.75 = 0.8125
        - RI_skeptical = RI × 0.8125 (19% reduction)
        
        **Purpose:** Explicitly discount optimistic projections when evidence is weak.
        """)
    
    # Bottlenecks Section
    st.header("🔍 Bottlenecks")
    
    with st.expander("**What are Bottlenecks?**"):
        st.markdown("""
        **Definition:** Specific frictions, blockers, or risk factors that could prevent the company from achieving its goals.
        
        **Key Attributes:**
        - **Type**: Technical, manufacturing, regulatory, market, financial, integration
        - **Location**: Where in the system/process the bottleneck occurs
        - **Severity**: 0-5 scale (see above)
        - **Verified**: Whether the bottleneck assessment is confirmed by independent sources
        - **Owner**: Who is responsible for resolving it
        - **Timeframe**: When it must be resolved
        
        **Examples:**
        - "Scale-up uniformity" (severity 5) - cannot achieve pilot-scale production
        - "Anchor customer pilot" (severity 5) - no validation pathway without it
        - "UL certification" (severity 4) - required for market access
        - "Unit economics proof" (severity 4) - need to demonstrate cost viability
        """)
    
    # Additional Context
    st.markdown("---")
    st.header("📊 Using These Metrics")
    
    st.markdown("""
    ### Decision Framework
    
    **High-potential companies typically show:**
    - CCF > 0.5 (confident in claims)
    - RI_skeptical > 0.4 (making real progress)
    - CI < 0.7 (not overly constrained)
    - RAR < 0.4 (manageable risk)
    
    **Red flags:**
    - High CCF but low RI → exciting idea, early execution
    - High CI + low RI → many blockers, not ready
    - Low E score but high T/SP → unproven despite hype
    - High RAR → likely to fail or face major delays
    
    ### Comparative Analysis
    
    When comparing companies:
    1. **CCF** for overall promise
    2. **RI_skeptical** for execution readiness
    3. **CI** for near-term friction
    4. **Bottleneck analysis** for specific risks
    5. **E/T/SP breakdown** to understand evidence quality
    
    ### Next Steps Based on Scores
    
    To improve metrics:
    - **Low E**: Arrange third-party testing, publish results, get certifications
    - **Low T**: Partner with research institutions, cite relevant literature
    - **Low SP**: Join credible accelerators, secure grants, get advisors
    - **Low RI**: Focus on TRL advancement and pilot demonstrations
    - **High CI**: Systematically address highest-severity bottlenecks first
    """)
    
    st.markdown("---")
    st.info("💡 **Tip:** Use the filters in the main dashboard to identify companies by specific thresholds. Export results to CSV for further analysis.")


# Main app
def main():
    st.title("📊 SBV Analysis Dashboard")
    st.markdown("Strategic Bottleneck Validation - Company Analysis Results")
    
    # Sidebar - Wiki/Help Button
    st.sidebar.header("📚 Resources")
    
    # Show Playwright status
    if "✅" in playwright_status:
        st.sidebar.success(playwright_status, icon="✅")
    else:
        st.sidebar.info(playwright_status, icon="ℹ️")
    
    # Show database location info on Streamlit Cloud
    if is_streamlit_cloud():
        st.sidebar.warning("⚠️ **Note:** Data is stored in temporary storage and will be lost on app restart. Export results before closing.", icon="⚠️")
    
    if st.sidebar.button("📖 SBV Wiki & Metrics Guide", use_container_width=True):
        st.session_state.show_wiki = True
    
    # Show Wiki Modal if requested
    if st.session_state.get('show_wiki', False):
        show_wiki_page()
        if st.button("✖️ Close Wiki", type="secondary"):
            st.session_state.show_wiki = False
            st.rerun()
        return
    
    # Load data
    df = load_analyses()
    
    if df.empty:
        st.warning("No analyses found. Run analysis first using the CLI.")
        st.code("python -m src.main analyze data/input/companies.csv")
        return
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Metric selection
    metric_filter = st.sidebar.selectbox(
        "Sort by",
        ["CCF", "RI_Skeptical", "CI", "RAR", "Date"],
        index=0
    )
    
    # Threshold filters
    min_ccf = st.sidebar.slider("Min CCF", 0.0, 1.0, 0.0, 0.05)
    min_ri = st.sidebar.slider("Min RI", 0.0, 1.0, 0.0, 0.05)
    
    # Apply filters
    filtered_df = df[
        (df["CCF"] >= min_ccf) &
        (df["RI_Skeptical"] >= min_ri)
    ].sort_values(metric_filter, ascending=False)
    
    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Companies", len(filtered_df))
    with col2:
        st.metric("Avg CI", f"{filtered_df['CI'].mean():.3f}")
    with col3:
        st.metric("Avg RI", f"{filtered_df['RI_Skeptical'].mean():.3f}")
    with col4:
        st.metric("Avg CCF", f"{filtered_df['CCF'].mean():.3f}")
    with col5:
        st.metric("Avg RAR", f"{filtered_df['RAR'].mean():.3f}")
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "➕ Add New Analysis",
        "📋 Company List",
        "📈 Visualizations",
        "🔍 Detailed Analysis",
        "📊 Comparative Analysis"
    ])
    
    # Tab 1: Add New Analysis
    with tab1:
        st.subheader("Add New Companies for Analysis")
        st.markdown("Upload a CSV file or enter company information manually to run SBV analysis.")
        
        # Check for OpenAI API key
        if not settings.openai_api_key or settings.openai_api_key == "your-key-here":
            st.error("⚠️ OpenAI API key not configured! Please set `OPENAI_API_KEY` in your environment or .env file.")
            st.info("The analysis requires an OpenAI API key to work. Add it to your `.env` file or Streamlit Cloud secrets.")
        
        # Two input methods
        input_method = st.radio(
            "Choose input method:",
            ["📤 Upload CSV", "✍️ Manual Entry"]
        )
        
        companies_to_analyze = []
        
        if input_method == "📤 Upload CSV":
            st.markdown("**CSV Format:** Must include `company_name` column. Optional: `homepage` column.")
            st.markdown("Example:")
            st.code("company_name,homepage\nDynami Battery Corp,https://dynami-battery.com/\nQuantumScape,https://www.quantumscape.com/")
            
            uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])
            
            if uploaded_file:
                # Save to temp file and parse
                try:
                    content = uploaded_file.read().decode('utf-8')
                    lines = content.splitlines()
                    reader = csv.DictReader(lines)
                    
                    if 'company_name' not in reader.fieldnames:
                        st.error("CSV must have 'company_name' column")
                    else:
                        for row in reader:
                            company_name = row['company_name'].strip()
                            if company_name:
                                companies_to_analyze.append({
                                    'company_name': company_name,
                                    'homepage': row.get('homepage', '').strip() or None
                                })
                        
                        st.success(f"✅ Loaded {len(companies_to_analyze)} companies from CSV")
                        
                        # Preview
                        if companies_to_analyze:
                            preview_df = pd.DataFrame(companies_to_analyze)
                            st.dataframe(preview_df, use_container_width=True)
                
                except Exception as e:
                    st.error(f"Error reading CSV: {e}")
        
        else:  # Manual Entry
            st.markdown("### Manual Company Entry")
            
            # Entry mode selection
            entry_mode = st.radio(
                "Entry Mode:",
                ["Quick Entry (Name + URL)", "Full Entry (Skip Scraping)"],
                help="Quick: We'll try to scrape. Full: Provide all data manually (use if website is blocked)"
            )
            
            if entry_mode == "Quick Entry (Name + URL)":
                st.info("💡 **Tip:** Providing a homepage URL improves accuracy. If omitted, we'll try to guess it (e.g., 'Intel Corp' → www.intel.com)", icon="ℹ️")
                
                col1, col2 = st.columns([2, 3])
                
                with col1:
                    company_name = st.text_input("Company Name", placeholder="e.g., Intel Corp")
                with col2:
                    homepage = st.text_input("Homepage URL (optional)", placeholder="https://www.intel.com")
                    
                manual_data = None
                
            else:  # Full Entry
                st.info("🛠️ **Manual Entry Mode:** Use this when the website is blocked or unavailable. AI will analyze based on your description.", icon="ℹ️")
                
                company_name = st.text_input("Company Name *", placeholder="e.g., Form Energy")
                homepage = st.text_input("Homepage URL (optional)", placeholder="https://formenergy.com")
                
                col1, col2 = st.columns(2)
                with col1:
                    description = st.text_area(
                        "Company Description *", 
                        placeholder="Brief description of what the company does...",
                        height=100
                    )
                    technology = st.text_input("Core Technology", placeholder="e.g., Iron-air battery")
                    
                with col2:
                    stage = st.selectbox(
                        "Development Stage",
                        ["Research", "Prototype", "Pilot", "Pre-commercial", "Commercial", "Unknown"]
                    )
                    claims = st.text_area(
                        "Key Technical Claims (one per line)",
                        placeholder="100-hour duration storage\nCost below $20/kWh\n...",
                        height=100
                    )
                
                # Package manual data
                manual_data = {
                    "description": description,
                    "technology": technology,
                    "stage": stage,
                    "technical_claims": [c.strip() for c in claims.split('\n') if c.strip()]
                } if description else None
            
            if st.button("➕ Add to List"):
                if company_name:
                    # Validate manual entry mode
                    if entry_mode == "Full Entry (Skip Scraping)" and not manual_data:
                        st.error("Please provide at least a company description for manual entry")
                    else:
                        # Store in session state
                        if 'manual_companies' not in st.session_state:
                            st.session_state.manual_companies = []
                        
                        company_data = {
                            'company_name': company_name.strip(),
                            'homepage': homepage.strip() if homepage else None
                        }
                        
                        # Add manual data if provided
                        if manual_data:
                            company_data['manual_data'] = manual_data
                        
                        st.session_state.manual_companies.append(company_data)
                        
                        if manual_data:
                            st.success(f"✅ Added {company_name} (manual entry - will skip scraping)")
                        else:
                            st.success(f"✅ Added {company_name}")
                        st.rerun()
                else:
                    st.warning("Please enter a company name")
            
            # Show current list
            if 'manual_companies' in st.session_state and st.session_state.manual_companies:
                st.markdown("**Companies to analyze:**")
                manual_df = pd.DataFrame(st.session_state.manual_companies)
                st.dataframe(manual_df, use_container_width=True)
                
                companies_to_analyze = st.session_state.manual_companies
                
                if st.button("🗑️ Clear List"):
                    st.session_state.manual_companies = []
                    st.rerun()
        
        # Run analysis button
        if companies_to_analyze:
            st.markdown("---")
            st.markdown(f"**Ready to analyze {len(companies_to_analyze)} companies**")
            
            if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
                if not settings.openai_api_key or settings.openai_api_key == "your-key-here":
                    st.error("Cannot start analysis without OpenAI API key!")
                else:
                    with st.spinner("Running analysis... This may take several minutes."):
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        status_text.text("Initializing analysis...")
                        progress_bar.progress(10)
                        
                        job, error = run_analysis(companies_to_analyze)
                        
                        if error:
                            st.error(f"❌ Analysis failed: {error}")
                        else:
                            progress_bar.progress(100)
                            status_text.text("Analysis complete!")
                            
                            # Show results
                            progress = job.progress
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total", progress['total'])
                            with col2:
                                st.metric("Completed", progress['completed'], delta=f"{progress['percent']:.1f}%")
                            with col3:
                                st.metric("Failed", progress['failed'])
                            
                            if progress['failed'] > 0:
                                with st.expander("⚠️ View Failed Companies"):
                                    for task in job.companies:
                                        if task.error:
                                            st.markdown(f"**{task.company_name}**: {task.error}")
                            
                            st.success("✅ Analysis complete! Switch to the 'Company List' tab to view results.")
                            
                            # Clear manual entry list
                            if 'manual_companies' in st.session_state:
                                st.session_state.manual_companies = []
                            
                            # Clear cache to show new results
                            st.cache_data.clear()
    
    # Tab 2: Company List
    with tab2:
        st.subheader("Company Analysis Results")
        
        # Display table
        display_cols = [
            "Company", "CCF", "RI_Skeptical", "CI", "RAR",
            "E", "T", "SP", "LV", "Bottlenecks"
        ]
        
        # Format numeric columns
        formatted_df = filtered_df[display_cols].copy()
        for col in ["CCF", "RI_Skeptical", "CI", "RAR"]:
            formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:.3f}")
        
        st.dataframe(
            formatted_df,
            use_container_width=True,
            height=400
        )
        
        # Export button
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="sbv_analysis_results.csv",
            mime="text/csv"
        )
    
    # Tab 3: Visualizations
    with tab3:
        st.subheader("Analysis Visualizations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # CI vs RI Scatter
            st.markdown("#### Constriction vs Readiness")
            fig1 = px.scatter(
                filtered_df,
                x="CI",
                y="RI_Skeptical",
                size="CCF",
                color="RAR",
                hover_name="Company",
                hover_data=["CCF", "Bottlenecks"],
                color_continuous_scale="RdYlGn_r",
                labels={
                    "CI": "Constriction Index (CI)",
                    "RI_Skeptical": "Readiness Index (RI Skeptical)",
                    "CCF": "Claim Confidence Factor",
                    "RAR": "Readiness-Adjusted Risk"
                }
            )
            fig1.update_layout(height=400)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # CCF Ranking
            st.markdown("#### Claim Confidence Factor (Top 10)")
            top_ccf = filtered_df.nlargest(10, "CCF")
            fig2 = px.bar(
                top_ccf,
                x="CCF",
                y="Company",
                orientation="h",
                color="CCF",
                color_continuous_scale="RdYlGn"
            )
            fig2.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig2, use_container_width=True)
        
        col3, col4 = st.columns(2)
        
        with col3:
            # Readiness Components
            st.markdown("#### Readiness Components (Average)")
            readiness_avg = filtered_df[["TRL", "IRL", "ORL", "RCL"]].mean()
            fig3 = go.Figure(data=[
                go.Bar(
                    x=["TRL", "IRL", "ORL", "RCL"],
                    y=readiness_avg.values,
                    marker_color=['#636EFA', '#EF553B', '#00CC96', '#AB63FA']
                )
            ])
            fig3.update_layout(
                height=400,
                yaxis_title="Level (1-9)",
                yaxis_range=[0, 9]
            )
            st.plotly_chart(fig3, use_container_width=True)
        
        with col4:
            # Likely & Lovely Radar
            st.markdown("#### Likely & Lovely (Average)")
            ll_avg = filtered_df[["E", "T", "SP", "LV"]].mean()
            fig4 = go.Figure(data=go.Scatterpolar(
                r=ll_avg.values,
                theta=["Evidence", "Theory", "Social Proof", "Lovely"],
                fill='toself',
                marker_color='#636EFA'
            ))
            fig4.update_layout(
                height=400,
                polar=dict(radialaxis=dict(visible=True, range=[0, 5]))
            )
            st.plotly_chart(fig4, use_container_width=True)
    
    # Tab 4: Detailed Analysis
    with tab4:
        st.subheader("Detailed Company Analysis")
        
        # Company selector
        company_names = filtered_df["Company"].tolist()
        selected_company = st.selectbox("Select Company", company_names)
        
        if selected_company:
            company_row = filtered_df[filtered_df["Company"] == selected_company].iloc[0]
            analysis_id = company_row["id"]
            
            # Load detailed analysis
            detail = get_analysis_detail(analysis_id)
            
            if detail:
                # Company header
                st.markdown(f"### {detail['company']}")
                if detail.get("homepage"):
                    st.markdown(f"🔗 [{detail['homepage']}]({detail['homepage']})")
                st.markdown(f"**Analysis Date:** {detail['as_of_date']}")
                
                # Key metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("CI (Constriction)", f"{detail['constriction']['CI_fix']:.3f}")
                with col2:
                    st.metric("RI (Readiness)", f"{detail['readiness']['RI_skeptical']:.3f}")
                with col3:
                    st.metric("CCF (Confidence)", f"{detail['likely_lovely']['CCF']:.3f}")
                with col4:
                    st.metric("RAR (Risk)", f"{detail['readiness']['RAR']:.3f}")
                
                # Bottlenecks
                st.markdown("#### 🚧 Bottlenecks")
                if detail.get("bottlenecks"):
                    bn_df = pd.DataFrame(detail["bottlenecks"])
                    st.dataframe(
                        bn_df[["id", "type", "location", "severity_adj", "verified", "owner", "timeframe"]],
                        use_container_width=True
                    )
                else:
                    st.info("No bottlenecks identified")
                
                # Citations
                st.markdown("#### 📚 Citations")
                if detail.get("citations"):
                    for cit in detail["citations"]:
                        st.markdown(f"- **{cit['claim']}**  \n  [{cit['url']}]({cit['url']}) (seen: {cit['date_seen']})")
                
                # Raw JSON
                with st.expander("View Raw JSON"):
                    st.json(detail)
    
    # Tab 5: Comparative Analysis
    with tab5:
        st.subheader("Comparative Analysis")
        
        # Multi-select companies
        selected_companies = st.multiselect(
            "Select companies to compare",
            filtered_df["Company"].tolist(),
            default=filtered_df["Company"].tolist()[:5] if len(filtered_df) >= 5 else filtered_df["Company"].tolist()
        )
        
        if selected_companies:
            compare_df = filtered_df[filtered_df["Company"].isin(selected_companies)]
            
            # Metrics comparison
            st.markdown("#### Metrics Comparison")
            
            metrics = ["CI", "RI_Skeptical", "CCF", "RAR"]
            fig = go.Figure()
            
            for metric in metrics:
                fig.add_trace(go.Bar(
                    name=metric,
                    x=compare_df["Company"],
                    y=compare_df[metric]
                ))
            
            fig.update_layout(
                barmode='group',
                height=400,
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Radar comparison
            st.markdown("#### Likely & Lovely Comparison")
            fig2 = go.Figure()
            
            for _, row in compare_df.iterrows():
                fig2.add_trace(go.Scatterpolar(
                    r=[row["E"], row["T"], row["SP"], row["LV"]],
                    theta=["Evidence", "Theory", "Social Proof", "Lovely"],
                    fill='toself',
                    name=row["Company"]
                ))
            
            fig2.update_layout(
                height=500,
                polar=dict(radialaxis=dict(visible=True, range=[0, 5]))
            )
            st.plotly_chart(fig2, use_container_width=True)


if __name__ == "__main__":
    main()

