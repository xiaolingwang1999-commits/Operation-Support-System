import streamlit as st
from datetime import datetime
import pandas as pd
from sqlalchemy.sql import text
conn = st.connection("postgresql", type="sql")

from streamlit_chat import message
import tempfile   # temporary file
from langchain.document_loaders.csv_loader import CSVLoader  # using CSV loaders
from langchain.embeddings import HuggingFaceEmbeddings # import hf embedding
from langchain.vectorstores import FAISS
from llama_cpp import Llama
from langchain.chains import ConversationalRetrievalChain
from langchain_community.llms import LlamaCpp
from langchain_core.runnables import Runnable

def show():
    def get_knowledge_overviews(type_id=None, search_query=None):
        query = f"""
            SELECT knowlid, typeid, knowltitle, versionnum 
            FROM knowledgeoverviews 
            WHERE typeid = 5
            ORDER BY knowlid asc
            """
        if type_id:
            query = f"""
            SELECT knowlid, typeid, knowltitle, versionnum 
            FROM knowledgeoverviews 
            WHERE typeid = '{type_id}'
            ORDER BY knowlid asc
            """
        if search_query:
            query = f"""
            SELECT knowlid, typeid, knowltitle, versionnum 
            FROM knowledgeoverviews 
            WHERE knowltitle ILIKE '%{search_query}%'
            ORDER BY knowlid asc
            """
        results = conn.query(query, ttl=3600)
        return results

    def get_knowledge_contents(knowlid):
        query = f"""
        SELECT partnum, title, content 
        FROM knowledgecontents
        WHERE knowlid = '{knowlid}'
        ORDER BY knowlid asc
        """
        results = conn.query(query, ttl=3600)
        return results
    
    def show_knowl(type_id=None, search_query=None):
        knowledge_data = get_knowledge_overviews(type_id, search_query)
        knowledge_data = knowledge_data[['knowlid', 'versionnum', 'knowltitle']]
        
        
        # Iterate over rows using iterrows()
        for index, row in knowledge_data.iterrows():
            # Option to show raw data
            with st.expander(f''' :pushpin: {row['knowltitle']}'''):
                st.dataframe(
                    row.to_frame().T,
                    use_container_width=True,
                    column_config={
                        "knowlid": st.column_config.NumberColumn(width="small"),
                        "versionnum": st.column_config.NumberColumn(width="small"),
                        "knowltitle": st.column_config.TextColumn(width="large")
                    }
                )
                knowledge_data_detail = get_knowledge_contents(row['knowlid'])
                st.dataframe(knowledge_data_detail,use_container_width=True)

    
    # Create two main sections
    upper_section = st.container()
    lower_section = st.container()
    
    with upper_section:
        st.header(":books: Knowledge Documents")
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

        tabs = st.tabs([":twisted_rightwards_arrows: Process",
        ":office: Policy", 
        "🛠️ Technical Specification",
        ":soon: Operation Guide  ", 
        ":mag: Search"])
        with tabs[0]:
            show_knowl(type_id=11)
        with tabs[1]:
            show_knowl(type_id=7)
        with tabs[2]:
            show_knowl(type_id=9)
        with tabs[3]:
            show_knowl(type_id=5)
        with tabs[4]:
            search_query = st.text_input("Search documents:", placeholder="Enter keywords to search...")
            show_knowl(search_query=search_query)


    
    with lower_section:
        
        DB_FAISS_PATH = 'vectorstore/db_faiss' # # Set the path of our generated embeddings
        model_path = "./models/TheBloke/llama-2-7b-chat.Q4_K_M.gguf"

        llm = LlamaCpp(
        model_path=model_path,
        n_ctx=2048,  # Context window
        n_batch=512,  # Batch size
        temperature=0.7,
        top_p=1,
        verbose=True,
        )

        st.header(":rainbow: AI Assistant")
        uploaded_file = st.file_uploader("Upload File", type="csv") # uploaded file is stored here
        # file uploader
        if uploaded_file:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name # save file locally

            loader = CSVLoader(file_path=tmp_file_path, encoding="utf-8", csv_args={'delimiter': ','}) 
            data = loader.load()
            embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2',model_kwargs={'device': 'cpu'}) 

            db = FAISS.from_documents(data, embeddings) 
            db.save_local(DB_FAISS_PATH)
           
            chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever=db.as_retriever())
           
            def conversational_chat(query):
               
                result = chain({"question": query, "chat_history": st.session_state['history']}) 
                st.session_state['history'].append((query, result["answer"]))
                return result["answer"] 

            if 'history' not in st.session_state:
                st.session_state['history'] = []
            if 'generated' not in st.session_state:
                st.session_state['generated'] = ["Hello ! Ask me(LLAMA2) about " + uploaded_file.name + " 🤗"]
            if 'past' not in st.session_state:
                st.session_state['past'] = ["Hey ! 👋"]

            response_container = st.container() 
            container = st.container()

            with container:
                with st.form(key='my_form', clear_on_submit=True):
                    user_input = st.text_input("Query:", placeholder="Talk to data 👉 (:", key='input') # user input values are here
                    submit_button = st.form_submit_button(label='Send') # button to retrieve answer

                if submit_button and user_input:
                    output = conversational_chat(user_input)

                    st.session_state['past'].append(user_input) 
                    st.session_state['generated'].append(output) 

            if st.session_state['generated']:
                with response_container:
                    for i in range(len(st.session_state['generated'])):
                        message(st.session_state["past"][i], is_user=True, key=str(i) + '_user', avatar_style="big-smile")
                        message(st.session_state["generated"][i], key=str(i), avatar_style="thumbs")
                
