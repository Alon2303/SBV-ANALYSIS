"""Streamlit dashboard for SBV Analysis Pipeline."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.storage import get_db, AnalysisRepository, Analysis
from src.config import settings


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
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Company List",
        "📈 Visualizations",
        "🔍 Detailed Analysis",
        "📊 Comparative Analysis"
    ])
    
    # Tab 1: Company List
    with tab1:
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
    
    # Tab 2: Visualizations
    with tab2:
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
    
    # Tab 3: Detailed Analysis
    with tab3:
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
    
    # Tab 4: Comparative Analysis
    with tab4:
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

