# This file will have lines 1-882 from original + new show_visualizations
# I'll construct it by copying the first 882 lines and adding new code

def show_visualizations(df):
    """Show visualization charts."""
    col1, col2 = st.columns(2)
    
    with col1:
        # CI vs RI Scatter
        st.markdown("#### Constriction vs Readiness")
        fig1 = px.scatter(
            df,
            x="CI",
            y="RI_Skeptical",
            size="CCF",
            color="RAR",
            hover_data=["Company"],
            labels={"CI": "Constriction Index", "RI_Skeptical": "Readiness Index"},
            color_continuous_scale="RdYlGn_r"
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # CCF Distribution
        st.markdown("#### Claim Confidence Distribution")
        fig2 = px.histogram(
            df,
            x="CCF",
            nbins=20,
            labels={"CCF": "Claim Confidence Factor"}
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        # Likely & Lovely Radar
        st.markdown("#### Likely & Lovely Scores")
        if len(df) > 0:
            fig3 = go.Figure()
            for _, row in df.head(5).iterrows():  # Top 5 companies
                fig3.add_trace(go.Scatterpolar(
                    r=[row["E"], row["T"], row["SP"], row["LV"]],
                    theta=["Evidence", "Theory", "Social Proof", "Lovely"],
                    name=row["Company"]
                ))
            fig3.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])))
            st.plotly_chart(fig3, use_container_width=True)
    
    with col4:
        # Readiness Levels
        st.markdown("#### Readiness Levels (TRL/IRL/ORL/RCL)")
        if len(df) > 0:
            readiness_df = df.head(10)[["Company", "TRL", "IRL", "ORL", "RCL"]]
            fig4 = px.bar(
                readiness_df,
                x="Company",
                y=["TRL", "IRL", "ORL", "RCL"],
                barmode='group',
                labels={"value": "Level (1-9)", "variable": "Type"}
            )
            fig4.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig4, use_container_width=True)


if __name__ == "__main__":
    main()




