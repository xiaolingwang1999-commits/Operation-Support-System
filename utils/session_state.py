import streamlit as st

def init_session_state():
    defaults = {
        "source_type": None,           # 'file' | 'api' | 'notion'
        "file_type": None,             # 'csv' | 'excel'
        "csv_sep": ",",
        "csv_encoding": "utf-8",
        "excel_sheet": None,
        "datasets": {},              
        "current_table": None,       
        "raw_df": None,              
        "clean_df": None,             
        "clean_code": "",

        "api_config": {
            "method": "GET",
            "url": "",
            "headers_json": "{}",
            "params_json": "{}",
            "body_json": "{}",
            "records_path": "",        # e.g. "data.items"
            "enable_pagination": False,
            "page_param": "page",
            "page_start": 1,
            "page_size_param": "page_size",
            "page_size_value": 100,
            "max_pages": 10,
            "timeout": 30,
            "auth_type": "None",
            "auth_bearer_token": "",
            "auth_basic_user": "",
            "auth_basic_pass": "",
        },
        
        "notion_config": {
            "token": "",
            "database_id": "",
            "max_results": 100,
            "filter_json": "{}",
            "sorts_json": "[]",
        },
        
        "viz_config": {
            "chart_type": "Line Chart",
            "x": None,
            "y": None,
            "color": None,
            "size": None,
            "aggregate": "none",
            "tooltip": [],
            "sample_rows": 5000,
        },
        
        "dashboard_charts": [], 
        "dashboard_layout": {}, 
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def get_session_state(key, default=None):
    return st.session_state.get(key, default)

def set_session_state(key, value):
    st.session_state[key] = value

def add_dataset(table_name: str, raw_df, source_info: dict = None):
    if "datasets" not in st.session_state:
        st.session_state["datasets"] = {}
    
    st.session_state["datasets"][table_name] = {
        "raw": raw_df,
        "clean": raw_df.copy(), 
        "source_info": source_info or {}
    }

    set_current_table(table_name)

def set_current_table(table_name: str):
    st.session_state["current_table"] = table_name
    
    if table_name and table_name in st.session_state.get("datasets", {}):
        dataset = st.session_state["datasets"][table_name]
        st.session_state["raw_df"] = dataset["raw"]
        st.session_state["clean_df"] = dataset["clean"]
    else:
        st.session_state["raw_df"] = None
        st.session_state["clean_df"] = None

def get_dataset_names():
    return list(st.session_state.get("datasets", {}).keys())

def update_clean_data(table_name: str, clean_df):
    if table_name in st.session_state.get("datasets", {}):
        st.session_state["datasets"][table_name]["clean"] = clean_df
        
        if st.session_state.get("current_table") == table_name:
            st.session_state["clean_df"] = clean_df

def clear_session_state():
    """清空会话状态"""
    for key in list(st.session_state.keys()):
        if not key.startswith('_'):  
            del st.session_state[key]
    init_session_state()