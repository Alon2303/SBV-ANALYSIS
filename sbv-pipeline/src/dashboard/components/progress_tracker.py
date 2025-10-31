"""Progress tracking UI component."""
import streamlit as st
from typing import Dict, Any, Optional
from src.drivers import DriverManager
from src.drivers.base import DriverStatus


def show_progress_tracker(driver_manager: DriverManager, compact: bool = False):
    """
    Display real-time progress for all data sources.
    
    Args:
        driver_manager: DriverManager instance
        compact: If True, show compact view
    """
    drivers = driver_manager.list_drivers()
    enabled_drivers = [d for d in drivers if d['is_enabled']]
    
    if not enabled_drivers:
        st.info("No data sources enabled")
        return
    
    if not compact:
        st.subheader("📊 Data Source Progress")
    
    # Overall progress
    overall_progress = driver_manager.get_aggregate_progress()
    
    if not compact:
        st.progress(overall_progress / 100.0, text=f"Overall Progress: {overall_progress:.0f}%")
        st.markdown("---")
    
    # Individual source progress
    for driver in enabled_drivers:
        progress = driver['progress']
        status = driver['status']
        
        # Status icon
        if status == 'completed':
            icon = "✅"
            color = "green"
        elif status == 'running':
            icon = "⏳"
            color = "blue"
        elif status == 'failed':
            icon = "❌"
            color = "red"
        elif status == 'disabled':
            icon = "⏸️"
            color = "gray"
        elif status == 'missing_api_key':
            icon = "🔑"
            color = "orange"
        else:
            icon = "⚪"
            color = "gray"
        
        # Show progress bar
        if compact:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.progress(progress / 100.0, text=f"{icon} {driver['display_name']}")
            with col2:
                st.caption(f"{progress:.0f}%")
            with col3:
                st.caption(status)
        else:
            st.markdown(f"### {icon} {driver['display_name']}")
            st.progress(progress / 100.0, text=f"{progress:.0f}% - {status}")
            
            # Get result if available
            result = driver_manager.get_result(driver['name'])
            if result:
                if result.status == DriverStatus.COMPLETED:
                    duration = result.duration_seconds
                    if duration:
                        st.caption(f"✅ Completed in {duration:.1f}s")
                    
                    # Show data preview
                    if result.data:
                        with st.expander(f"📋 View {driver['display_name']} Data"):
                            st.json(result.data, expanded=False)
                
                elif result.status == DriverStatus.FAILED and result.error:
                    st.error(f"Error: {result.error}")
            
            st.markdown("---")


def show_compact_progress(driver_manager: DriverManager):
    """Show compact progress view in sidebar or small space."""
    show_progress_tracker(driver_manager, compact=True)


def show_source_status_badges(driver_manager: DriverManager):
    """
    Show quick status badges for all sources.
    
    Args:
        driver_manager: DriverManager instance
    """
    drivers = driver_manager.list_drivers()
    
    cols = st.columns(len(drivers))
    
    for i, driver in enumerate(drivers):
        with cols[i]:
            status = driver['status']
            
            if status == 'completed':
                st.success(f"✅ {driver['display_name']}", icon="✅")
            elif status == 'running':
                st.info(f"⏳ {driver['display_name']}", icon="⏳")
            elif status == 'failed':
                st.error(f"❌ {driver['display_name']}", icon="❌")
            elif status == 'disabled':
                st.warning(f"⏸️ {driver['display_name']}", icon="⏸️")
            elif status == 'missing_api_key':
                st.warning(f"🔑 {driver['display_name']}", icon="🔑")
            else:
                st.info(f"⚪ {driver['display_name']}")


def show_results_summary(driver_manager: DriverManager):
    """
    Show summary of results from all sources.
    
    Args:
        driver_manager: DriverManager instance
    """
    results = driver_manager.get_results()
    
    if not results:
        st.info("No results yet - run an analysis to see data from all sources")
        return
    
    st.subheader("📊 Results Summary")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    completed = sum(1 for r in results.values() if r.status == DriverStatus.COMPLETED)
    failed = sum(1 for r in results.values() if r.status == DriverStatus.FAILED)
    total_duration = sum(r.duration_seconds for r in results.values() if r.duration_seconds)
    
    with col1:
        st.metric("✅ Completed", completed)
    with col2:
        st.metric("❌ Failed", failed)
    with col3:
        st.metric("⏱️ Total Time", f"{total_duration:.1f}s")
    with col4:
        st.metric("📊 Sources", len(results))
    
    # Detailed results
    with st.expander("📋 Detailed Results"):
        for source_name, result in results.items():
            st.markdown(f"**{source_name.upper()}**")
            
            if result.status == DriverStatus.COMPLETED:
                st.success(f"✅ Success ({result.duration_seconds:.1f}s)")
                
                # Show key data points
                if result.data:
                    data_keys = list(result.data.keys())
                    st.caption(f"Data fields: {', '.join(data_keys[:5])}{'...' if len(data_keys) > 5 else ''}")
            
            elif result.status == DriverStatus.FAILED:
                st.error(f"❌ Failed: {result.error}")
            
            st.markdown("---")

