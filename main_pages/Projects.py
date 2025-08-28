import streamlit as st
from datetime import datetime
import pandas as pd
from sqlalchemy.sql import text
conn = st.connection("postgresql", type="sql")

def get_processes():
    query = """
    SELECT DISTINCT knowlid, knowltitle 
    FROM knowledgeoverviews 
    WHERE typeid = 11
    ORDER BY knowltitle
    """
    result = conn.query(query, ttl=3600)
    return result

def get_users():
    query = """
    SELECT DISTINCT username 
    FROM users 
    WHERE typeid = 2
    ORDER BY username
    """
    result = conn.query(query, ttl=3600)
    return result['username'].tolist()

def get_knowlcontents(knowl_id):
    query = f"""
    SELECT partnum, title, content 
    FROM knowledgecontents 
    WHERE knowlid = '{knowl_id}'
    ORDER BY partnum ASC
    """
    results = conn.query(query, ttl=3600)
    return results

def show(): 
    if 'projects' not in st.session_state:
        st.session_state.projects = []

    if 'show_form' not in st.session_state:
        st.session_state.show_form = False
    
    if 'archive_form' not in st.session_state:
        st.session_state.archive_form = False

    processes_df = get_processes()

    st.title(":white_check_mark: Projects Management")
    col1, col2,col3 = st.columns([2, 0.1,0.1])

    with col2:
        if st.button(":heavy_plus_sign:", help="Click to Add New Project"):
            st.session_state.show_form = True
    with col3:
        if st.button(":briefcase:", help="Click to Archive Project"):
            st.session_state.archive_form = True

    if st.session_state.projects:
        user_options = get_users() 
        for i, project in enumerate(st.session_state.projects):
            with st.expander(f"{project['projectname']}", expanded=True):
                if not project.get('knowlid'):
                    project_df = pd.DataFrame([{
                        "step": 0,
                        "step_title": "",
                        "responsible_staff": "",
                        "begin_time": pd.to_datetime("today").date(),
                        "predict_finish_time": None,
                        "actual_finish_time": None,
                        "completion_rate": 0.0,
                        "remark": ""
                    }])
                else:
                    knowl_contents = get_knowlcontents(project['knowlid'])
                    data = [{
                        "step": row['partnum'],
                        "step_title": row['title'],
                        "responsible_staff": "",
                        "begin_time": pd.to_datetime("today").date(),
                        "predict_finish_time": None,
                        "actual_finish_time": None,
                        "completion_rate": 0.0,
                        "remark": row['content']
                    } for _, row in knowl_contents.iterrows()]
                    project_df = pd.DataFrame(data)

                edited_df = st.data_editor(
                    project_df,
                    column_config={
                        "step": st.column_config.NumberColumn(format="%d"),
                        "step_title": st.column_config.TextColumn(),
                        "responsible_staff": st.column_config.SelectboxColumn(options=user_options),
                        "begin_time": st.column_config.DateColumn(format="YYYY-MM-DD"),
                        "predict_finish_time": st.column_config.DateColumn(format="YYYY-MM-DD"),
                        "actual_finish_time": st.column_config.DateColumn(format="YYYY-MM-DD"),
                        "completion_rate": st.column_config.NumberColumn(format="%.1f%%"),
                        "remark": st.column_config.TextColumn()
                    },
                    num_rows="dynamic",
                    use_container_width=True,
                    key=f"project_editor_{i}"
                )
                
    else:
        st.info("There is no project here，please click + buttion to add.")

    if st.session_state.show_form:
        with st.form("Add Detail of Project"):
            st.subheader("Add New Project")
            
            process_search = st.selectbox(
                "Affiliation Process (Search)",
                options=processes_df['knowlid'].tolist(), 
                format_func=lambda x: processes_df.loc[processes_df['knowlid'] == x, 'knowltitle'].values[0],  # 显示用 knowltitle
                index=None,
                placeholder="If there is no affiliation process, just leave this blank"
            )
            
            project_name = st.text_input("Poject Title*", placeholder="Please input the title of this project")

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Begin Time", datetime.now())
            with col2:
                end_date = st.date_input("Predict Finish Time")

            submitted = st.form_submit_button("Submit")
            if submitted:
                if not project_name:
                    st.error("You must input the title of the project!")
                else:
                    new_project = {
                        'projectname': project_name,
                        'knowlid': process_search,
                        'begintime': start_date,
                        'predictfinishtime': end_date
                    }
                    
                    st.session_state.projects.append(new_project)
                    st.session_state.show_form = False
                    st.rerun()

    if st.session_state.archive_form:
        with st.form("Archive"):
            st.subheader("Archive Project")
            project_search = st.selectbox(
                "Choose the Project You Want to Archive",
                options=[project['projectname'] for project in st.session_state.projects]
            )
            
            end_date = st.date_input("Actual Finish Time", datetime.now())
            submitted = st.form_submit_button("Archive")

        if submitted:
            max_id = conn.query("SELECT COALESCE(MAX(projid), 0) FROM projectsoverviews").iat[0, 0]
            new_project_id = max_id + 1
            project = next(p for p in st.session_state.projects if p['projectname'] == project_search)
            with conn.session as s:
                knowlid_archive = project.get('knowlid')
                if not st.write(project.get('knowlid')):
                    knowlid_archive = 0
                overview_query = f"""
                    INSERT INTO projectsoverviews(projid,knowlid,projtitle,begintime,predictfinishtime,actualfinishtime)
                    VALUES ({new_project_id}, {knowlid_archive}, '{project_search}', 
                            '{project.get('begintime')}','{project.get('predictfinishtime', datetime.now().date())}',
                            '{end_date}')
                    """
                
                s.execute(text(overview_query))
                s.commit()

                project_index = next(i for i, p in enumerate(st.session_state.projects) if p['projectname'] == project_search)
                project_state = st.session_state[f"project_editor_{project_index}"]
                if project.get('knowlid'):
                    knowl_contents = get_knowlcontents(project['knowlid'])
                    data = [{
                        "step": row['partnum'],
                        "step_title": row['title'],
                        "responsible_staff": "",
                        "begin_time": pd.to_datetime("today").date(),
                        "predict_finish_time": None,
                        "actual_finish_time": None,
                        "completion_rate": 0.0,
                        "remark": row['content']
                    } for _, row in knowl_contents.iterrows()]
                    project_df = pd.DataFrame(data)
 
                if project_state['deleted_rows']:
                    deletions = project_state['deleted_rows']
                    project_df = project_df.drop(deletions).reset_index(drop=True)

                if project_state['edited_rows']:
                    for row_index, changes in project_state['edited_rows'].items():
                        row_index = int(row_index)
                        for column, new_value in changes.items():
                            project_df.at[row_index, column] = new_value

                if 'added_rows' in project_state and project_state['added_rows']:
                    for added_row in project_state['added_rows']:

                        if added_row:

                            new_row_data = {}
                            for col in project_df.columns:
                                new_row_data[col] = added_row.get(col, None) 
                            
                            project_df = pd.concat([project_df, pd.DataFrame([new_row_data])], ignore_index=True)
                project_df.insert(0, 'projectid', new_project_id)

                for _, row in project_df.iterrows():
                    content_query = f"""
                    INSERT INTO projectscontents 
                    VALUES (
                        {row['projectid']}, {row['step']}, '{row['step_title']}', 
                        '{row['responsible_staff']}', '{row['begin_time']}', 
                        {f"'{row['predict_finish_time']}'" if pd.notna(row['predict_finish_time']) else 'NULL'}, 
                        {f"'{row['actual_finish_time']}'" if pd.notna(row['actual_finish_time']) else 'NULL'}, 
                        {row['completion_rate']}, '{row['remark']}'
                    )
                    """
                    s.execute(text(content_query))
                    s.commit()
            


            
            st.session_state.projects.pop(i)
            st.success("Project archived successfully!")
            st.cache_data.clear()
            st.session_state.archive_form = False
            st.rerun()

   