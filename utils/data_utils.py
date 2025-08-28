import pandas as pd
import requests
import json
import io
from typing import Dict, Any, Tuple, List, Optional
import re
from datetime import datetime

def get_nested_value(data: Dict[str, Any], path: str) -> Any:
    if not path or not path.strip():
        return data
    
    keys = path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        elif isinstance(current, list) and key.isdigit():
            idx = int(key)
            if 0 <= idx < len(current):
                current = current[idx]
            else:
                return None
        else:
            return None
    
    return current


def extract_database_id_from_url(url: str) -> str:
    if not url:
        raise ValueError("Please provide URL of Notion Database")
    
    # 匹配各种Notion URL格式
    patterns = [
        r'notion\.so/([a-f0-9]{32})',  # https://www.notion.so/database_id
        r'notion\.so/.+/([a-f0-9]{32})',  # https://www.notion.so/workspace/database_id
        r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})',  # UUID格式
        r'([a-f0-9]{32})',  # 纯32位ID
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            database_id = match.group(1).replace('-', '').lower()
            if len(database_id) == 32:
                return database_id
    
    raise ValueError("Cannot get valid Database ID rom URL")

def fetch_notion_database(config: Dict[str, Any]) -> pd.DataFrame:
    try:
        from notion_client import Client
    except ImportError:
        raise ImportError("Pleae install notion-client: pip install notion-client")
    
    token = config.get("token", "")
    database_id = config.get("database_id", "")
    max_results = config.get("max_results", 100)
    
    if not token:
        raise ValueError("Please provide Notion Token")
    if not database_id:
        raise ValueError("Please provide Database ID")
   
    database_id = re.sub(r'[^a-f0-9]', '', database_id.lower())
    if len(database_id) != 32:
        raise ValueError(f"Length of database ID shold be 32, current length is: {len(database_id)}")
    

    notion = Client(auth=token)
    
    try:

        response = notion.databases.query(
            database_id=database_id,
            page_size=min(max_results, 100) 
        )
        
        results = response.get("results", [])
        

        while response.get("has_more", False) and len(results) < max_results:
            response = notion.databases.query(
                database_id=database_id,
                page_size=min(max_results - len(results), 100),
                start_cursor=response.get("next_cursor")
            )
            results.extend(response.get("results", []))
        
        if not results:
            raise ValueError("Notion数据库为空或无权限访问")
        
 
        parsed_data = []
        for page in results:
            row = {"id": page.get("id", "")}
            
            properties = page.get("properties", {})
            for prop_name, prop_data in properties.items():
                prop_type = prop_data.get("type", "")
                
                if prop_type == "title":
                    title_list = prop_data.get("title", [])
                    row[prop_name] = "".join([t.get("plain_text", "") for t in title_list])
                elif prop_type == "rich_text":
                    rich_text_list = prop_data.get("rich_text", [])
                    row[prop_name] = "".join([t.get("plain_text", "") for t in rich_text_list])
                elif prop_type == "number":
                    row[prop_name] = prop_data.get("number")
                elif prop_type == "select":
                    select_obj = prop_data.get("select")
                    row[prop_name] = select_obj.get("name", "") if select_obj else ""
                elif prop_type == "multi_select":
                    multi_select_list = prop_data.get("multi_select", [])
                    row[prop_name] = ", ".join([ms.get("name", "") for ms in multi_select_list])
                elif prop_type == "date":
                    date_obj = prop_data.get("date")
                    if date_obj:
                        row[prop_name] = date_obj.get("start", "")
                    else:
                        row[prop_name] = ""
                elif prop_type == "checkbox":
                    row[prop_name] = prop_data.get("checkbox", False)
                elif prop_type == "url":
                    row[prop_name] = prop_data.get("url", "")
                elif prop_type == "email":
                    row[prop_name] = prop_data.get("email", "")
                elif prop_type == "phone_number":
                    row[prop_name] = prop_data.get("phone_number", "")
                elif prop_type == "created_time":
                    row[prop_name] = prop_data.get("created_time", "")
                elif prop_type == "last_edited_time":
                    row[prop_name] = prop_data.get("last_edited_time", "")
                else:
                    row[prop_name] = str(prop_data.get(prop_type, ""))
            
            parsed_data.append(row)
        
        df = pd.DataFrame(parsed_data)
        
        if df.empty:
            raise ValueError("Data from Notion is Null")
        
        return df
        
    except Exception as e:
        if "Unauthorized" in str(e):
            raise ValueError("Notion Token is invalid")
        elif "not_found" in str(e):
            raise ValueError("Cannot find the database, please check Database ID")
        else:
            raise ValueError(f"Notion API wrong: {e}")

def apply_clean_code(df: pd.DataFrame, code: str) -> Tuple[pd.DataFrame, str, Optional[str]]:
    if not code or not code.strip():
        return df.copy(), "", None
    safe_globals = {
        "pd": pd,
        "datetime": datetime,
        "re": re,
        "json": json,
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "map": map,
        "filter": filter,
        "sorted": sorted,
        "sum": sum,
        "max": max,
        "min": min,
        "abs": abs,
        "round": round,
    }
    
    dangerous_names = [
        "__import__", "eval", "exec", "compile", "open", "file",
        "input", "raw_input", "reload", "__builtins__",
        "globals", "locals", "vars", "dir", "hasattr", "getattr", "setattr", "delattr",
        "os", "sys", "subprocess", "importlib"
    ]
    
    for name in dangerous_names:
        if name in safe_globals:
            del safe_globals[name]
    
    dangerous_patterns = [
        r'\b__import__\b', r'\beval\b', r'\bexec\b', r'\bcompile\b',
        r'\bopen\b', r'\bfile\b', r'\binput\b', r'\braw_input\b',
        r'\bos\.', r'\bsys\.', r'\bsubprocess\.',
        r'\bglobals\b', r'\blocals\b', r'\bvars\b',
        r'\b__.*__\b'  
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            return df, "", f"There are dangerous operation in the code: {pattern}"

    local_vars = {"df": df.copy()}
    
    output_buffer = io.StringIO()
    
    try:
        import sys
        old_stdout = sys.stdout
        sys.stdout = output_buffer
 
        exec(code, safe_globals, local_vars)

        sys.stdout = old_stdout

        if "result" in local_vars:
            result_df = local_vars["result"]
        elif "clean_df" in local_vars:
            result_df = local_vars["clean_df"]
        else:
            result_df = local_vars["df"]
        
        if not isinstance(result_df, pd.DataFrame):
            return df, output_buffer.getvalue(), "执行结果不是DataFrame类型"
        
        logs = output_buffer.getvalue()
        return result_df, logs, None
        
    except Exception as e:
        sys.stdout = old_stdout
        logs = output_buffer.getvalue()
        return df, logs, f"error: {str(e)}"

def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    return output.getvalue()

def convert_csv_encoding(file_content: bytes, from_encoding: str, to_encoding: str = "utf-8") -> bytes:
    try:
        # 解码原始内容
        text_content = file_content.decode(from_encoding)
        # 重新编码
        return text_content.encode(to_encoding)
    except Exception as e:
        raise ValueError(f"编码转换失败: {e}")

def detect_csv_encoding(file_content: bytes) -> str:
    encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig', 'cp936', 'latin1', 'iso-8859-1']
    
    for encoding in encodings_to_try:
        try:
            file_content.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    
    return 'utf-8' 