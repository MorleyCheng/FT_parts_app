import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import logging
import re

def format_dataframe(df: pd.DataFrame, max_rows: int = 100) -> pd.DataFrame:
    """格式化 DataFrame 以便在 Streamlit 中顯示"""
    try:
        if df.empty:
            return df
        
        # 限制顯示行數
        if len(df) > max_rows:
            df = df.head(max_rows)
            st.info(f"顯示前 {max_rows} 筆資料，共 {len(df)} 筆")
        
        # 格式化日期時間欄位
        for col in df.columns:
            if df[col].dtype == 'object':
                # 嘗試轉換日期時間格式
                if any(keyword in col.lower() for keyword in ['時間', 'date', 'time', 'timestamp']):
                    try:
                        df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
        
        # 格式化數字欄位
        for col in df.columns:
            if df[col].dtype in ['float64', 'int64']:
                if '率' in col or '百分比' in col:
                    df[col] = df[col].round(2)
                elif '天數' in col:
                    df[col] = df[col].round(1)
        
        return df
        
    except Exception as e:
        logging.error(f"DataFrame 格式化失敗: {str(e)}")
        return df

def get_status_color(status: str) -> str:
    """根據配件狀態返回對應的顏色"""
    color_mapping = {
        '正常生產': '#28a745',
        'AVAILABLE': '#28a745',
        '廠內維修': '#ffc107',
        'IN_REPAIR': '#ffc107',
        '客戶維修': '#dc3545',
        'OUT_REPAIR': '#dc3545',
        '客戶借出': '#17a2b8',
        'BORROWED': '#17a2b8',
        '待release': '#6f42c1',
        '其它': '#6c757d'
    }
    
    return color_mapping.get(status, '#6c757d')

def format_number(number: Union[int, float], format_type: str = 'default') -> str:
    """格式化數字顯示"""
    try:
        if pd.isna(number):
            return "N/A"
        
        if format_type == 'percentage':
            return f"{number:.1f}%"
        elif format_type == 'currency':
            return f"${number:,.2f}"
        elif format_type == 'integer':
            return f"{int(number):,}"
        elif format_type == 'decimal':
            return f"{number:.2f}"
        else:
            if isinstance(number, float):
                return f"{number:.2f}"
            else:
                return f"{number:,}"
                
    except Exception as e:
        logging.error(f"數字格式化失敗: {str(e)}")
        return str(number)

def create_download_link(data: Union[pd.DataFrame, str, bytes], 
                        filename: str, 
                        link_text: str = "下載檔案") -> str:
    """建立下載連結"""
    try:
        if isinstance(data, pd.DataFrame):
            # DataFrame 轉 CSV
            csv_data = data.to_csv(index=False, encoding='utf-8-sig')
            return f'<a href="data:text/csv;charset=utf-8,{csv_data}" download="{filename}">{link_text}</a>'
        elif isinstance(data, str):
            # 文字資料
            return f'<a href="data:text/plain;charset=utf-8,{data}" download="{filename}">{link_text}</a>'
        elif isinstance(data, bytes):
            # 二進位資料
            import base64
            b64_data = base64.b64encode(data).decode()
            return f'<a href="data:application/octet-stream;base64,{b64_data}" download="{filename}">{link_text}</a>'
        else:
            return "不支援的資料格式"
            
    except Exception as e:
        logging.error(f"下載連結建立失敗: {str(e)}")
        return "下載連結建立失敗"

def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """驗證日期範圍"""
    try:
        if start_date > end_date:
            st.error("開始日期不能晚於結束日期")
            return False
        
        if (end_date - start_date).days > 365:
            st.warning("日期範圍超過一年，可能影響查詢效能")
        
        return True
        
    except Exception as e:
        logging.error(f"日期範圍驗證失敗: {str(e)}")
        return False

def clean_text(text: str) -> str:
    """清理文字內容"""
    try:
        if not isinstance(text, str):
            return str(text)
        
        # 移除多餘空格
        text = ' '.join(text.split())
        
        # 移除特殊字符（保留中文、英文、數字、基本標點）
        text = re.sub(r'[^\w\s\u4e00-\u9fff\-_.,!?()[\]{}]', '', text)
        
        return text.strip()
        
    except Exception as e:
        logging.error(f"文字清理失敗: {str(e)}")
        return str(text)

def parse_search_query(query: str) -> Dict[str, Any]:
    """解析搜尋查詢"""
    try:
        parsed = {
            'keywords': [],
            'filters': {},
            'operators': []
        }
        
        # 提取關鍵字
        keywords = re.findall(r'\b\w+\b', query)
        parsed['keywords'] = [kw for kw in keywords if len(kw) > 1]
        
        # 提取篩選條件（例如：status:維修）
        filters = re.findall(r'(\w+):([^\s]+)', query)
        for key, value in filters:
            parsed['filters'][key] = value
        
        # 提取邏輯運算子
        operators = re.findall(r'\b(AND|OR|NOT)\b', query.upper())
        parsed['operators'] = operators
        
        return parsed
        
    except Exception as e:
        logging.error(f"搜尋查詢解析失敗: {str(e)}")
        return {'keywords': [query], 'filters': {}, 'operators': []}

def calculate_statistics(data: pd.DataFrame, column: str) -> Dict[str, float]:
    """計算統計資訊"""
    try:
        if data.empty or column not in data.columns:
            return {}
        
        numeric_data = pd.to_numeric(data[column], errors='coerce').dropna()
        
        if numeric_data.empty:
            return {}
        
        stats = {
            'count': len(numeric_data),
            'mean': numeric_data.mean(),
            'median': numeric_data.median(),
            'std': numeric_data.std(),
            'min': numeric_data.min(),
            'max': numeric_data.max(),
            'q25': numeric_data.quantile(0.25),
            'q75': numeric_data.quantile(0.75)
        }
        
        return stats
        
    except Exception as e:
        logging.error(f"統計計算失敗: {str(e)}")
        return {}

def create_summary_table(data: Dict[str, Any]) -> pd.DataFrame:
    """建立摘要表格"""
    try:
        summary_data = []
        
        for key, value in data.items():
            if isinstance(value, (int, float)):
                summary_data.append({
                    '項目': key,
                    '數值': format_number(value),
                    '類型': '數值'
                })
            elif isinstance(value, str):
                summary_data.append({
                    '項目': key,
                    '數值': value,
                    '類型': '文字'
                })
            elif isinstance(value, datetime):
                summary_data.append({
                    '項目': key,
                    '數值': value.strftime('%Y-%m-%d %H:%M:%S'),
                    '類型': '日期時間'
                })
        
        return pd.DataFrame(summary_data)
        
    except Exception as e:
        logging.error(f"摘要表格建立失敗: {str(e)}")
        return pd.DataFrame()

def generate_report_filename(report_type: str, extension: str = 'xlsx') -> str:
    """生成報表檔名"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        clean_type = clean_text(report_type).replace(' ', '_')
        return f"{clean_type}_{timestamp}.{extension}"
        
    except Exception as e:
        logging.error(f"檔名生成失敗: {str(e)}")
        return f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"

def check_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """檢查資料品質"""
    try:
        if df.empty:
            return {'status': 'empty', 'message': '資料為空'}
        
        quality_report = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'missing_values': {},
            'duplicate_rows': df.duplicated().sum(),
            'data_types': {},
            'quality_score': 0
        }
        
        # 檢查缺失值
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            missing_percentage = (missing_count / len(df)) * 100
            quality_report['missing_values'][col] = {
                'count': missing_count,
                'percentage': missing_percentage
            }
        
        # 檢查資料類型
        for col in df.columns:
            quality_report['data_types'][col] = str(df[col].dtype)
        
        # 計算品質分數
        total_missing = sum([info['count'] for info in quality_report['missing_values'].values()])
        missing_ratio = total_missing / (len(df) * len(df.columns))
        duplicate_ratio = quality_report['duplicate_rows'] / len(df)
        
        quality_score = max(0, 100 - (missing_ratio * 50) - (duplicate_ratio * 30))
        quality_report['quality_score'] = round(quality_score, 2)
        
        return quality_report
        
    except Exception as e:
        logging.error(f"資料品質檢查失敗: {str(e)}")
        return {'status': 'error', 'message': str(e)}

def create_alert_message(message: str, alert_type: str = 'info') -> None:
    """建立警告訊息"""
    try:
        if alert_type == 'success':
            st.success(f"✅ {message}")
        elif alert_type == 'warning':
            st.warning(f"⚠️ {message}")
        elif alert_type == 'error':
            st.error(f"❌ {message}")
        else:
            st.info(f"ℹ️ {message}")
            
    except Exception as e:
        logging.error(f"警告訊息建立失敗: {str(e)}")
        st.error("訊息顯示失敗")

def format_time_duration(seconds: float) -> str:
    """格式化時間長度"""
    try:
        if seconds < 60:
            return f"{seconds:.1f} 秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} 分鐘"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} 小時"
            
    except Exception as e:
        logging.error(f"時間格式化失敗: {str(e)}")
        return f"{seconds} 秒"

def create_progress_bar(current: int, total: int, message: str = "") -> None:
    """建立進度條"""
    try:
        if total > 0:
            progress = current / total
            st.progress(progress)
            
            if message:
                st.text(f"{message} ({current}/{total})")
            else:
                st.text(f"進度: {current}/{total} ({progress*100:.1f}%)")
                
    except Exception as e:
        logging.error(f"進度條建立失敗: {str(e)}")

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """安全除法，避免除零錯誤"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except Exception:
        return default

def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """截斷文字"""
    try:
        if not isinstance(text, str):
            text = str(text)
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
        
    except Exception as e:
        logging.error(f"文字截斷失敗: {str(e)}")
        return str(text)

def create_expandable_text(text: str, max_length: int = 100) -> None:
    """建立可展開的文字顯示"""
    try:
        if len(text) <= max_length:
            st.text(text)
        else:
            with st.expander(f"顯示完整內容 ({len(text)} 字元)"):
                st.text(text)
                
    except Exception as e:
        logging.error(f"可展開文字建立失敗: {str(e)}")
        st.text(str(text))

def validate_file_upload(uploaded_file, allowed_extensions: List[str] = None) -> bool:
    """驗證上傳檔案"""
    try:
        if uploaded_file is None:
            return False
        
        if allowed_extensions:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                st.error(f"不支援的檔案格式。允許的格式: {', '.join(allowed_extensions)}")
                return False
        
        # 檢查檔案大小（限制為 10MB）
        if uploaded_file.size > 10 * 1024 * 1024:
            st.error("檔案大小不能超過 10MB")
            return False
        
        return True
        
    except Exception as e:
        logging.error(f"檔案驗證失敗: {str(e)}")
        return False

def create_info_box(title: str, content: str, box_type: str = 'info') -> None:
    """建立資訊框"""
    try:
        if box_type == 'success':
            st.success(f"**{title}**\n\n{content}")
        elif box_type == 'warning':
            st.warning(f"**{title}**\n\n{content}")
        elif box_type == 'error':
            st.error(f"**{title}**\n\n{content}")
        else:
            st.info(f"**{title}**\n\n{content}")
            
    except Exception as e:
        logging.error(f"資訊框建立失敗: {str(e)}")

def get_system_info() -> Dict[str, str]:
    """獲取系統資訊"""
    try:
        import platform
        import sys
        
        return {
            '作業系統': platform.system(),
            '系統版本': platform.release(),
            'Python 版本': sys.version.split()[0],
            'Streamlit 版本': st.__version__,
            '當前時間': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        logging.error(f"系統資訊獲取失敗: {str(e)}")
        return {'錯誤': str(e)}