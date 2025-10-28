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

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.storage import get_db, AnalysisRepository, Analysis, init_db
from src.config import settings
from src.input import parse_company_file
from src.orchestrator import JobManager


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
            if a.status == "completed":
                data.append({
                    "id": a.id,
                    "Company": a.company.name,
                    "Homepage": a.company.homepage or "",
                    "Date": a.as_of_date,
                    "CI": a.CI_fix or 0.0,
                    "RI": a.RI or 0.0,
                    "RI_Skeptical": a.RI_skeptical or 0.0,
                    "CCF": a.CCF or 0.0,
                    "RAR": a.RAR or 0.0,
                    "TRL": a.TRL_adj or 0.0,
                    "IRL": a.IRL_adj or 0.0,
                    "ORL": a.ORL_adj or 0.0,
                    "RCL": a.RCL_adj or 0.0,
                    "E": a.E or 0,
                    "T": a.T or 0,
                    "SP": a.SP or 0,
                    "LV": a.LV or 0,
                    "Bottlenecks": a.k or 0,
                })
        
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


# Main app
def main():
    st.title("📊 SBV Analysis Dashboard")
    st.markdown("Strategic Bottleneck Validation - Company Analysis Results")
    
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
            st.markdown("Enter company information below:")
            
            col1, col2 = st.columns([2, 3])
            
            with col1:
                company_name = st.text_input("Company Name", placeholder="e.g., Dynami Battery Corp")
            with col2:
                homepage = st.text_input("Homepage URL (optional)", placeholder="https://example.com")
            
            if st.button("➕ Add to List"):
                if company_name:
                    # Store in session state
                    if 'manual_companies' not in st.session_state:
                        st.session_state.manual_companies = []
                    
                    st.session_state.manual_companies.append({
                        'company_name': company_name.strip(),
                        'homepage': homepage.strip() if homepage else None
                    })
                    st.success(f"Added {company_name}")
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
        
        st.dataframe(
            filtered_df[display_cols].style.format({
                "CCF": "{:.3f}",
                "RI_Skeptical": "{:.3f}",
                "CI": "{:.3f}",
                "RAR": "{:.3f}"
            }).background_gradient(
                subset=["CCF", "RI_Skeptical"],
                cmap="RdYlGn"
            ),
            use_container_width=True,
            height=400
        )
        
        # Export button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
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

