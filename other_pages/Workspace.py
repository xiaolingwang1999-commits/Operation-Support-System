import streamlit as st
import pandas as pd
import json
from datetime import datetime
from utils.session_state import (
    get_session_state, set_session_state, add_dataset, 
    set_current_table, get_dataset_names, update_clean_data
)
from utils.data_utils import (
    fetch_notion_database, apply_clean_code,
    df_to_excel_bytes, extract_database_id_from_url
)
from utils.chart_utils import create_chart_from_config
from main_pages.Dashboard import add_chart_to_dashboard


def show():
    st.title("🔧 Data Analysis Workspace")
    st.caption("Support import frpm CSV、Excel、API、Notion. Easy to clean and visualize")
    st.markdown("""
        <style>
            .stTabs [data-baseweb="tab-list"] {
                gap: 0px;
            }
            .stTabs [data-baseweb="tab"] {
                flex: 1;
                text-align: center;
                padding: 10px 5px;
                font-size: 14px;
            }
        </style>
        """, unsafe_allow_html=True)
    tabs = st.tabs(["📥 Import Data", "🛠️ Data Wash", "📊 Chart Generation"])
    
    with tabs[0]:
        show_data_import()
    
    with tabs[1]:
        show_data_cleaning()
    
    with tabs[2]:
        show_visualization()
    



def show_data_import():
    st.subheader("📥 Import Data")
    try:
        from notion_client import Client
        NOTION_AVAILABLE = True
    except ImportError:
        NOTION_AVAILABLE = False
    
    if NOTION_AVAILABLE:
        source_options = ["Local Files (CSV/Excel)", "Notion Databases"]
    else:
        source_options = ["Local Files（CSV/Excel）"]
    
    source_type = st.radio("Select the data source", options=source_options, horizontal=True)
    
    if not NOTION_AVAILABLE and "Notion" in str(source_type):
        st.error("❌ Notion features are not available. Please install notion-client: 'pip install notion-client`")
    
    if source_type.startswith("Local Files"):
        show_file_import()
    elif source_type.startswith("Notion") and NOTION_AVAILABLE:
        show_notion_import()

def show_file_import():
    set_session_state("source_type", "file")
    
    file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx", "xls"])
    if file is not None:
        file_name = file.name.lower()
        
        if file_name.endswith(".csv"):
            set_session_state("file_type", "csv")
            set_session_state("excel_sheet", None)
            csv_sep = st.text_input("CSV separator", value=get_session_state("csv_sep", ","), max_chars=3)
            set_session_state("csv_sep", csv_sep)

            table_name = st.text_input("Name of Data Sheet", value=file.name.replace('.csv', ''), key="csv_table_name")
            
            if st.button("Import data", key="import_csv"):
                encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig', 'cp936', 'latin1']
                success = False
                
                for encoding in encodings_to_try:
                    try:
                        file.seek(0)
                        df = pd.read_csv(file, sep=csv_sep, encoding=encoding)
                        source_info = {
                            "type": "csv",
                            "filename": file.name,
                            "encoding": encoding,
                            "separator": csv_sep,
                            "import_time": datetime.now().isoformat()
                        }
                        add_dataset(table_name, df, source_info)
                        if encoding == 'utf-8':
                            st.success(f"CSV import successfully：{len(df):,} row，{len(df.columns)} columns")
                        else:
                            st.success(f"CSV import successfully（The encoding is {encoding}）：{len(df):,} row, {len(df.columns)} columns")
                        st.dataframe(df.head(50), use_container_width=True)
                        success = True
                        break
                    except (UnicodeDecodeError, pd.errors.EmptyDataError, pd.errors.ParserError):
                        continue
                
                if not success:
                    st.error("If the CSV file cannot be read, please check the file format or encoding")
        
        else: 
            set_session_state("file_type", "excel")
            xls = pd.ExcelFile(file)
            sheet = st.selectbox("Select data sheet", options=xls.sheet_names)
            set_session_state("excel_sheet", sheet)

            table_name = st.text_input("Name of Data Sheet", value=f"{file.name.split('.')[0]}_{sheet}", key="excel_table_name")
            
            if st.button("Import Data", key="import_excel"):
                try:
                    df = pd.read_excel(file, sheet_name=sheet)
                    source_info = {
                        "type": "excel",
                        "filename": file.name,
                        "sheet_name": sheet,
                        "import_time": datetime.now().isoformat()
                    }
                    add_dataset(table_name, df, source_info)
                    st.success(f"Excel import successfully：{len(df):,} row, {len(df.columns)} columns（Sheet：{sheet}）")
                    st.dataframe(df.head(50), use_container_width=True)
                except Exception as e:
                    st.error(f"Fail to load Excel：{e}")


def show_notion_import():
    set_session_state("source_type", "notion")
    notion_cfg = get_session_state("notion_config")
    
    with st.container(border=True):
        st.markdown("#### 🗃️ Notion Database configuration")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            notion_cfg["token"] = st.text_input(
                "Notion Token",
                value=notion_cfg.get("token", ""),
                type="password",
                placeholder="get this from your Notion",
                help="Create an integration in your Notion settings and get a token"
            )
        with col2:
            notion_cfg["max_results"] = st.number_input(
                "Maximum Number of Results",
                min_value=1,
                max_value=1000,
                value=int(notion_cfg.get("max_results", 100)),
                step=10
            )
        
        import_method = st.radio(
            "导入方式",
            ["📝 Database ID", "🔗 Link of Database"],
            horizontal=True,
            help="Select Import data via Database ID or Database link"
        )
        
        if import_method == "📝 Database ID":
            notion_cfg["database_id"] = st.text_input(
                "Database ID",
                value=notion_cfg.get("database_id", ""),
                placeholder="get this from your Notion",
                help="A 32-bit string in the database URL"
            )
        else:
            database_url = st.text_input(
                "Link of Database",
                value="",
                placeholder="get this from your Notion",
                help="Paste the full Notion database URL"
            )
            
            if database_url:
                try:
                    extracted_id = extract_database_id_from_url(database_url)
                    notion_cfg["database_id"] = extracted_id
                    st.success(f"✅ Database ID: {extracted_id}")
                except Exception as e:
                    st.error(f"❌ URL resolution failed: {e}")
                    notion_cfg["database_id"] = ""
    
    set_session_state("notion_config", notion_cfg)
    
    table_name = st.text_input("Data Sheet Name", value="Notion Data", key="notion_table_name")
    
    if st.button("📊 Import Data from Notion", type="primary"):
        with st.spinner("Importing from Notion..."):
            try:
                df_raw = fetch_notion_database(notion_cfg)
                source_info = {
                    "type": "notion",
                    "database_id": notion_cfg.get("database_id", ""),
                    "import_time": datetime.now().isoformat()
                }
                add_dataset(table_name, df_raw, source_info)
                st.success(f"Import from Notion Successfully：{len(df_raw):,} row，{len(df_raw.columns)} columns")
                st.dataframe(df_raw.head(50), use_container_width=True)
            except Exception as e:
                st.error(f"Faild to import from Notio：{e}")

def show_data_cleaning():
    st.subheader("🛠️ Data Wash")
    dataset_names = get_dataset_names()
    if dataset_names:
        col1, col2, col3 = st.columns([3, 1.2, 1])
        with col1:
            current_table = get_session_state("current_table")
            selected_table = st.selectbox(
                "Select Data Table",
                options=dataset_names,
                index=dataset_names.index(current_table) if current_table in dataset_names else 0,
                key="table_selector"
            )
            if selected_table != current_table:
                set_current_table(selected_table)
                st.rerun()
        
        with col2:
            st.write("")
            if st.button("🗑️ Delete Data", use_container_width=True, help="Delete the data table you select"):
                if len(dataset_names) > 1:
                    datasets = get_session_state("datasets", {})
                    if selected_table in datasets:
                        del datasets[selected_table]
                        set_session_state("datasets", datasets)
                        remaining_tables = [t for t in dataset_names if t != selected_table]
                        if remaining_tables:
                            set_current_table(remaining_tables[0])
                        else:
                            set_current_table(None)
                        st.rerun()
                else:
                    st.error("There should be at least one table left")
        
        with col3:
            if selected_table:
                dataset = get_session_state("datasets", {}).get(selected_table, {})
                raw_df = dataset.get("raw")
                if raw_df is not None:
                    st.metric("Number of Rows", f"{len(raw_df):,}")
    
    
    current_table = get_session_state("current_table")
    if not current_table:
        st.info("Please upload data from \"Import Data\"page first.")
        return
    
    dataset = get_session_state("datasets", {}).get(current_table, {})
    raw_df = dataset.get("raw")
    if raw_df is None:
        st.info("There is no raw data in current sheet")
        return
    
    show_common_cleaning_operations()
    show_advanced_cleaning()
    show_data_preview()

def show_common_cleaning_operations():
    st.markdown("#### :1234: Commonly Used Data Cleaning Operations")
    current_table = get_session_state("current_table")
    dataset = get_session_state("datasets", {}).get(current_table, {})
    clean_df = dataset.get("clean")
    raw_df = dataset.get("raw")
    
    if clean_df is not None and not clean_df.empty:
        current_df = clean_df
    elif raw_df is not None and not raw_df.empty:
        current_df = raw_df
    else:
        st.warning("No available data")
        return
    
    cols = list(current_df.columns)
    
    with st.container(border=True):
        st.markdown("##### Columns Operation")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Remove Spaces**")
            selected_col_trim = st.selectbox("Select Column（Remove spaces）", options=["Please Select"] + cols, key="trim_col")
            trim_type = st.radio("Delete Type", ["Spaces Front and Back", "All Spaces", "Front Spaces Only", "Back Space Only"], key="trim_type", horizontal=True)
            
            if st.button("🧹 Run Remove", key="btn_trim"):
                if selected_col_trim != "Please Select":
                    try:
                        df_work = current_df.copy()
                        if trim_type == "Spaces Front and Back":
                            df_work[selected_col_trim] = df_work[selected_col_trim].astype(str).str.strip()
                        elif trim_type == "All Spaces":
                            df_work[selected_col_trim] = df_work[selected_col_trim].astype(str).str.replace(' ', '', regex=False)
                        elif trim_type == "Front Spaces Only":
                            df_work[selected_col_trim] = df_work[selected_col_trim].astype(str).str.lstrip()
                        elif trim_type == "Back Space Only":
                            df_work[selected_col_trim] = df_work[selected_col_trim].astype(str).str.rstrip()
                        
                        update_clean_data(current_table, df_work)
                        st.success(f"Run {trim_type} to '{selected_col_trim}' already")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fail to run: {e}")
                else:
                    st.warning("Please select the columns")
        
        with col2:
            st.markdown("**Delete Duplicate Rows**")
            duplicate_cols = st.multiselect("Determine duplicates based on which columns (empty = all columns)", options=cols, key="dup_cols")
            keep_option = st.selectbox("Retain", ["First", "Last"], key="keep_dup")
            
            if st.button("🗑️ Delete Duplicate Rows", key="btn_dedup"):
                try:
                    df_work = current_df.copy()
                    subset_cols = duplicate_cols if duplicate_cols else None
                    keep_val = "first" if keep_option == "First" else "last"
                    
                    original_count = len(df_work)
                    df_work = df_work.drop_duplicates(subset=subset_cols, keep=keep_val)
                    removed_count = original_count - len(df_work)
                    
                    update_clean_data(current_table, df_work)
                    st.success(f"Delete {removed_count} Duplicate Rows, left {len(df_work)} Rows")
                    st.rerun()
                except Exception as e:
                    st.error(f"Fail to run: {e}")
        
        with col3:
            st.markdown("**Delete Null Rows**")
            null_cols = st.multiselect("Determine null values based on which columns (null = arbitrary columns)", options=cols, key="null_cols")
            null_how = st.selectbox("Delete Condition", ["Any column is empty", "All columns are empty"], key="null_how")
            
            if st.button("🚫 Delete Null Rows", key="btn_dropna"):
                try:
                    df_work = current_df.copy()
                    subset_cols = null_cols if null_cols else None
                    how_val = "any" if null_how == "Any column is empty" else "all"
                    
                    original_count = len(df_work)
                    df_work = df_work.dropna(subset=subset_cols, how=how_val)
                    removed_count = original_count - len(df_work)
                    
                    set_session_state("clean_df", df_work)
                    st.success(f"Delete {removed_count} null rows, left {len(df_work)} rows")
                    st.rerun()
                except Exception as e:
                    st.error(f"Fail to run：{e}")

def show_advanced_cleaning():
    st.markdown("---")
    st.markdown("#### 📝 Advanced Cleaning (Code Pattern)")
    st.markdown("You can enter your custom pandas cleaning code below.")
    
    with st.expander("Check out the sample cleaning code", expanded=False):
        st.code(
            """# 示例1：保留列、重命名、类型转换
# df 为输入的 DataFrame，写法1：直接在 df 上修改
# df = df[['日期','渠道','订单金额']].rename(columns={'订单金额':'sales'}).copy()
# df['日期'] = pd.to_datetime(df['日期'])
# df['month'] = df['日期'].dt.to_period('M').astype(str)

# 示例2：写函数并返回 result
# def transform(df):
#     out = df.copy()
#     out = out.dropna(subset=['订单金额'])
#     out['订单金额'] = out['订单金额'].astype(float)
#     return out
# result = transform(df)

# 示例3：分组汇总
# clean_df = df.groupby('渠道', as_index=False)['订单金额'].sum()""",
            language="python"
        )
    
    clean_code = st.text_area(
        "Enter the wash code here",
        value=get_session_state("clean_code", ""),
        height=260,
        placeholder="For example: df = df.rename(columns={'old':'new'})"
    )
    set_session_state("clean_code", clean_code)
    
    if st.button("Run code", type="primary"):
        with st.spinner("Washing Data..."):
            current_table = get_session_state("current_table")
            dataset = get_session_state("datasets", {}).get(current_table, {})
            raw_df = dataset.get("raw")
            if raw_df is None:
                st.error("There is no raw data to clean")
                return
            
            new_df, logs, err = apply_clean_code(raw_df, clean_code)
            if err:
                st.error(err)
            else:
                update_clean_data(current_table, new_df)
                st.success(f"Wash {len(new_df):,} rows and {len(new_df.columns)} columns successfully")
            if logs and logs.strip():
                with st.expander("View the execution log"):
                    st.code(logs)

def show_data_preview():
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Raw Data Preview")
        current_table = get_session_state("current_table")
        dataset = get_session_state("datasets", {}).get(current_table, {})
        raw_df = dataset.get("raw")
        if raw_df is not None:
            st.dataframe(raw_df.head(50), use_container_width=True)
        else:
            st.info("No raw data")
    
    with c2:
        st.markdown("##### Preview of Cleaning Results")
        clean_df = dataset.get("clean")
        if clean_df is not None:
            st.dataframe(clean_df.head(50), use_container_width=True)
        else:
            st.info("Cleaning results have not yet been generated. Click \"Run Clean Code \"to execute.")

def show_visualization():
    st.subheader("📊 Chart Generation")

    dataset_names = get_dataset_names()
    if not dataset_names:
        st.info("No Available Data. Please upload in \"Import Data\"Page.")
        return
    current_table = get_session_state("current_table")
    default_table = None

    datasets = get_session_state("datasets", {})
    for table_name in dataset_names:
        dataset = datasets.get(table_name, {})
        if dataset.get("clean") is not None and not dataset.get("clean").empty:
            default_table = table_name
            break

    if not default_table:
        default_table = current_table if current_table in dataset_names else dataset_names[0]

    selected_table = st.selectbox(
        "Select the data table for chart generation",
        options=dataset_names,
        index=dataset_names.index(default_table) if default_table in dataset_names else 0,
        key="viz_table_selector",
        help="Select the data table for chart generation"
    )

    dataset = datasets.get(selected_table, {})
    clean_df = dataset.get("clean")
    raw_df = dataset.get("raw")

    if clean_df is not None and not clean_df.empty:
        active_df = clean_df
        data_status = "Washed Data"
    elif raw_df is not None and not raw_df.empty:
        active_df = raw_df
        data_status = "Raw Data"
    else:
        active_df = None
        data_status = "No Data"

    if active_df is None or active_df.empty:
        st.info(f"Data sheet '{selected_table}' no available dta. Please import data fisrt.")
        return

    st.caption(f"📊 Currently using: {selected_table} ({data_status}) - {len(active_df):,} 行 × {len(active_df.columns)} 列")
    
    df = active_df
    cols = list(df.columns)

    cfg = get_session_state("viz_config")

    left, right = st.columns([1, 2])
    with left:
        cfg["chart_type"] = st.selectbox("Chart Type", options=["Line Chart", "Bar Chart", "Scatter Plot", "Histogram", "Box Plot"], index=["Line Chart", "Bar Chart", "Scatter Plot", "Histogram", "Box Plot"].index(cfg.get("chart_type", "Line Chart")))
        cfg["x"] = st.selectbox("X Axis", options=[None] + cols, index=(cols.index(cfg.get("x")) + 1) if cfg.get("x") in cols else 0)
        cfg["y"] = st.selectbox("Y Axis", options=[None] + cols, index=(cols.index(cfg.get("y")) + 1) if cfg.get("y") in cols else 0)
        cfg["color"] = st.selectbox("Color/Group", options=[None] + cols, index=(cols.index(cfg.get("color")) + 1) if cfg.get("color") in cols else 0)
        cfg["size"] = st.selectbox("Point Size (Scatter)", options=[None] + cols, index=(cols.index(cfg.get("size")) + 1) if cfg.get("size") in cols else 0)
        cfg["aggregate"] = st.selectbox("Aggregation Function (Bar)", options=["none", "sum", "mean", "median", "count", "min", "max"], index=["none", "sum", "mean", "median", "count", "min", "max"].index(cfg.get("aggregate", "none")))
        cfg["tooltip"] = st.multiselect("Tooltip Fields", options=cols, default=[cfg["x"], cfg["y"]] if cfg.get("x") in cols and cfg.get("y") in cols else [])
        cfg["sample_rows"] = st.number_input("Sample Rows (Improve Rendering Speed)", min_value=100, max_value=200000, value=int(cfg.get("sample_rows", 5000)), step=100)

        with st.expander("Data Preview", expanded=False):
            st.dataframe(df.head(10), use_container_width=True)

        col_d1, col_d2 = st.columns(2)

        with col_d1:
            if st.button("💾 Save Chart", help="Right-click on the chart and select 'Save Image'", use_container_width=True):
                st.info("💡 Right-click on the chart above and select 'Save Image' to download the chart in PNG format")


        with col_d2:
            chart_data = df
            if cfg.get("sample_rows") and len(df) > cfg.get("sample_rows", 5000):
                chart_data = df.sample(n=cfg.get("sample_rows", 5000), random_state=42)
            
            csv_chart_data = chart_data.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="📊 Chart Data CSV",
                data=csv_chart_data,
                file_name="chart_data.csv",
                mime="text/csv",
                help="Download the data used in the current chart",
                use_container_width=True
            )
    
    with right:
        try:
            chart = create_chart_from_config(df, cfg)
            if chart:
                st.altair_chart(chart, use_container_width=True)
            else:
                st.warning("Unable to create chart, please check configuration")
            st.markdown("##### 📌 Apply this chart to the data dashboard interface")
            chart_title = st.text_input("Chart Title", value=f"{cfg.get('chart_type', 'Chart')} - {cfg.get('x', 'X')} vs {cfg.get('y', 'Y')}")
            chart_description = st.text_area("Chart Description", value="", height=68)

            if st.button("📌 Add to Dashboard", type="primary", use_container_width=True):
                try:
                    chart_config_with_table = cfg.copy()
                    chart_config_with_table["source_table"] = selected_table
                    chart_config_with_table["table_columns"] = list(active_df.columns) if active_df is not None else []

                    chart_idx = add_chart_to_dashboard(chart_config_with_table, chart_title, chart_description)
                    st.success(f"Chart added to dashboard! Chart ID: {chart_idx + 1}")
                    st.info(f"📋 Associated Data Table: {selected_table}")
                except Exception as e:
                    st.error(f"Failed to add to dashboard: {e}")
            
            set_session_state("viz_config", cfg)
            

       
        except Exception as e:
            st.error(f"Fail to generate chart{e}")
        