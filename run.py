import streamlit as st
from other_pages.Login import check_password, is_admin
from other_pages import Admin
st.set_page_config(page_title=" ")
user_role = is_admin()
if not check_password(): 
    st.stop()
if user_role == "admin":
    Admin.show()
else:

    from streamlit_option_menu import option_menu
    import sys
    import os
    # 添加当前目录到Python路径
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    # 导入页面模块
    from main_pages import Dashboard, Home, Knowledge, Projects
    from other_pages import Workspace
    from utils.session_state import init_session_state

    # 页面配置
    st.set_page_config(
        page_title="Operation Support System",
        page_icon="⏫",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 隐藏默认的页面导航
    st.markdown("""
    <style>
        .stAppHeader {display: none;}
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 1rem;
        }
        .workspace-indicator {
            background-color: #e8f5e8;
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #02ab21;
            margin-bottom: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)

    # 初始化会话状态
    init_session_state()

    # 自定义CSS样式
    st.markdown("""
    <style>
        .main-header {
            padding: 1rem 0;
            border-bottom: 1px solid #e0e0e0;
            margin-bottom: 2rem;
        }
        .sidebar .sidebar-content {
            padding-top: 2rem;
        }
        .chart-container {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
            background: white;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)

    # 侧边栏导航
    with st.sidebar:
        st.title("⏫ OSS")
        
        # 检查当前是否在 Workspace 页面
        is_workspace = st.session_state.get('current_page') == 'workspace' or ('page' in st.query_params and st.query_params.page == "workspace")
        
        # 导航选项（不包含 Workspace）
        options = ["Home", "Dashboard", "Projects", "Knowledge"]
        icons = ["house", "bar-chart", "kanban", "book"]
        
        # 获取当前选择的导航项
        nav_selection = st.session_state.get('nav_selection', 'Home')
        if is_workspace:
            # 如果在 Workspace 页面，保持之前的导航选择
            default_index = options.index(nav_selection) if nav_selection in options else 0
        else:
            default_index = options.index(nav_selection) if nav_selection in options else 0
        
        selected = option_menu(
            menu_title=None,
            options=options,
            icons=icons,
            menu_icon="cast",
            default_index=default_index,
            key="main_nav",
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "orange", "font-size": "18px"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "#eee",
                },
                "nav-link-selected": {"background-color": "#02ab21"},
            },
        )
        
        # 更新导航选择
        if not is_workspace:
            st.session_state['nav_selection'] = selected
        
        # 如果在 Workspace 页面，显示返回 Dashboard 的按钮
        if is_workspace:
            st.markdown("---")
            if st.button("⬅️ Back to Main Pages", use_container_width=True):
                st.session_state['current_page'] = 'dashboard'
                if 'page' in st.query_params:
                    st.query_params.clear()
                st.rerun()

    # 检查页面跳转逻辑
    query_params = st.query_params
    if 'page' in query_params and query_params.page == "workspace":
        st.session_state['current_page'] = 'workspace'
        # 显示 Workspace 页面指示器
        Workspace.show()
        
    elif st.session_state.get('current_page') == 'workspace':
        # 显示 Workspace 页面指示器
        Workspace.show()

    else:
        # 根据导航选择显示对应页面
        current_selection = st.session_state.get('nav_selection', 'Home')
        
        if current_selection == "Dashboard":
            Dashboard.show()
        elif current_selection == "Home":
            Home.show()
        elif current_selection == "Knowledge":
            Knowledge.show()
        elif current_selection == "Projects":
            Projects.show()