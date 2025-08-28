ℹ️ Repository Information
Project Name: Operation Support System
Repository URL: https://github.com/xiaolingwang1999-commits/Operation-Support-System

😊 How to Run This Project

Prerequisites👀
Python 3.8 or higher
PostgreSQL 12 or higher
Visual Studio Code
Git installed on your system

Application Setup Instructions💻⚡

Clone the Repository 🚩
git clone https://github.com/xiaolingwang1999-commits/Operation-Support-System.git
cd Operation-Support-System

Set Up PostgreSQL Database 📚
Before running the application, you need to set up the PostgreSQL database using the SQL commands in set_database.txt.

Download the Language Model 🤖 
Visit: https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF
Download the llama-2-7b-chat.Q4_K_M.gguf model file

Organize Model Files ✍
Create the following directory structure in your project root:
models/
└── TheBloke/
    └── llama-2-7b-chat.Q4_K_M.gguf

Install required dependencies in Visual Studio Code 👇
pip install -r requirements.txt

Run the Application 🎯
streamlit run run.py
