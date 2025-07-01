import sqlite3
import pandas as pd
import requests
import os
from datetime import datetime, timedelta
import streamlit as st
from typing import Optional, Dict, List, Any
import logging

class DatabaseManager:
    """資料庫管理類別，負責資料庫連接、查詢和同步"""
    
    def __init__(self):
        self.db_path = "tooling_data.db"
        self.github_db_url = "https://github.com/username/repo/raw/main/tooling_data.db"  # 需要替換為實際 URL
        self.cache_duration = 3600  # 1小時快取
        self.last_download_time = None
        
        # 設置日誌
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 初始化資料庫
        self._initialize_database()
    
    def _initialize_database(self):
        """初始化資料庫連接"""
        try:
            if not os.path.exists(self.db_path):
                self._download_database()
            elif self._should_update_database():
                self._download_database()
        except Exception as e:
            self.logger.error(f"資料庫初始化失敗: {str(e)}")
    
    def _should_update_database(self) -> bool:
        """檢查是否需要更新資料庫"""
        if not self.last_download_time:
            return True
        
        time_diff = datetime.now() - self.last_download_time
        return time_diff.total_seconds() > self.cache_duration
    
    def _download_database(self) -> bool:
        """從 GitHub 下載最新資料庫"""
        try:
            # 如果是本地開發環境，直接使用現有資料庫
            if os.path.exists(self.db_path):
                self.logger.info("使用本地資料庫文件")
                self.last_download_time = datetime.now()
                return True
            
            # 在生產環境中從 GitHub 下載
            self.logger.info("正在從 GitHub 下載資料庫...")
            response = requests.get(self.github_db_url, timeout=30)
            response.raise_for_status()
            
            with open(self.db_path, 'wb') as f:
                f.write(response.content)
            
            self.last_download_time = datetime.now()
            self.logger.info("資料庫下載成功")
            return True
            
        except Exception as e:
            self.logger.error(f"資料庫下載失敗: {str(e)}")
            return False
    
    def check_database_connection(self) -> bool:
        """檢查資料庫連接狀態"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            
            # 檢查必要的資料表是否存在
            required_tables = ['pat_parts_all', 'kyec_parts_all', 'pat_stats_weekly', 'kyec_stats_weekly', 'table_change_log']
            existing_tables = [table[0] for table in tables]
            
            for table in required_tables:
                if table not in existing_tables:
                    self.logger.warning(f"缺少必要資料表: {table}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"資料庫連接檢查失敗: {str(e)}")
            return False
    
    def get_last_update_time(self) -> Optional[str]:
        """獲取資料庫最後更新時間"""
        try:
            if os.path.exists(self.db_path):
                mtime = os.path.getmtime(self.db_path)
                return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            return None
        except Exception as e:
            self.logger.error(f"獲取更新時間失敗: {str(e)}")
            return None
    
    def execute_query(self, query: str, params: tuple = None) -> pd.DataFrame:
        """執行 SQL 查詢並返回 DataFrame"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            if params:
                df = pd.read_sql_query(query, conn, params=params)
            else:
                df = pd.read_sql_query(query, conn)
            
            conn.close()
            return df
            
        except Exception as e:
            self.logger.error(f"查詢執行失敗: {str(e)}")
            return pd.DataFrame()
    
    
    def get_overview_statistics(self) -> Dict[str, int]:
        """獲取總覽統計資訊"""
        try:
            stats = {}
            
            # 總配件數
            total_query = """
                SELECT COUNT(*) as count FROM (
                    SELECT 配件編號 FROM pat_parts_all
                    UNION ALL
                    SELECT 配件編號 FROM kyec_parts_all
                )
            """
            total_result = self.execute_query(total_query)
            stats['total_parts'] = total_result['count'].iloc[0] if not total_result.empty else 0
            
            # 維修中配件
            repair_query = """
                SELECT COUNT(*) as count FROM (
                    SELECT 配件編號 FROM pat_parts_all WHERE 配件狀態 IN ('OUT_REPAIR', 'REPAIR')
                    UNION ALL
                    SELECT 配件編號 FROM kyec_parts_all WHERE 配件狀態 IN ('客戶維修', '廠內維修')
                )
            """
            repair_result = self.execute_query(repair_query)
            stats['repair_parts'] = repair_result['count'].iloc[0] if not repair_result.empty else 0
            
            # 正常生產配件
            normal_query = """
                SELECT COUNT(*) as count FROM (
                    SELECT 配件編號 FROM pat_parts_all WHERE 配件狀態 = 'PRODUCTION'
                    UNION ALL
                    SELECT 配件編號 FROM kyec_parts_all WHERE 配件狀態 = '正常生產'
                )
            """
            normal_result = self.execute_query(normal_query)
            stats['normal_parts'] = normal_result['count'].iloc[0] if not normal_result.empty else 0
            
            # 客戶借出配件
            borrowed_query = """
                SELECT COUNT(*) as count FROM (
                    SELECT 配件編號 FROM pat_parts_all WHERE 配件狀態 = 'BORROW'
                    UNION ALL
                    SELECT 配件編號 FROM kyec_parts_all WHERE 配件狀態 = '客戶借出'
                )
            """
            borrowed_result = self.execute_query(borrowed_query)
            stats['borrowed_parts'] = borrowed_result['count'].iloc[0] if not borrowed_result.empty else 0
            
            return stats
            
        except Exception as e:
            self.logger.error(f"總覽統計獲取失敗: {str(e)}")
            return {}
    
    def get_pat_status_distribution(self) -> pd.DataFrame:
        """獲取 PAT 配件狀態分佈"""
        query = """
            SELECT 配件狀態, COUNT(*) as 數量
            FROM pat_parts_all
            GROUP BY 配件狀態
            ORDER BY 數量 DESC
        """
        return self.execute_query(query)
    
    def get_kyec_status_distribution(self) -> pd.DataFrame:
        """獲取 KYEC 配件狀態分佈"""
        query = """
            SELECT 配件狀態, COUNT(*) as 數量
            FROM kyec_parts_all
            GROUP BY 配件狀態
            ORDER BY 數量 DESC
        """
        return self.execute_query(query)
    
    def get_status_trend_data(self) -> pd.DataFrame:
        """獲取狀態趨勢資料"""
        try:
            # 從週統計表獲取趨勢資料
            query = """
                SELECT 每周狀態 as 日期, '正常生產' as 狀態, SUM(正常生產) as 數量
                FROM pat_stats_weekly
                GROUP BY 每周狀態
                UNION ALL
                SELECT 每周狀態 as 日期, '廠內維修' as 狀態, SUM(廠內維修) as 數量
                FROM pat_stats_weekly
                GROUP BY 每周狀態
                UNION ALL
                SELECT 每周狀態 as 日期, '客戶維修' as 狀態, SUM(客戶維修) as 數量
                FROM pat_stats_weekly
                GROUP BY 每周狀態
                ORDER BY 日期
            """
            return self.execute_query(query)
        except Exception as e:
            self.logger.error(f"趨勢資料獲取失敗: {str(e)}")
            return pd.DataFrame()
    
    def get_detailed_pat_statistics(self) -> pd.DataFrame:
        """獲取 PAT 詳細統計"""
        query = """
            SELECT 
                配件種類,
                COUNT(*) as 總數量,
                SUM(CASE WHEN 配件狀態 = 'PRODUCTION' THEN 1 ELSE 0 END) as 正常生產,
                SUM(CASE WHEN 配件狀態 = 'REPAIR' THEN 1 ELSE 0 END) as 廠內維修,
                SUM(CASE WHEN 配件狀態 = 'OUT_REPAIR' THEN 1 ELSE 0 END) as 客戶維修,
                SUM(CASE WHEN 配件狀態 = 'BORROW' THEN 1 ELSE 0 END) as 客戶借出
            FROM pat_parts_all
            GROUP BY 配件種類
            ORDER BY 總數量 DESC
        """
        return self.execute_query(query)
    
    def get_detailed_kyec_statistics(self) -> pd.DataFrame:
        """獲取 KYEC 詳細統計"""
        query = """
            SELECT 
                配件種類,
                COUNT(*) as 總數量,
                SUM(CASE WHEN 配件狀態 = '正常生產' THEN 1 ELSE 0 END) as 正常生產,
                SUM(CASE WHEN 配件狀態 = '廠內維修' THEN 1 ELSE 0 END) as 廠內維修,
                SUM(CASE WHEN 配件狀態 = '客戶維修' THEN 1 ELSE 0 END) as 客戶維修,
                SUM(CASE WHEN 配件狀態 = '客戶借出' THEN 1 ELSE 0 END) as 客戶借出
            FROM kyec_parts_all
            GROUP BY 配件種類
            ORDER BY 總數量 DESC
        """
        return self.execute_query(query)
    
    def get_customer_statistics(self) -> pd.DataFrame:
        """獲取客戶統計資料"""
        query = """
            SELECT 
                客戶名稱,
                COUNT(*) as 配件數量,
                SUM(CASE WHEN 配件狀態 LIKE '%維修%' THEN 1 ELSE 0 END) as 維修中配件,
                SUM(CASE WHEN 配件狀態 LIKE '%借出%' THEN 1 ELSE 0 END) as 借出配件
            FROM (
                SELECT 客戶名稱, 配件狀態 FROM pat_parts_all
                UNION ALL
                SELECT 客戶名稱, 配件狀態 FROM kyec_parts_all
            )
            GROUP BY 客戶名稱
            ORDER BY 配件數量 DESC
        """
        return self.execute_query(query)
    
    def get_trend_analysis(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """獲取指定時間範圍的趨勢分析"""
        try:
            # 由於週統計表的日期格式可能不標準，這裡提供一個基本的查詢
            query = """
                SELECT 
                    每周狀態 as 日期,
                    '正常生產' as 狀態,
                    SUM(正常生產) as 數量
                FROM pat_stats_weekly
                GROUP BY 每周狀態
                UNION ALL
                SELECT 
                    每周狀態 as 日期,
                    '廠內維修' as 狀態,
                    SUM(廠內維修) as 數量
                FROM pat_stats_weekly
                GROUP BY 每周狀態
                ORDER BY 日期
            """
            return self.execute_query(query)
        except Exception as e:
            self.logger.error(f"趨勢分析獲取失敗: {str(e)}")
            return pd.DataFrame()
    
    def get_maintenance_cycle_data(self) -> pd.DataFrame:
        """獲取維修週期資料"""
        query = """
            SELECT 
                配件編號,
                配件名稱,
                維修天數,
                開始時間
            FROM pat_parts_all
            WHERE 維修天數 IS NOT NULL AND 維修天數 > 0
            ORDER BY 維修天數 DESC
        """
        return self.execute_query(query)
    
    def get_change_logs(self, table_filter: str = "全部", operation_filter: str = "全部", 
                       days_filter: str = "全部", search_term: str = "") -> pd.DataFrame:
        """獲取變更紀錄"""
        try:
            query = "SELECT * FROM table_change_log WHERE 1=1"
            params = []
            
            # 資料表篩選
            if table_filter != "全部":
                query += " AND table_name = ?"
                params.append(table_filter)
            
            # 操作類型篩選
            if operation_filter != "全部":
                query += " AND operation = ?"
                params.append(operation_filter)
            
            # 時間範圍篩選
            if days_filter != "全部":
                days_map = {"最近7天": 7, "最近30天": 30, "最近90天": 90}
                if days_filter in days_map:
                    days = days_map[days_filter]
                    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
                    query += " AND DATE(timestamp) >= ?"
                    params.append(cutoff_date)
            
            # 搜尋條件
            if search_term:
                query += " AND (row_key LIKE ? OR old_value LIKE ? OR new_value LIKE ?)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern, search_pattern])
            
            query += " ORDER BY timestamp DESC LIMIT 1000"
            
            df = self.execute_query(query, tuple(params) if params else None)
            
            # 轉換時間戳格式
            if not df.empty and 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            return df
            
        except Exception as e:
            self.logger.error(f"變更紀錄獲取失敗: {str(e)}")
            return pd.DataFrame()
    
    def get_available_columns(self, tables: List[str]) -> List[str]:
        """獲取指定資料表的可用欄位"""
        try:
            columns = set()
            
            for table in tables:
                query = f"PRAGMA table_info({table})"
                result = self.execute_query(query)
                if not result.empty:
                    table_columns = result['name'].tolist()
                    columns.update(table_columns)
            
            return sorted(list(columns))
            
        except Exception as e:
            self.logger.error(f"欄位資訊獲取失敗: {str(e)}")
            return []
    
    def get_database_info(self) -> Dict[str, Any]:
        """獲取資料庫資訊"""
        try:
            info = {}
            
            # 資料庫大小
            if os.path.exists(self.db_path):
                size_bytes = os.path.getsize(self.db_path)
                size_mb = round(size_bytes / (1024 * 1024), 2)
                info['資料庫大小'] = f"{size_mb} MB"
            
            # 資料表數量
            tables_query = "SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'"
            tables_result = self.execute_query(tables_query)
            info['資料表數量'] = tables_result['count'].iloc[0] if not tables_result.empty else 0
            
            # 最後修改時間
            info['最後修改時間'] = self.get_last_update_time()
            
            return info
            
        except Exception as e:
            self.logger.error(f"資料庫資訊獲取失敗: {str(e)}")
            return {}
    
    def get_last_sync_time(self) -> str:
        """獲取最後同步時間"""
        if self.last_download_time:
            return self.last_download_time.strftime("%Y-%m-%d %H:%M:%S")
        return "未知"
    
    def manual_sync(self) -> bool:
        """手動同步資料庫"""
        try:
            return self._download_database()
        except Exception as e:
            self.logger.error(f"手動同步失敗: {str(e)}")
            return False
    
    def validate_sql_query(self, query: str) -> bool:
        """驗證 SQL 查詢的安全性"""
        if not query:
            return False
        
        # 移除結尾的分號（這是正常的）
        query_cleaned = query.strip().rstrip(';')
        query_upper = query_cleaned.upper()
        
        # 只允許 SELECT 查詢
        if not query_upper.startswith('SELECT'):
            return False
        
        # 使用正則表達式檢查危險關鍵字（但允許在字串中出現）
        import re
        dangerous_patterns = [
            r'\bDROP\b', r'\bDELETE\b', r'\bINSERT\b', r'\bUPDATE\b',
            r'\bALTER\b', r'\bCREATE\b', r'\bTRUNCATE\b', r'\bEXEC\b',
            r'\bEXECUTE\b', r'--'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query_upper):
                return False
        
        # 檢查是否有多個語句（用分號分隔）
        statements = query.split(';')
        if len([s for s in statements if s.strip()]) > 1:
            return False
        
        # UNION 查詢是允許的，但要檢查是否安全
        if 'UNION' in query_upper:
            # 確保 UNION 後面也是 SELECT
            union_parts = re.split(r'\bUNION\s+(?:ALL\s+)?', query_upper)
            for part in union_parts:
                part = part.strip()
                if part and not part.startswith('SELECT'):
                    return False
        
        return True
    
    def execute_safe_query(self, query: str) -> pd.DataFrame:
        """執行安全的查詢（僅允許 SELECT）"""
        if not self.validate_sql_query(query):
            raise ValueError("查詢包含不安全的 SQL 語句")
        
        if not query.strip().upper().startswith('SELECT'):
            raise ValueError("僅允許 SELECT 查詢")
        
        return self.execute_query(query)