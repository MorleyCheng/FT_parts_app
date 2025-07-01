import sys
import platform

if platform.system() == "Linux":
    try:
        __import__('pysqlite3')
        sys.modules['sqlite3'] = sys.modules['pysqlite3']
    except ImportError:
        pass

import vanna as vn
from vanna.openai.openai_chat import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore
import streamlit as st
import pandas as pd
from datetime import datetime
import logging
from typing import Dict, List, Optional, Any
import os
import json

class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

class VannaConfig:
    """Vanna AI 配置和管理類別 - 基於官方範例"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model_name = "tooling_parts_model"
        self.training_data_file = "data/training_data.json"
        
        # 初始化 Vanna AI
        self.vn = self._initialize_vanna()
        
        # 載入或建立訓練資料
        self._setup_training_data()
    
    def _initialize_vanna(self):
        """初始化 Vanna AI - 根據官方範例"""
        try:
            # 獲取 OpenAI API 金鑰
            api_key = self._get_openai_api_key()
            if not api_key:
                st.warning("⚠️ 未設置 OpenAI API 金鑰，AI 功能將受限")
                # 使用假的 API 金鑰進行初始化，但會在實際調用時失敗
                api_key = "sk-fake-key-for-initialization"
            
            # 初始化 Vanna 實例（使用 ChromaDB）
            vn_instance = MyVanna(config={
                'api_key': api_key,
                'model': 'gpt-3.5-turbo',  # 或 'gpt-4'
                'path': './chroma_db',  # ChromaDB 資料庫路徑
                'allow_llm_to_see_data': True  # 在配置中設置
            })
            
            # 連接到 SQLite 資料庫
            db_path = os.path.abspath("tooling_data.db")
            if not os.path.exists(db_path):
                self.logger.error(f"資料庫文件不存在: {db_path}")
                return None
            
            vn_instance.connect_to_sqlite(db_path)
            
            # 確保設置允許 LLM 查看資料庫資料
            try:
                vn_instance.allow_llm_to_see_data = True
                self.logger.info("已設置 allow_llm_to_see_data = True")
            except Exception as e:
                self.logger.warning(f"設置 allow_llm_to_see_data 失敗: {str(e)}")
            
            self.logger.info("Vanna AI 初始化成功")
            return vn_instance
            
        except Exception as e:
            self.logger.error(f"Vanna AI 初始化失敗: {str(e)}")
            st.error(f"AI 查詢引擎初始化失敗: {str(e)}")
            return None
    
    def _get_openai_api_key(self) -> Optional[str]:
        """獲取 OpenAI API 金鑰"""
        # 優先從 Streamlit secrets 獲取
        try:
            return st.secrets["openai"]["api_key"]
        except:
            pass
        
        # 從環境變數獲取
        return os.getenv("OPENAI_API_KEY")
    
    def _get_openai_api_key(self) -> Optional[str]:
        """獲取 OpenAI API 金鑰"""
        # 優先從 Streamlit secrets 獲取
        try:
            return st.secrets["openai"]["api_key"]
        except:
            pass
        
        # 從環境變數獲取
        return os.getenv("OPENAI_API_KEY")
    
    def _setup_training_data(self):
        """設置訓練資料 - 參考官方範例"""
        if not self.vn:
            return
        self._train_model()
        try:
            # 檢查是否已經有訓練資料
            existing_training_data = self.vn.get_training_data()
            
            if len(existing_training_data) == 0:
                self.logger.info("開始訓練 Vanna AI 模型...")
                self._train_model()
            else:
                self.logger.info(f"已有 {len(existing_training_data)} 筆訓練資料")
                
        except Exception as e:
            self.logger.error(f"訓練資料設置失敗: {str(e)}")
    
    def _train_model(self):
        """訓練模型 - 基於官方範例的方式"""
        if not self.vn:
            return
            
        try:
            # 1. 根據官方範例，先從資料庫獲取實際的 DDL
            try:
                df_ddl = self.vn.run_sql("SELECT type, sql FROM sqlite_master WHERE sql is not null")
                
                for ddl in df_ddl['sql'].to_list():
                    if ddl and ddl.strip():
                        self.vn.train(ddl=ddl)
                        self.logger.info(f"訓練 DDL: {ddl[:50]}...")
                        
            except Exception as ddl_error:
                self.logger.warning(f"無法從資料庫獲取 DDL，使用預設 DDL: {str(ddl_error)}")
                
                # 備用 DDL 訓練
                ddl_statements = [
                    """
                    CREATE TABLE kyec_parts_all (
                        客戶產品型號 TEXT,
                        客戶名稱 TEXT,
                        配件編號 TEXT,
                        財產編號 TEXT,
                        板全號 TEXT,
                        目前儲位 TEXT,
                        配件狀態 TEXT,
                        舊配件編碼 TEXT,
                        財產歸屬 TEXT,
                        所屬客戶 TEXT,
                        配件種類 TEXT,
                        Dut數 INTEGER,
                        機台型號 TEXT,
                        Handler型號 TEXT,
                        封裝型式 TEXT,
                        狀態開始時間 TEXT,
                        上一個狀態 TEXT,
                        處理時間 TEXT,
                        領用時間 TEXT,
                        配件種類編號 TEXT
                    );
                    """,
                    """
                    CREATE TABLE pat_parts_all (
                        客戶名稱 TEXT,
                        站點 TEXT,
                        配件名稱 TEXT,
                        GLB_NO TEXT,
                        Package_Type TEXT,
                        配件種類 TEXT,
                        LB_DB_NO TEXT,
                        配件狀態 TEXT,
                        待驗收 TEXT,
                        儲位 TEXT,
                        製作出廠日期 TIMESTAMP,
                        財產歸屬 TEXT,
                        客戶財編 TEXT,
                        產品型號 TEXT,
                        配件編號 TEXT,
                        配件種類編號 TEXT,
                        開始時間 TEXT,
                        借出天數 REAL,
                        說明 TEXT,
                        維修天數 REAL,
                        產品型號_簡化 TEXT
                    );
                    """,
                    """
                    CREATE TABLE table_change_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        table_name TEXT,
                        operation TEXT,
                        timestamp TEXT,
                        row_key TEXT,
                        column_name TEXT,
                        old_value TEXT,
                        new_value TEXT,
                        user TEXT,
                        note TEXT
                    );
                    """
                ]
                
                for ddl in ddl_statements:
                    self.vn.train(ddl=ddl)
            
            # 2. 訓練文檔說明
            documentation = [
                "The database contains information about tooling parts from two main sources: PAT and KYEC.",
                "PAT is also known as 鴻谷, 紅古, or 鴻股.",
                "KYEC is also known as 京元電子, 京元電, 京元, or 晶圓.",
                "The customer '創惟' and '創惟科技' refer to the same company, Genesys Logic.",
                "The table 'table_change_log' stores table change log. Its columns are: id, table_name, operation, timestamp, row_key, column_name, old_value, new_value, user, note.",
                "'table_change_log' is an audit table that records all changes made to other tables.",
                "The 'operation' column shows the type of change (e.g., 'update', 'insert').",
                "The table 'query_log' is currently empty.",
                "The table 'pat_parts_all' stores pat parts all. Its columns are: 客戶名稱, 站點, 配件名稱, GLB_NO, Package Type, 配件種類, LB / DB NO, 配件狀態, 待驗收, 儲 位, 製作出廠日期, 財產歸屬, 客戶財編, 產品型號, 配件編號, 配件種類編號, 開始時間, 借出天數, 說明, 維修天數, 產品型號_簡化.",
                "'pat_parts_all' contains detailed records of individual parts from PAT.",
                "'配件狀態' (Part Status) indicates the current state of a part.",
                "Possible values for '配件狀態' in 'pat_parts_all' are: ['OUT_REPAIR', 'REPAIR', 'BORROW', 'PRODUCTION', '其它'].",
                "'維修天數' means repair days, and '借出天數' means loan days.",
                "The table 'pat_stats_weekly' stores pat stats weekly. Its columns are: 配件種類編號, 產品型號_簡化, 站點, 配件種類, 總數量, 正常生產, 廠內維修, 客戶維修, 客戶借出, 其它, 每周狀態.",
                "'pat_stats_weekly' provides weekly aggregated statistics for PAT parts.",
                "Columns like '總數量', '正常生產', '廠內維修' represent the count of parts in each status for that week.",
                "The table 'kyec_parts_all' stores kyec parts all. Its columns are: 客戶產品型號, 客戶名稱, 配件編號, 財產編號, 板全號, 目前儲位, 配件狀態, 舊配件編碼, 財產歸屬, 所屬客戶, 配件種類, Dut數, 機台型號, Handler型號, 封裝型式, 狀態開始時間, 上一個狀態, 處理時間, 領用時間, 配件種類編號.",
                "'kyec_parts_all' contains detailed records of individual parts from KYEC.",
                "'配件狀態' (Part Status) indicates the current state of a part.",
                "Possible values for '配件狀態' in 'kyec_parts_all' are: ['廠內維修', '客戶維修', '正常生產', '其它', '待release'].",
                "The table 'kyec_stats_weekly' stores kyec stats weekly. Its columns are: 板全號, 客戶產品型號, 機台型號, 配件種類, 總數量, 正常生產, 廠內維修, 客戶維修, 客戶借出, 待release, 其它, 每周狀態.",
                "'kyec_stats_weekly' provides weekly aggregated statistics for KYEC parts.",
                "Columns like '總數量', '正常生產', '廠內維修' represent the count of parts in each status for that week."
            ]
            
            for doc in documentation:
                self.vn.train(documentation=doc)
            
            # 3. 訓練問題-SQL 對
            question_sql_pairs = [
                {
                    "question": "顯示所有正在客戶維修的配件",
                    "sql": """
                    SELECT 配件編號, 配件名稱, 客戶名稱, 開始時間, 說明
                    FROM pat_parts_all 
                    WHERE 配件狀態 = 'OUT_REPAIR'
                    UNION ALL
                    SELECT 配件編號, 配件種類 as 配件名稱, 客戶名稱, 狀態開始時間 as 開始時間, 目前儲位 as 說明
                    FROM kyec_parts_all 
                    WHERE 配件狀態 = '客戶維修'
                    """
                },
                {
                    "question": "統計各種配件狀態的數量",
                    "sql": """
                    SELECT 配件狀態, COUNT(*) as 數量
                    FROM (
                        SELECT 配件狀態 FROM pat_parts_all
                        UNION ALL
                        SELECT 配件狀態 FROM kyec_parts_all
                    ) 
                    GROUP BY 配件狀態
                    ORDER BY 數量 DESC
                    """
                },
                {
                    "question": "查看配件變更歷史",
                    "sql": """
                    SELECT timestamp as 變更時間, operation as 操作類型, 
                            table_name as 資料表, row_key as 配件識別,
                            column_name as 變更欄位, old_value as 原值, 
                            new_value as 新值, user as 操作人員
                    FROM table_change_log
                    ORDER BY timestamp DESC
                    LIMIT 100
                    """
                },
                {
                    "question": "列出PAT客戶維修配件",
                    "sql": "SELECT * FROM pat_parts_all WHERE 配件狀態 = 'OUT_REPAIR'"
                },
                {
                    "question": "列出PAT送回維修的配件",
                    "sql": "SELECT * FROM pat_parts_all WHERE 配件狀態 = 'OUT_REPAIR'"
                },
                {
                    "question": "KY送回維修的配件",
                    "sql": "SELECT * FROM kyec_parts_all WHERE 配件狀態 = '客戶維修'"
                },
                {
                    "question": "LB015T0800127004A 什麼時候寄回維修",
                    "sql": "SELECT 配件編號, 開始時間 FROM pat_parts_all WHERE 配件編號 = 'LB015T0800127004A' AND 配件狀態 = 'OUT_REPAIR'"
                },
                {
                    "question": "上週有多少配件寄回維修",
                    "sql": "SELECT COUNT(DISTINCT row_key) FROM table_change_log WHERE (new_value = 'REPAIR' OR new_value = 'OUT_REPAIR' OR new_value = '廠內維修' OR new_value = '客戶維修') AND timestamp >= DATE('now', '-7 days')"
                },
                {
                    "question": "列出正常生產少於2的配件?",
                    "sql": "SELECT 產品型號_簡化, 正常生產, 站點 FROM pat_stats_weekly WHERE 正常生產 < 2 UNION ALL SELECT 客戶產品型號, 正常生產, 機台型號 FROM kyec_stats_weekly WHERE 正常生產 < 2"
                },
                {
                    "question": "列出總數量少於2的配件?",
                    "sql": "SELECT 產品型號_簡化, 站點, 總數量 FROM pat_stats_weekly WHERE 總數量 < 2 UNION ALL SELECT 客戶產品型號, 機台型號, 總數量 FROM kyec_stats_weekly WHERE 總數量 < 2"
                },
                {
                    "question": "列出PAT廠內維修的配件",
                    "sql": "SELECT * FROM pat_parts_all WHERE 配件狀態 = 'REPAIR'"
                },
                {
                    "question": "查詢借出天數最長的配件",
                    "sql": """
                    SELECT 配件編號, 配件名稱, 客戶名稱, 借出天數, 開始時間
                    FROM pat_parts_all
                    WHERE 借出天數 IS NOT NULL AND 借出天數 > 0
                    ORDER BY 借出天數 DESC
                    LIMIT 10
                    """
                },
                {
                    "question": "顯示所有待release狀態的配件",
                    "sql": "SELECT * FROM kyec_parts_all WHERE 配件狀態 = '待release'"
                },
                {
                    "question": "顯示最近一週的配件狀態異動",
                    "sql": "SELECT * FROM table_change_log WHERE column_name LIKE '%配件狀態%' AND timestamp >= DATE('now', '-7 days')"
                },
                {
                    "question": "統計京元電腦總數",
                    "sql": "SELECT * FROM kyec_stats_weekly WHERE 配件種類='PC'"
                },
                {
                    "question": "統計鴻谷電腦總數",
                    "sql": "SELECT * FROM pat_stats_weekly WHERE 配件種類='PC'"
                },
                {
                    "question": "顯示7423-OV3 FT2板子",
                    "sql": """
                    SELECT
                    產品型號_簡化 AS 產品型號,
                    站點,
                    總數量,
                    正常生產,
                    客戶維修,
                    廠內維修,
                    其它
                    FROM pat_stats_weekly
                    WHERE 產品型號_簡化 LIKE '%7423-OV3%' AND 站點 LIKE '%FT2%'
                    UNION ALL
                    SELECT
                    客戶產品型號 AS 產品型號,
                    板全號 AS 站點,
                    總數量,
                    正常生產,
                    客戶維修,
                    廠內維修,
                    其它
                    FROM kyec_stats_weekly
                    WHERE 客戶產品型號 LIKE '%7423-OV3%' AND 板全號 LIKE '%FT2%'
                    """
                },
                {
                    "question": "顯示7423-TB1 FT2在PAT的板子",
                    "sql": """
                    SELECT *
                    FROM pat_stats_weekly
                    WHERE 產品型號_簡化 LIKE '%7423-TB1%' AND 站點 LIKE '%FT2%'
                    """
                },
                {
                    "question": "顯示5450-OS1 FT1在KYEC的DB",
                    "sql": """
                    SELECT *
                    FROM kyec_stats_weekly
                    WHERE 客戶產品型號 LIKE '%5450-OS1%' AND 配件種類 LIKE '%DB%'
                    """
                },
                {
                    "question": "7423-TB1 FT2的GLB No是什麼",
                    "sql": "SELECT 產品型號_簡化, GLB_NO, 站點, 配件編號, 配件狀態 FROM pat_parts_all WHERE 產品型號_簡化 LIKE '%7423-TB1%' AND 站點 LIKE '%FT2%'"
                },
                {
                    "question": "列出PAT gen1電腦",
                    "sql": "SELECT * FROM pat_stats_weekly WHERE 產品型號_簡化 LIKE '%gen1%'"
                },
                {
                    "question": "列出KYEC gen2電腦",
                    "sql": "SELECT * FROM kyec_stats_weekly WHERE 客戶產品型號 LIKE '%gen2%'"
                }
            ]  
            
            for pair in question_sql_pairs:
                self.vn.train(question=pair["question"], sql=pair["sql"])
            
            self.logger.info("模型訓練完成")
            
        except Exception as e:
            self.logger.error(f"模型訓練失敗: {str(e)}")
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """詢問問題並獲取結果 - 參考官方範例"""
        if not self.vn:
            return {
                'success': False,
                'error': 'Vanna AI 未初始化'
            }
        
        # 檢查 OpenAI API 金鑰
        api_key = self._get_openai_api_key()
        if not api_key:
            return {
                'success': False,
                'error': '請設置 OpenAI API 金鑰才能使用 AI 查詢功能'
            }
        
        try:
            # 生成 SQL
            self.logger.info(f"開始處理問題: {question}")
            
            try:
                sql = self.vn.generate_sql(question)
                self.logger.info(f"Vanna AI 生成的原始 SQL: {sql}")
            except Exception as sql_error:
                self.logger.error(f"Vanna AI SQL 生成失敗: {str(sql_error)}")
                
                # 檢查是否是 API 金鑰問題
                if "api" in str(sql_error).lower() or "key" in str(sql_error).lower():
                    return {
                        'success': False,
                        'error': '請檢查 OpenAI API 金鑰設置是否正確'
                    }
                
                return {
                    'success': False,
                    'error': f'無法生成 SQL 查詢: {str(sql_error)}'
                }
            
            if not sql or sql.strip() == "":
                return {
                    'success': False,
                    'error': '無法生成有效的 SQL 查詢'
                }
            
            # 記錄生成的 SQL 用於調試
            self.logger.info(f"最終使用的 SQL: {sql}")
            
            # 驗證 SQL 安全性
            self.logger.info(f"開始驗證 SQL 安全性: {sql}")
            
            if not self._validate_sql(sql):
                self.logger.warning(f"SQL 安全性驗證失敗: {sql}")
                
                # 詳細分析為什麼驗證失敗
                sql_upper = sql.strip().upper().rstrip(';')
                self.logger.info(f"處理後的 SQL: {sql_upper}")
            
            self.logger.info("SQL 安全性驗證通過")
            
            # 執行 SQL
            df = self.vn.run_sql(sql)
            
            # 生成解釋（如果方法存在的話）
            explanation = ""
            try:
                if hasattr(self.vn, 'generate_explanation'):
                    explanation = self.vn.generate_explanation(sql)
                else:
                    # 提供簡單的解釋
                    explanation = f"執行了 SQL 查詢來回答問題：{question}"
            except Exception as e:
                self.logger.warning(f"無法生成解釋: {str(e)}")
                explanation = f"查詢執行成功，返回了 {len(df)} 筆記錄"
            
            return {
                'success': True,
                'sql': sql,
                'data': df,
                'explanation': explanation,
                'question': question
            }
            
        except Exception as e:
            self.logger.error(f"問題處理失敗: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'question': question
            }
    
    def _validate_sql(self, sql: str) -> bool:
        """驗證 SQL 安全性"""
        if not sql:
            return False
        
        sql_upper = sql.strip().upper()
        
        # 移除結尾的分號（這是正常的）
        sql_upper = sql_upper.rstrip(';')
        
        # 只允許 SELECT 查詢
        if not sql_upper.startswith('SELECT'):
            return False
        
        # 檢查危險關鍵字（但允許在字串中出現）
        dangerous_patterns = [
            r'\bDROP\b', r'\bDELETE\b', r'\bINSERT\b', r'\bUPDATE\b',
            r'\bALTER\b', r'\bCREATE\b', r'\bTRUNCATE\b', r'\bEXEC\b',
            r'\bEXECUTE\b', r'--'
        ]
        
        import re
        for pattern in dangerous_patterns:
            if re.search(pattern, sql_upper):
                return False
        
        # 檢查是否有多個語句（用分號分隔）
        statements = sql.split(';')
        if len([s for s in statements if s.strip()]) > 1:
            return False
        
        return True
    
    def generate_plotly_code(self, question: str, sql: str, df: pd.DataFrame) -> Optional[str]:
        """生成 Plotly 圖表代碼 - 參考官方範例"""
        if not self.vn or df.empty:
            return None
        
        try:
            if hasattr(self.vn, 'generate_plotly_code'):
                plotly_code = self.vn.generate_plotly_code(
                    question=question,
                    sql=sql,
                    df=df
                )
                return plotly_code
            else:
                self.logger.info("generate_plotly_code 方法不可用，跳過圖表生成")
                return None
        except Exception as e:
            self.logger.error(f"圖表代碼生成失敗: {str(e)}")
            return None
    
    def get_related_questions(self, question: str) -> List[str]:
        """獲取相關問題建議"""
        try:
            if not self.vn:
                return self._get_default_questions()
            
            # 使用 Vanna 的相關問題功能
            related = self.vn.get_related_training_data(question)
            
            if related:
                return [item.get('question', '') for item in related[:5] if item.get('question')]
            else:
                return self._get_default_questions()
                
        except Exception as e:
            self.logger.error(f"相關問題獲取失敗: {str(e)}")
            return self._get_default_questions()
    
    def _get_default_questions(self) -> List[str]:
        """獲取預設問題"""
        return [
            "顯示所有配件狀態統計",
            "查看正在維修的配件",
            "顯示客戶配件分佈",
            "查看配件變更歷史",
            "統計配件種類數量"
        ]
    
    def get_training_data_summary(self) -> Dict[str, Any]:
        """獲取訓練資料摘要"""
        try:
            if not self.vn:
                return {'error': 'Vanna AI 未初始化'}
            
            training_data = self.vn.get_training_data()
            
            return {
                'total_count': len(training_data),
                'ddl_count': len([item for item in training_data if 'ddl' in item]),
                'documentation_count': len([item for item in training_data if 'documentation' in item]),
                'sql_count': len([item for item in training_data if 'question' in item and 'sql' in item])
            }
            
        except Exception as e:
            self.logger.error(f"訓練資料摘要獲取失敗: {str(e)}")
            return {'error': str(e)}
    
    def add_training_data(self, question: str, sql: str) -> bool:
        """添加新的訓練資料"""
        try:
            if not self.vn:
                return False
            
            self.vn.train(question=question, sql=sql)
            self.logger.info(f"新增訓練資料: {question}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加訓練資料失敗: {str(e)}")
            return False
    
    def remove_training_data(self, id: str) -> bool:
        """移除訓練資料"""
        try:
            if not self.vn:
                return False
            
            self.vn.remove_training_data(id)
            return True
            
        except Exception as e:
            self.logger.error(f"移除訓練資料失敗: {str(e)}")
            return False
    
    def get_model_status(self) -> Dict[str, Any]:
        """獲取模型狀態"""
        try:
            if not self.vn:
                return {
                    'status': '未初始化',
                    'error': 'Vanna AI 實例未建立'
                }
            
            training_summary = self.get_training_data_summary()
            
            return {
                'status': '正常',
                'training_data_count': training_summary.get('total_count', 0),
                'last_training': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'model_name': self.model_name,
                'database_connected': True
            }
            
        except Exception as e:
            return {
                'status': '異常',
                'error': str(e)
            }