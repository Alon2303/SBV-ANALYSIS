"""Source configuration UI component."""
import streamlit as st
from typing import Dict, Any


def show_source_config(driver_manager) -> Dict[str, bool]:
    """
    Display source configuration controls with toggles.
    
    Args:
        driver_manager: DriverManager instance
    
    Returns:
        Dict of source_name -> enabled status
    """
    st.subheader("🔌 Data Source Configuration")
    
    st.markdown("""
    Control which data sources are used for company research. Toggle sources on/off based on your needs and available API keys.
    """)
    
    # Get current driver states
    drivers = driver_manager.list_drivers()
    
    # Create columns for layout
    col1, col2 = st.columns(2)
    
    enabled_states = {}
    
    for i, driver in enumerate(drivers):
        # Alternate between columns
        with col1 if i % 2 == 0 else col2:
            with st.container():
                # Determine if driver can be enabled
                can_enable = True
                status_msg = ""
                
                if driver['requires_api_key'] and not driver['has_api_key']:
                    can_enable = False
                    status_msg = "🔑 API key required"
                elif driver['status'] == 'missing_api_key':
                    can_enable = False
                    status_msg = "🔑 Add API key to .env"
                elif driver['status'] == 'failed':
                    status_msg = "❌ Last run failed"
                elif driver['status'] == 'completed':
                    status_msg = "✅ Ready"
                else:
                    status_msg = "⚡ Ready"
                
                # Show toggle with description
                col_toggle, col_info = st.columns([3, 1])
                
                with col_toggle:
                    # Use session state to persist toggle state
                    key = f"enable_{driver['name']}"
                    if key not in st.session_state:
                        st.session_state[key] = driver['is_enabled'] and can_enable
                    
                    is_enabled = st.checkbox(
                        f"**{driver['display_name']}**",
                        value=st.session_state[key],
                        disabled=not can_enable,
                        key=key,
                        help=driver['description']
                    )
                    
                    enabled_states[driver['name']] = is_enabled
                
                with col_info:
                    st.caption(status_msg)
                
                # Show description
                st.caption(driver['description'])
                
                # Show API key instructions if needed
                if driver['requires_api_key'] and not driver['has_api_key']:
                    with st.expander("ℹ️ How to add API key"):
                        api_key_name = f"{driver['name'].upper()}_API_KEY"
                        st.code(f"""
# Add to .env file:
{api_key_name}=your-key-here
ENABLE_{driver['name'].upper()}=true
                        """, language="bash")
                        
                        # Add links to get API keys
                        if driver['name'] == 'tavily':
                            st.markdown("[Get Tavily API Key →](https://app.tavily.com/sign-up)")
                        elif driver['name'] == 'crunchbase':
                            st.markdown("[Get Crunchbase API Key →](https://www.crunchbase.com/)")
                        elif driver['name'] == 'serpapi':
                            st.markdown("[Get SerpAPI Key →](https://serpapi.com/users/sign_up)")
                
                st.markdown("---")
    
    # Show summary
    enabled_count = sum(1 for v in enabled_states.values() if v)
    total_count = len(enabled_states)
    
    if enabled_count == 0:
        st.warning("⚠️ No data sources enabled! Enable at least one source to run analysis.")
    else:
        st.success(f"✅ {enabled_count} of {total_count} sources enabled")
    
    # Show cost estimate
    st.subheader("💰 Cost Estimate")
    
    monthly_cost = 0
    cost_breakdown = []
    
    for driver in drivers:
        if enabled_states.get(driver['name'], False):
            if driver['name'] == 'wayback':
                cost_breakdown.append(f"• {driver['display_name']}: FREE")
            elif driver['name'] == 'tavily':
                monthly_cost += 30
                cost_breakdown.append(f"• {driver['display_name']}: $30/month")
            elif driver['name'] == 'crunchbase':
                monthly_cost += 29
                cost_breakdown.append(f"• {driver['display_name']}: $29/month")
            elif driver['name'] == 'serpapi':
                monthly_cost += 50
                cost_breakdown.append(f"• {driver['display_name']}: $50/month")
    
    if monthly_cost == 0:
        st.info("🆓 Current configuration: **FREE** (Wayback Machine only)")
    else:
        st.info(f"💵 Estimated monthly cost: **${monthly_cost}**")
    
    if cost_breakdown:
        with st.expander("💳 Cost Breakdown"):
            for item in cost_breakdown:
                st.markdown(item)
    
    return enabled_states

