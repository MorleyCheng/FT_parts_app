"""
Components module for Streamlit Vanna AI Chatbot

This module contains all the core components for the application:
- ChatInterface: 聊天介面管理
- DatabaseManager: 資料庫連接和管理
- QueryProcessor: 查詢處理和分析
- ReportGenerator: Excel 報表生成
- VisualizationManager: 資料視覺化
"""

from .chat_interface import ChatInterface
from .database_manager import DatabaseManager
from .query_processor import QueryProcessor
from .report_generator import ReportGenerator
from .visualization import VisualizationManager

__all__ = [
    'ChatInterface',
    'DatabaseManager', 
    'QueryProcessor',
    'ReportGenerator',
    'VisualizationManager'
]

__version__ = '1.0.0'
__author__ = 'GLI FT Parts Team'