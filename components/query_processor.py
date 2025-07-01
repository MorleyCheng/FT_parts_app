import pandas as pd
import sqlite3
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta

class QueryProcessor:
    """查詢處理器 - 處理複雜查詢和資料分析"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_path = "tooling_data.db"
    
    def execute_query(self, sql: str, params: tuple = None) -> pd.DataFrame:
        """執行 SQL 查詢"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            if params:
                df = pd.read_sql_query(sql, conn, params=params)
            else:
                df = pd.read_sql_query(sql, conn)
            
            conn.close()
            return df
            
        except Exception as e:
            self.logger.error(f"查詢執行失敗: {str(e)}")
            return pd.DataFrame()
    
    def get_parts_status_analysis(self) -> Dict[str, pd.DataFrame]:
        """獲取配件狀態分析"""
        try:
            analysis = {}
            
            # PAT 配件狀態統計
            pat_query = """
                SELECT 
                    配件狀態,
                    COUNT(*) as 數量,
                    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM pat_parts_all), 2) as 百分比
                FROM pat_parts_all
                GROUP BY 配件狀態
                ORDER BY 數量 DESC
            """
            analysis['pat_status'] = self.execute_query(pat_query)
            
            # KYEC 配件狀態統計
            kyec_query = """
                SELECT 
                    配件狀態,
                    COUNT(*) as 數量,
                    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM kyec_parts_all), 2) as 百分比
                FROM kyec_parts_all
                GROUP BY 配件狀態
                ORDER BY 數量 DESC
            """
            analysis['kyec_status'] = self.execute_query(kyec_query)
            
            # 綜合狀態統計
            combined_query = """
                SELECT 
                    配件狀態,
                    COUNT(*) as 數量,
                    '綜合' as 來源
                FROM (
                    SELECT 配件狀態 FROM pat_parts_all
                    UNION ALL
                    SELECT 配件狀態 FROM kyec_parts_all
                )
                GROUP BY 配件狀態
                ORDER BY 數量 DESC
            """
            analysis['combined_status'] = self.execute_query(combined_query)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"配件狀態分析失敗: {str(e)}")
            return {}
    
    def get_customer_analysis(self) -> Dict[str, pd.DataFrame]:
        """獲取客戶分析"""
        try:
            analysis = {}
            
            # 客戶配件統計
            customer_query = """
                SELECT 
                    客戶名稱,
                    COUNT(*) as 配件總數,
                    SUM(CASE WHEN 配件狀態 LIKE '%維修%' OR 配件狀態 LIKE '%REPAIR%' THEN 1 ELSE 0 END) as 維修中配件,
                    SUM(CASE WHEN 配件狀態 LIKE '%借出%' OR 配件狀態 = 'BORROW' THEN 1 ELSE 0 END) as 借出配件,
                    SUM(CASE WHEN 配件狀態 = '正常生產' OR 配件狀態 = 'PRODUCTION' THEN 1 ELSE 0 END) as 正常配件
                FROM (
                    SELECT 客戶名稱, 配件狀態 FROM pat_parts_all WHERE 客戶名稱 IS NOT NULL
                    UNION ALL
                    SELECT 客戶名稱, 配件狀態 FROM kyec_parts_all WHERE 客戶名稱 IS NOT NULL
                )
                GROUP BY 客戶名稱
                ORDER BY 配件總數 DESC
            """
            analysis['customer_stats'] = self.execute_query(customer_query)
            
            # 客戶維修率分析
            repair_rate_query = """
                SELECT 
                    客戶名稱,
                    配件總數,
                    維修中配件,
                    ROUND(維修中配件 * 100.0 / 配件總數, 2) as 維修率
                FROM (
                    SELECT 
                        客戶名稱,
                        COUNT(*) as 配件總數,
                        SUM(CASE WHEN 配件狀態 LIKE '%維修%' OR 配件狀態 LIKE '%REPAIR%' THEN 1 ELSE 0 END) as 維修中配件
                    FROM (
                        SELECT 客戶名稱, 配件狀態 FROM pat_parts_all WHERE 客戶名稱 IS NOT NULL
                        UNION ALL
                        SELECT 客戶名稱, 配件狀態 FROM kyec_parts_all WHERE 客戶名稱 IS NOT NULL
                    )
                    GROUP BY 客戶名稱
                    HAVING 配件總數 >= 5
                )
                ORDER BY 維修率 DESC
            """
            analysis['repair_rate'] = self.execute_query(repair_rate_query)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"客戶分析失敗: {str(e)}")
            return {}
    
    def get_maintenance_analysis(self) -> Dict[str, pd.DataFrame]:
        """獲取維修分析"""
        try:
            analysis = {}
            
            # 維修週期分析
            maintenance_cycle_query = """
                SELECT 
                    配件編號,
                    配件名稱,
                    客戶名稱,
                    維修天數,
                    開始時間,
                    說明,
                    CASE 
                        WHEN 維修天數 <= 7 THEN '短期維修'
                        WHEN 維修天數 <= 30 THEN '中期維修'
                        ELSE '長期維修'
                    END as 維修類型
                FROM pat_parts_all
                WHERE 維修天數 IS NOT NULL AND 維修天數 > 0
                ORDER BY 維修天數 DESC
            """
            analysis['maintenance_cycle'] = self.execute_query(maintenance_cycle_query)
            
            # 維修統計摘要
            maintenance_summary_query = """
                SELECT 
                    COUNT(*) as 總維修配件數,
                    AVG(維修天數) as 平均維修天數,
                    MIN(維修天數) as 最短維修天數,
                    MAX(維修天數) as 最長維修天數,
                    SUM(CASE WHEN 維修天數 <= 7 THEN 1 ELSE 0 END) as 短期維修數,
                    SUM(CASE WHEN 維修天數 > 7 AND 維修天數 <= 30 THEN 1 ELSE 0 END) as 中期維修數,
                    SUM(CASE WHEN 維修天數 > 30 THEN 1 ELSE 0 END) as 長期維修數
                FROM pat_parts_all
                WHERE 維修天數 IS NOT NULL AND 維修天數 > 0
            """
            analysis['maintenance_summary'] = self.execute_query(maintenance_summary_query)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"維修分析失敗: {str(e)}")
            return {}
    
    def get_trend_analysis(self, days: int = 30) -> Dict[str, pd.DataFrame]:
        """獲取趨勢分析"""
        try:
            analysis = {}
            
            # 從週統計表獲取趨勢
            trend_query = """
                SELECT 
                    每周狀態 as 時間週期,
                    SUM(總數量) as 總配件數,
                    SUM(正常生產) as 正常生產數,
                    SUM(廠內維修) as 廠內維修數,
                    SUM(客戶維修) as 客戶維修數,
                    SUM(客戶借出) as 客戶借出數,
                    ROUND(SUM(客戶維修) * 100.0 / SUM(總數量), 2) as 客戶維修率,
                    ROUND(SUM(廠內維修) * 100.0 / SUM(總數量), 2) as 廠內維修率
                FROM (
                    SELECT 每周狀態, 總數量, 正常生產, 廠內維修, 客戶維修, 客戶借出, 0 as 待release, 其它
                    FROM pat_stats_weekly
                    UNION ALL
                    SELECT 每周狀態, 總數量, 正常生產, 廠內維修, 客戶維修, 客戶借出, 待release, 其它
                    FROM kyec_stats_weekly
                )
                GROUP BY 每周狀態
                ORDER BY 時間週期
            """
            analysis['weekly_trend'] = self.execute_query(trend_query)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"趨勢分析失敗: {str(e)}")
            return {}
    
    def get_change_log_analysis(self, days: int = 30) -> Dict[str, pd.DataFrame]:
        """獲取變更記錄分析"""
        try:
            analysis = {}
            
            # 最近變更統計
            recent_changes_query = """
                SELECT 
                    DATE(timestamp) as 變更日期,
                    operation as 操作類型,
                    COUNT(*) as 變更次數
                FROM table_change_log
                WHERE DATE(timestamp) >= date('now', '-{} days')
                GROUP BY DATE(timestamp), operation
                ORDER BY 變更日期 DESC, 變更次數 DESC
            """.format(days)
            analysis['recent_changes'] = self.execute_query(recent_changes_query)
            
            # 操作人員統計
            user_activity_query = """
                SELECT 
                    user as 操作人員,
                    COUNT(*) as 操作次數,
                    COUNT(DISTINCT DATE(timestamp)) as 活躍天數,
                    MIN(timestamp) as 首次操作,
                    MAX(timestamp) as 最後操作
                FROM table_change_log
                WHERE DATE(timestamp) >= date('now', '-{} days')
                AND user IS NOT NULL
                GROUP BY user
                ORDER BY 操作次數 DESC
            """.format(days)
            analysis['user_activity'] = self.execute_query(user_activity_query)
            
            # 變更頻率分析
            change_frequency_query = """
                SELECT 
                    table_name as 資料表,
                    operation as 操作類型,
                    COUNT(*) as 變更次數,
                    COUNT(DISTINCT row_key) as 影響配件數
                FROM table_change_log
                WHERE DATE(timestamp) >= date('now', '-{} days')
                GROUP BY table_name, operation
                ORDER BY 變更次數 DESC
            """.format(days)
            analysis['change_frequency'] = self.execute_query(change_frequency_query)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"變更記錄分析失敗: {str(e)}")
            return {}
    
    def get_parts_type_analysis(self) -> Dict[str, pd.DataFrame]:
        """獲取配件種類分析"""
        try:
            analysis = {}
            
            # PAT 配件種類統計
            pat_type_query = """
                SELECT 
                    配件種類,
                    COUNT(*) as 配件數量,
                    COUNT(DISTINCT 客戶名稱) as 客戶數量,
                    SUM(CASE WHEN 配件狀態 = 'PRODUCTION' THEN 1 ELSE 0 END) as 可用數量,
                    SUM(CASE WHEN 配件狀態 LIKE '%REPAIR%' THEN 1 ELSE 0 END) as 維修數量
                FROM pat_parts_all
                WHERE 配件種類 IS NOT NULL
                GROUP BY 配件種類
                ORDER BY 配件數量 DESC
            """
            analysis['pat_types'] = self.execute_query(pat_type_query)
            
            # KYEC 配件種類統計
            kyec_type_query = """
                SELECT 
                    配件種類,
                    COUNT(*) as 配件數量,
                    COUNT(DISTINCT 客戶名稱) as 客戶數量,
                    SUM(CASE WHEN 配件狀態 = '正常生產' THEN 1 ELSE 0 END) as 正常數量,
                    SUM(CASE WHEN 配件狀態 LIKE '%維修%' THEN 1 ELSE 0 END) as 維修數量
                FROM kyec_parts_all
                WHERE 配件種類 IS NOT NULL
                GROUP BY 配件種類
                ORDER BY 配件數量 DESC
            """
            analysis['kyec_types'] = self.execute_query(kyec_type_query)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"配件種類分析失敗: {str(e)}")
            return {}
    
    def search_parts(self, search_term: str, search_type: str = "all") -> pd.DataFrame:
        """搜尋配件"""
        try:
            if search_type == "pat":
                query = """
                    SELECT 配件編號, 配件名稱, 客戶名稱, 配件狀態, 站點, 配件種類, 開始時間
                    FROM pat_parts_all
                    WHERE 配件編號 LIKE ? OR 配件名稱 LIKE ? OR 客戶名稱 LIKE ?
                    ORDER BY 配件編號
                """
            elif search_type == "kyec":
                query = """
                    SELECT 配件編號, 板全號, 客戶名稱, 配件狀態, 配件種類, 機台型號, 狀態開始時間
                    FROM kyec_parts_all
                    WHERE 配件編號 LIKE ? OR 板全號 LIKE ? OR 客戶名稱 LIKE ?
                    ORDER BY 配件編號
                """
            else:  # all
                query = """
                    SELECT 配件編號, 配件名稱, 客戶名稱, 配件狀態, '站點' as 來源, 開始時間
                    FROM pat_parts_all
                    WHERE 配件編號 LIKE ? OR 配件名稱 LIKE ? OR 客戶名稱 LIKE ?
                    UNION ALL
                    SELECT 配件編號, 配件種類 as 配件名稱, 客戶名稱, 配件狀態, 'KYEC' as 來源, 狀態開始時間 as 開始時間
                    FROM kyec_parts_all
                    WHERE 配件編號 LIKE ? OR 配件種類 LIKE ? OR 客戶名稱 LIKE ?
                    ORDER BY 配件編號
                """
            
            search_pattern = f"%{search_term}%"
            params = (search_pattern, search_pattern, search_pattern)
            
            if search_type == "all":
                params = params + params  # 重複參數給 UNION 查詢
            
            return self.execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"配件搜尋失敗: {str(e)}")
            return pd.DataFrame()
    
    def get_parts_detail(self, part_id: str) -> Dict[str, Any]:
        """獲取配件詳細資訊"""
        try:
            detail = {}
            
            # 從 PAT 表查詢
            pat_query = """
                SELECT * FROM pat_parts_all WHERE 配件編號 = ?
            """
            pat_result = self.execute_query(pat_query, (part_id,))
            
            if not pat_result.empty:
                detail['pat_info'] = pat_result.iloc[0].to_dict()
            
            # 從 KYEC 表查詢
            kyec_query = """
                SELECT * FROM kyec_parts_all WHERE 配件編號 = ?
            """
            kyec_result = self.execute_query(kyec_query, (part_id,))
            
            if not kyec_result.empty:
                detail['kyec_info'] = kyec_result.iloc[0].to_dict()
            
            # 查詢變更歷史
            change_query = """
                SELECT timestamp, operation, column_name, old_value, new_value, user, note
                FROM table_change_log
                WHERE row_key LIKE ?
                ORDER BY timestamp DESC
                LIMIT 20
            """
            change_result = self.execute_query(change_query, (f"%{part_id}%",))
            detail['change_history'] = change_result
            
            return detail
            
        except Exception as e:
            self.logger.error(f"配件詳細資訊獲取失敗: {str(e)}")
            return {}
    
    def validate_query_safety(self, sql: str) -> bool:
        """驗證查詢安全性"""
        if not sql:
            return False
        
        # 移除結尾的分號（這是正常的）
        sql_cleaned = sql.strip().rstrip(';')
        sql_upper = sql_cleaned.upper()
        
        # 只允許 SELECT 查詢
        if not sql_upper.startswith('SELECT'):
            return False
        
        # 使用正則表達式檢查危險關鍵字（但允許在字串中出現）
        import re
        dangerous_patterns = [
            r'\bDROP\b', r'\bDELETE\b', r'\bINSERT\b', r'\bUPDATE\b',
            r'\bALTER\b', r'\bCREATE\b', r'\bTRUNCATE\b', r'\bEXEC\b',
            r'\bEXECUTE\b', r'--'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sql_upper):
                return False
        
        # 檢查是否有多個語句（用分號分隔）
        statements = sql.split(';')
        if len([s for s in statements if s.strip()]) > 1:
            return False
        
        # UNION 查詢是允許的，但要檢查是否安全
        if 'UNION' in sql_upper:
            # 確保 UNION 後面也是 SELECT
            union_parts = re.split(r'\bUNION\s+(?:ALL\s+)?', sql_upper)
            for part in union_parts:
                part = part.strip()
                if part and not part.startswith('SELECT'):
                    return False
        
        return True