import altair as alt
import pandas as pd
from typing import Dict, Any, Optional

def create_chart_from_config(df: pd.DataFrame, config: Dict[str, Any]) -> Optional[alt.Chart]:
    """Create Altair chart based on configuration"""
    if df is None or df.empty:
        return None
    
    chart_type = config.get("chart_type", "Line Chart")
    x_col = config.get("x")
    y_col = config.get("y")
    color_col = config.get("color")
    size_col = config.get("size")
    aggregate = config.get("aggregate", "none")
    tooltip = config.get("tooltip", [])
    sample_rows = config.get("sample_rows", 5000)
    
    # Data sampling
    if len(df) > sample_rows:
        df_chart = df.sample(n=sample_rows, random_state=42)
    else:
        df_chart = df.copy()
    
    # Base chart object
    base = alt.Chart(df_chart)
    
    # Build encoding
    encoding = {}
    
    if x_col:
        encoding['x'] = alt.X(x_col, title=x_col)
    if y_col:
        if aggregate != "none" and chart_type == "Bar Chart":
            encoding['y'] = alt.Y(f"{aggregate}({y_col})", title=f"{aggregate}({y_col})")
        else:
            encoding['y'] = alt.Y(y_col, title=y_col)
    
    if color_col:
        encoding['color'] = alt.Color(color_col, title=color_col)
    
    if size_col and chart_type == "Scatter Plot":
        encoding['size'] = alt.Size(size_col, title=size_col)
    
    # Set tooltip
    if tooltip:
        encoding['tooltip'] = tooltip
    elif x_col and y_col:
        encoding['tooltip'] = [x_col, y_col]
    
    # Create chart based on type
    if chart_type == "Line Chart":
        chart = base.mark_line(point=True).add_selection(
            alt.selection_interval(bind='scales')
        )
    elif chart_type == "Bar Chart":
        chart = base.mark_bar().add_selection(
            alt.selection_interval(bind='scales')
        )
    elif chart_type == "Scatter Plot":
        chart = base.mark_circle().add_selection(
            alt.selection_interval(bind='scales')
        )
    elif chart_type == "Histogram":
        if x_col:
            chart = base.mark_bar().add_selection(
                alt.selection_interval(bind='scales')
            )
            encoding['x'] = alt.X(f"{x_col}:O", bin=True, title=x_col)
            encoding['y'] = alt.Y('count()', title='Frequency')
        else:
            return None
    elif chart_type == "Box Plot":
        if x_col and y_col:
            chart = base.mark_boxplot().add_selection(
                alt.selection_interval(bind='scales')
            )
        else:
            return None
    else:
        return None
    
    # Apply encoding
    chart = chart.encode(**encoding)
    
    # Set chart properties
    chart = chart.properties(
        width=600,
        height=400,
        title=f"{chart_type}: {x_col} vs {y_col}" if x_col and y_col else chart_type
    ).resolve_scale(
        color='independent'
    )
    
    return chart

def get_chart_summary(config: Dict[str, Any]) -> str:
    """Get chart configuration summary"""
    chart_type = config.get("chart_type", "Unknown")
    x_col = config.get("x", "Not set")
    y_col = config.get("y", "Not set")
    color_col = config.get("color")
    aggregate = config.get("aggregate", "none")
    
    summary = f"{chart_type} | X: {x_col} | Y: {y_col}"
    
    if color_col:
        summary += f" | Group: {color_col}"
    
    if aggregate != "none" and chart_type == "Bar Chart":
        summary += f" | Aggregate: {aggregate}"
    
    return summary

def validate_chart_config(df: pd.DataFrame, config: Dict[str, Any]) -> tuple[bool, str]:
    """Validate if chart configuration is valid"""
    if df is None or df.empty:
        return False, "Data is empty"
    
    chart_type = config.get("chart_type")
    x_col = config.get("x")
    y_col = config.get("y")
    
    if not chart_type:
        return False, "Chart type not selected"
    
    if chart_type in ["Line Chart", "Bar Chart", "Scatter Plot", "Box Plot"]:
        if not x_col or not y_col:
            return False, f"{chart_type} requires X and Y axes"
        
        if x_col not in df.columns:
            return False, f"Column '{x_col}' does not exist"
        
        if y_col not in df.columns:
            return False, f"Column '{y_col}' does not exist"
    
    elif chart_type == "Histogram":
        if not x_col:
            return False, "Histogram requires X axis"
        
        if x_col not in df.columns:
            return False, f"Column '{x_col}' does not exist"
    
    # Check color column
    color_col = config.get("color")
    if color_col and color_col not in df.columns:
        return False, f"Color column '{color_col}' does not exist"
    
    # Check size column
    size_col = config.get("size")
    if size_col and size_col not in df.columns:
        return False, f"Size column '{size_col}' does not exist"
    
    return True, "Configuration is valid"