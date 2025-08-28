import streamlit as st
import pandas as pd
import altair as alt
import json
from datetime import datetime
from utils.session_state import get_session_state, set_session_state
from utils.chart_utils import create_chart_from_config

def show():
    """Display data dashboard page"""
    # Page header
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title("📊 Data Dashboard")
    
    with col2:
        if st.button("🔧 Go to Workspace", type="primary", use_container_width=True, key="goto_workspace"):
            # Method 1: Use query parameters
            st.query_params.page = "workspace"
            st.session_state['current_page'] = 'workspace'
            st.rerun()
    
    # Get dashboard charts
    dashboard_charts = get_session_state("dashboard_charts", [])
    
    # If no charts, show prompt
    if not dashboard_charts:
        st.info("📈 No chart data available. Please go to 【Data Analysis Workspace】 to create charts and add them to the dashboard.")
        
        # Show example instructions
        with st.expander("💡 How to Use Data Dashboard", expanded=True):
            st.markdown("""
            ### Usage Steps:
            1. Click the 【🔧 Go to Workspace】 button in the top right
            2. Import data in the workspace (CSV, Excel, API or Notion)
            3. Perform data cleaning (optional)
            4. Create visualization charts
            5. Click 【📌 Add to Dashboard】 to save charts to the dashboard
            6. Return to the dashboard to view all charts
            """)
        return
    
    # Display chart grid
    st.markdown("###  Chart Display :sparkles:")
    
    # Create chart grid layout
    cols_per_row = 2  # Display 2 charts per row
    
    for i in range(0, len(dashboard_charts), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j in range(cols_per_row):
            chart_idx = i + j
            if chart_idx < len(dashboard_charts):
                chart_info = dashboard_charts[chart_idx]
                
                with cols[j]:
                    render_chart_module(chart_info, chart_idx)

def render_chart_module(chart_info, chart_idx):
    """Render single chart module"""
    with st.container(border=True):
        # Chart header
        col1, col2 = st.columns([8, 1])
        
        with col1:
            st.subheader(chart_info.get('title', f'Chart {chart_idx + 1}'))
            if chart_info.get('description'):
                st.caption(chart_info['description'])
        
        with col2:
            # Delete button
            if st.button("🗑️", key=f"delete_{chart_idx}", help="Delete chart"):
                delete_chart_from_dashboard(chart_idx)
                st.rerun()
        
        # Display chart
        try:
            # Get data table information from chart configuration
            chart_config = chart_info.get('config', {})
            source_table = chart_config.get('source_table')
            datasets = get_session_state("datasets", {})

            active_df = None
            data_source_info = ""

            # Preferentially use the data table specified in chart configuration
            if source_table and source_table in datasets:
                dataset = datasets[source_table]
                clean_df = dataset.get("clean")
                raw_df = dataset.get("raw")

                if clean_df is not None and not clean_df.empty:
                    active_df = clean_df
                    data_source_info = f"Data Table: {source_table} (Cleaned)"
                elif raw_df is not None and not raw_df.empty:
                    active_df = raw_df
                    data_source_info = f"Data Table: {source_table} (Raw Data)"

            # If the chart's specified data table doesn't exist, try using the currently selected data table
            if active_df is None:
                current_table = get_session_state("current_table")
                if current_table and current_table in datasets:
                    dataset = datasets[current_table]
                    clean_df = dataset.get("clean")
                    raw_df = dataset.get("raw")

                    if clean_df is not None and not clean_df.empty:
                        active_df = clean_df
                        data_source_info = f"Data Table: {current_table} (Cleaned) - Fallback Mode"
                    elif raw_df is not None and not raw_df.empty:
                        active_df = raw_df
                        data_source_info = f"Data Table: {current_table} (Raw Data) - Fallback Mode"

            # Finally fall back to the old single-table system
            if active_df is None:
                clean_df = get_session_state("clean_df")
                raw_df = get_session_state("raw_df")

                if clean_df is not None and not clean_df.empty:
                    active_df = clean_df
                    data_source_info = "Legacy Data (Cleaned)"
                elif raw_df is not None and not raw_df.empty:
                    active_df = raw_df
                    data_source_info = "Legacy Data (Raw Data)"
            
            if active_df is None or active_df.empty:
                if source_table:
                    st.warning(f"⚠️ The data table '{source_table}' associated with the chart does not exist or has no data")
                    st.info("💡 Please re-import data in the workspace, or delete this chart")
                else:
                    st.warning("⚠️ No data available, please re-import data")
                return

            # Display data source information
            if data_source_info:
                st.caption(f"📊 {data_source_info}")

            # Validate chart configuration compatibility with current data
            x_col = chart_config.get('x')
            y_col = chart_config.get('y')

            # Check if configured columns exist in current data
            missing_cols = []
            if x_col and x_col not in active_df.columns:
                missing_cols.append(f"X Axis: {x_col}")
            if y_col and y_col not in active_df.columns:
                missing_cols.append(f"Y Axis: {y_col}")

            if missing_cols:
                st.error(f"Chart configuration does not match current data, missing columns: {', '.join(missing_cols)}")
                st.info(f"Current data columns: {', '.join(active_df.columns.tolist())}")
                if source_table:
                    st.info(f"💡 Chart created based on data table: {source_table}")
                    expected_cols = chart_config.get('table_columns', [])
                    if expected_cols:
                        st.info(f"Expected columns: {', '.join(expected_cols)}")
                return
            
            # Create chart
            chart = create_chart_from_config(active_df, chart_config)
            
            if chart:
                st.altair_chart(chart, use_container_width=True)
            else:
                st.error("Chart creation failed")
                
        except Exception as e:
            st.error(f"Chart rendering failed: {str(e)}")
            # Show detailed error information for debugging
            with st.expander("View detailed error information"):
                st.code(str(e))
            
        # Display chart information
        with st.expander("📋 Chart Information", expanded=False):
            chart_info_display = {
                "Chart Type": chart_info.get('config', {}).get('chart_type', 'Unknown'),
                "X Axis": chart_info.get('config', {}).get('x', 'Not set'),
                "Y Axis": chart_info.get('config', {}).get('y', 'Not set'),
                "Created At": chart_info.get('created_at', 'Unknown'),
                "Associated Data Table": chart_info.get('config', {}).get('source_table', 'Not associated'),
                "Data Rows": len(active_df) if 'active_df' in locals() and active_df is not None else 0
            }

            # If there is expected column information, also display it
            expected_cols = chart_info.get('config', {}).get('table_columns', [])
            if expected_cols:
                chart_info_display["Expected Column Count"] = len(expected_cols)
                chart_info_display["Expected Column Names"] = ", ".join(expected_cols[:5]) + ("..." if len(expected_cols) > 5 else "")

            st.json(chart_info_display)


def delete_chart_from_dashboard(chart_idx):
    """Delete chart from dashboard"""
    dashboard_charts = get_session_state("dashboard_charts", [])
    if 0 <= chart_idx < len(dashboard_charts):
        removed_chart = dashboard_charts.pop(chart_idx)
        set_session_state("dashboard_charts", dashboard_charts)
        st.success(f"Deleted chart: {removed_chart.get('title', f'Chart {chart_idx + 1}')}")

def add_chart_to_dashboard(chart_config, title=None, description=None):
    """Add chart to dashboard"""
    dashboard_charts = get_session_state("dashboard_charts", [])
    
    chart_info = {
        "config": chart_config,
        "title": title or f"Chart {len(dashboard_charts) + 1}",
        "description": description or "",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "id": len(dashboard_charts)  # Simple ID generation
    }
    
    dashboard_charts.append(chart_info)
    set_session_state("dashboard_charts", dashboard_charts)
    
    return len(dashboard_charts) - 1  # Return the index of the new chart