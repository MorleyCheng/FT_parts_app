"""
Utils module for Streamlit Vanna AI Chatbot

This module contains utility functions and configurations:
- VannaConfig: Vanna AI 配置和管理
- helpers: 輔助函數和工具
"""

from .vanna_config import VannaConfig
from .helpers import (
    format_dataframe,
    get_status_color,
    format_number,
    create_download_link,
    validate_date_range,
    clean_text,
    parse_search_query,
    calculate_statistics,
    create_summary_table,
    generate_report_filename,
    check_data_quality,
    create_alert_message,
    format_time_duration,
    safe_divide,
    truncate_text,
    get_system_info
)

__all__ = [
    'VannaConfig',
    'format_dataframe',
    'get_status_color',
    'format_number',
    'create_download_link',
    'validate_date_range',
    'clean_text',
    'parse_search_query',
    'calculate_statistics',
    'create_summary_table',
    'generate_report_filename',
    'check_data_quality',
    'create_alert_message',
    'format_time_duration',
    'safe_divide',
    'truncate_text',
    'get_system_info'
]

__version__ = '1.0.0'
__author__ = 'GLI FT Parts Team'