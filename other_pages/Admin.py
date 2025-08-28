import streamlit as st
import pandas as pd
from sqlalchemy.sql import text
from datetime import datetime
from utils.session_state import get_session_state, set_session_state
import os

def show():
    st.title("🛠️ Database Admin Panel")
    st.caption("Manage OSS database with full CRUD operations")
    try:
        conn = st.connection("postgresql", type="sql")
        st.success("✅ Successfully connected to PostgreSQL database")
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        return
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Database Overview", 
        "➕ Add Records", 
        "✏️ Edit Records", 
        "🗑️ Delete Records", 
        "⚙️ Database Tools"
    ])
    
    with tab1:
        show_database_overview(conn)
    
    with tab2:
        show_add_records(conn)
    
    with tab3:
        show_edit_records(conn)
    
    with tab4:
        show_delete_records(conn)
    
    with tab5:
        show_database_tools(conn)

def get_table_names(conn):
    try:
        query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        result = conn.session.execute(query)
        tables = [row[0] for row in result.fetchall()]
        return tables
    except Exception as e:
        st.error(f"Error fetching tables: {e}")
        return []

def get_table_data(conn, table_name):
    try:
        query = f"""SELECT * FROM {table_name} LIMIT 1000"""
        df = conn.query(query)
        return df
    except Exception as e:
        st.error(f"Error fetching data from {table_name}: {e}")
        return pd.DataFrame()

def get_table_schema(conn, table_name):
    try:
        query = text("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = :table_name 
            ORDER BY ordinal_position;
        """)
        result = conn.session.execute(query, {"table_name": table_name})
        schema = []
        for row in result.fetchall():
            schema.append({
                "Column Name": row[0],
                "Data Type": row[1],
                "Nullable": row[2],
                "Default": row[3] if row[3] else "None"
            })
        return schema
    except Exception as e:
        st.error(f"Error fetching schema for {table_name}: {e}")
        return []

def get_primary_key(conn, table_name):
    try:
        query = text(f"""
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = '{table_name}'::regclass AND i.indisprimary;
        """)
        result = conn.session.execute(query, {"table_name": table_name})
        primary_keys = [row[0] for row in result.fetchall()]
        return primary_keys[0] if primary_keys else None
    except Exception as e:
        st.error(f"Error fetching primary key for {table_name}: {e}")
        return None

def show_database_overview(conn):
    st.subheader("📊 Database Overview")
    tables = get_table_names(conn)
    
    if not tables:
        st.info("No tables found in the database.")
        return

    selected_table = st.selectbox("Select Table", tables, key="overview_table")
    
    if selected_table:
        df = get_table_data(conn, selected_table)
        
        if not df.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Records", len(df))
            with col2:
                st.metric("Columns", len(df.columns))
            with col3:
                primary_key = get_primary_key(conn, selected_table)
                st.metric("Primary Key", primary_key or "None")
            
            st.subheader(f"Data Preview - {selected_table}")
            st.dataframe(df, use_container_width=True, height=300)
            
            st.subheader("Table Structure")
            schema = get_table_schema(conn, selected_table)
            if schema:
                st.dataframe(pd.DataFrame(schema), use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Refresh Data", use_container_width=True):
                    st.rerun()
            with col2:
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Export CSV",
                    csv,
                    f"{selected_table}_export.csv",
                    "text/csv",
                    use_container_width=True
                )
        else:
            st.warning(f"No data found in table '{selected_table}'")

def show_add_records(conn):
    st.subheader("➕ Add New Records")
    
    tables = get_table_names(conn)
    if not tables:
        st.info("No tables available for adding records.")
        return
    
    selected_table = st.selectbox("Select Table", tables, key="add_table")
    
    if selected_table:
        schema = get_table_schema(conn, selected_table)
        
        if schema:
            st.info(f"Table: {selected_table}")
   
            with st.form(key="add_record_form"):
                st.write("### Add New Record")
                
                input_data = {}
                for column_info in schema:
                    column_name = column_info["Column Name"]
                    data_type = column_info["Data Type"]
                    if "nextval" in str(column_info["Default"]):
                        continue
                        
                    if data_type in ['integer', 'bigint', 'smallint']:
                        input_data[column_name] = st.number_input(
                            f"{column_name} ({data_type})", 
                            value=0, step=1
                        )
                    elif data_type in ['numeric', 'double precision', 'real']:
                        input_data[column_name] = st.number_input(
                            f"{column_name} ({data_type})", 
                            value=0.0, step=0.1
                        )
                    elif data_type == 'boolean':
                        input_data[column_name] = st.checkbox(column_name)
                    else:
                        input_data[column_name] = st.text_input(
                            f"{column_name} ({data_type})", 
                            value=""
                        )
                
                submitted = st.form_submit_button("💾 Add Record")
                
                if submitted:
                    if add_record(conn, selected_table, input_data):
                        st.success("Record added successfully!")
                        st.rerun()

def show_edit_records(conn):
    st.subheader("✏️ Edit Records")
    
    tables = get_table_names(conn)
    if not tables:
        st.info("No tables available for editing.")
        return
    
    selected_table = st.selectbox("Select Table", tables, key="edit_table")
    
    if selected_table:
        df = get_table_data(conn, selected_table)
        primary_key = get_primary_key(conn, selected_table)
        
        if not df.empty and primary_key:
            st.write("### Select Record to Edit")
            
            record_options = [f"{row[primary_key]} - {row.to_dict()}" for _, row in df.iterrows()]
            
            selected_record_idx = st.selectbox(
                "Select Record", 
                options=range(len(df)),
                format_func=lambda x: record_options[x]
            )
            
            if selected_record_idx is not None:
                record_data = df.iloc[selected_record_idx].to_dict()
                
                with st.form(key="edit_record_form"):
                    st.write("### Edit Record")
                    
                    edited_data = {}
                    for column in df.columns:
                        current_value = record_data[column]
                        
                        if pd.isna(current_value):
                            current_value = None
                        
                        if df[column].dtype in ['int64', 'float64']:
                            edited_data[column] = st.number_input(
                                f"{column}", 
                                value=float(current_value) if current_value is not None else 0.0
                            )
                        elif df[column].dtype == 'bool':
                            edited_data[column] = st.checkbox(column, value=bool(current_value) if current_value is not None else False)
                        else:
                            edited_data[column] = st.text_input(
                                f"{column}", 
                                value=str(current_value) if current_value is not None else ""
                            )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submitted = st.form_submit_button("💾 Update Record")
                    with col2:
                        if st.form_submit_button("❌ Cancel"):
                            st.rerun()
                    
                    if submitted:
                        if update_record(conn, selected_table, primary_key, record_data[primary_key], edited_data):
                            st.success("Record updated successfully!")
                            st.rerun()
        else:
            st.warning("No primary key found or table is empty")

def show_delete_records(conn):
    st.subheader("🗑️ Delete Records")
    
    tables = get_table_names(conn)
    if not tables:
        st.info("No tables available for deletion.")
        return
    
    selected_table = st.selectbox("Select Table", tables, key="delete_table")
    
    if selected_table:
        df = get_table_data(conn, selected_table)
        primary_key = get_primary_key(conn, selected_table)
        
        if not df.empty and primary_key:
            st.warning("⚠️ Warning: This action cannot be undone!")
 
            record_options = [f"{row[primary_key]} - {row.to_dict()}" for _, row in df.iterrows()]
            
            records_to_delete = st.multiselect(
                "Select records to delete", 
                options=range(len(df)),
                format_func=lambda x: record_options[x]
            )
            
            if records_to_delete:
                st.write(f"Selected {len(records_to_delete)} records for deletion")
                
                if st.button("🔥 Confirm Delete", type="secondary"):
                    success_count = 0
                    for record_idx in records_to_delete:
                        record_data = df.iloc[record_idx]
                        if delete_record(conn, selected_table, primary_key, record_data[primary_key]):
                            success_count += 1
                    
                    st.success(f"Deleted {success_count} records successfully!")
                    st.rerun()

def show_database_tools(conn):
    st.subheader("⚙️ Database Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### 🔄 Database Operations")
        
        if st.button("🔄 Refresh Database Cache", use_container_width=True):
            st.success("Database cache refreshed!")
            st.rerun()
        
        if st.button("📋 Show Database Info", use_container_width=True):
            show_database_info(conn)
    
    with col2:
        st.write("### 💾 Backup & Restore")
        
        if st.button("📊 Export Schema", use_container_width=True):
            export_schema(conn)

def add_record(conn, table_name, data):
    try:
        columns = ', '.join(data.keys())
        placeholders = ', '.join([f":{key}" for key in data.keys()])
        
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        conn.session.execute(query, data)
        conn.session.commit()
        return True
    except Exception as e:
        st.error(f"Error adding record: {e}")
        conn.session.rollback()
        return False

def update_record(conn, table_name, primary_key, key_value, data):
    try:
        set_clause = ', '.join([f"{key} = :{key}" for key in data.keys()])
        params = data.copy()
        params['key_value'] = key_value
        
        query = f"UPDATE {table_name} SET {set_clause} WHERE {primary_key} = :key_value"
        conn.session.execute(query, params)
        conn.session.commit()
        return True
    except Exception as e:
        st.error(f"Error updating record: {e}")
        conn.session.rollback()
        return False

def delete_record(conn, table_name, primary_key, key_value):
    try:
        query = f"DELETE FROM {table_name} WHERE {primary_key} = :key_value"
        conn.session.execute(query, {"key_value": key_value})
        conn.session.commit()
        return True
    except Exception as e:
        st.error(f"Error deleting record: {e}")
        conn.session.rollback()
        return False

def show_database_info(conn):
    try:
        query = text("""
            SELECT 
                version() as db_version,
                current_database() as db_name,
                current_user as current_user,
                inet_server_addr() as server_address,
                inet_server_port() as server_port
        """)
        result = conn.session.execute(query)
        db_info = result.fetchone()
        tables = get_table_names(conn)
        
        info = {
            "Database Version": db_info[0],
            "Database Name": db_info[1],
            "Current User": db_info[2],
            "Server Address": db_info[3],
            "Server Port": db_info[4],
            "Total Tables": len(tables),
            "Table Names": tables
        }
        
        st.json(info)
        
    except Exception as e:
        st.error(f"Error getting database info: {e}")

def export_schema(conn):
    try:
        query = text("""
            SELECT 
                table_name,
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
        """)
        result = conn.session.execute(query)
        schema_data = result.fetchall()
        schema_md = "# Database Schema\n\n"
        current_table = ""
        
        for row in schema_data:
            if row[0] != current_table:
                current_table = row[0]
                schema_md += f"## Table: {current_table}\n\n"
                schema_md += "| Column Name | Data Type | Nullable | Default |\n"
                schema_md += "|-------------|-----------|----------|---------|\n"
            
            schema_md += f"| {row[1]} | {row[2]} | {row[3]} | {row[4] or 'None'} |\n"
        
        st.download_button(
            "📥 Download Schema",
            schema_md,
            "database_schema.md",
            "text/markdown",
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"Error exporting schema: {e}")