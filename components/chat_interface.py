import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import plotly.express as px
import plotly.graph_objects as go
from utils.vanna_config import VannaConfig

class ChatInterface:
    """聊天介面管理類別 - 基於 Vanna AI 官方範例"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 初始化 Vanna AI
        if 'vanna_config' not in st.session_state:
            with st.spinner("🤖 正在初始化 AI 查詢引擎..."):
                st.session_state.vanna_config = VannaConfig()
        
        self.vanna_config = st.session_state.vanna_config
        
        # 初始化 session state
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
    
    def render_chat_interface(self, selected_suggestion: str = ""):
        """渲染聊天介面 - 參考官方範例"""
        
        # 顯示聊天歷史
        self._display_chat_history()
        
        # 處理選中的建議
        if selected_suggestion and selected_suggestion not in [msg.get('content', '') for msg in st.session_state.messages if msg.get('role') == 'user']:
            self._process_question(selected_suggestion)
            st.rerun()
        
        # 查詢輸入
        self._render_query_input()
    
    def _display_chat_history(self):
        """顯示聊天歷史"""
        if not st.session_state.messages:
            st.markdown("""
            ### 👋 歡迎使用配件查詢小幫手！
            
            我可以幫您查詢配件相關資訊。您可以用自然語言提問，例如：
            
            - "顯示所有正在客戶維修的配件"
            - "統計各種配件狀態的數量"
            - "查看最近的配件變更記錄"
            """)
        
        # 顯示對話記錄
        for message in st.session_state.messages:
            self._render_message(message)
    
    def _render_message(self, message: Dict[str, Any]):
        """渲染單個訊息"""
        if message['role'] == 'user':
            with st.chat_message("user", avatar="👤"):
                st.markdown(message['content'])
        
        elif message['role'] == 'assistant':
            with st.chat_message("assistant", avatar="🤖"):
                if message.get('success', False):
                    self._render_successful_response(message)
                else:
                    self._render_error_response(message)
    
    def _render_successful_response(self, message: Dict[str, Any]):
        """渲染成功的回應"""
        # 顯示解釋
        #if 'explanation' in message and message['explanation']:
            #st.markdown(f"**💡 解釋：** {message['explanation']}")
        
        # 顯示 SQL 查詢
        if 'sql' in message and message['sql']:
            with st.expander("🔍 查看 SQL 查詢", expanded=False):
                st.code(message['sql'], language='sql')
        
        # 顯示查詢結果
        if 'data' in message and not message['data'].empty:
            df = message['data']
            
            st.markdown(f"**📊 查詢結果：** 找到 {len(df)} 筆資料")
            
            # 顯示資料表格
            st.dataframe(df, use_container_width=True, height=min(400, (len(df) + 1) * 35))
            
            # 生成圖表（如果適合）
            self._try_generate_chart(message.get('question', ''), message.get('sql', ''), df)
            
            # 提供下載選項
            self._render_download_options(df, message.get('question', ''))
        
        elif 'data' in message:
            st.info("查詢執行成功，但未返回任何結果。")
    
    def _render_error_response(self, message: Dict[str, Any]):
        """渲染錯誤回應"""
        st.error(f"❌ {message.get('error', '查詢失敗')}")
        
        if 'sql' in message and message['sql']:
            with st.expander("🔍 查看嘗試的 SQL 查詢"):
                st.code(message['sql'], language='sql')
    
    def _try_generate_chart(self, question: str, sql: str, df: pd.DataFrame):
        """嘗試生成圖表"""
        return
    
    def _generate_simple_chart(self, df: pd.DataFrame):
        """生成簡單的圖表"""
        try:
            # 如果有數量相關的欄位，生成長條圖
            numeric_cols = df.select_dtypes(include=['number']).columns
            text_cols = df.select_dtypes(include=['object']).columns
            
            if len(numeric_cols) > 0 and len(text_cols) > 0:
                # 取第一個文字欄位作為 x 軸，第一個數字欄位作為 y 軸
                x_col = text_cols[0]
                y_col = numeric_cols[0]
                
                if len(df) <= 20:  # 只有在資料不太多時才顯示圖表
                    fig = px.bar(df.head(10), x=x_col, y=y_col, 
                               title=f"{y_col} 按 {x_col} 分佈")
                    st.plotly_chart(fig, use_container_width=True)
                    
        except Exception as e:
            self.logger.warning(f"簡單圖表生成失敗: {str(e)}")
    
    def _render_download_options(self, df: pd.DataFrame, question: str):
        """渲染下載選項"""
        col1, col2 = st.columns(2)
        
        # 使用更加複雜的唯一 key 生成方式
        import hashlib
        import uuid

        # 使用問題、當前時間和隨機 UUID 生成唯一 key
        unique_key_base = f"{question}_{datetime.now().isoformat()}_{str(uuid.uuid4())}"
        unique_hash = hashlib.md5(unique_key_base.encode()).hexdigest()[:16]
        
        with col1:
            csv_data = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 下載 CSV",
                data=csv_data,
                file_name=f"查詢結果_{unique_hash}.csv",
                mime="text/csv",
                use_container_width=True,
                key=f"csv_download_{unique_hash}"
            )
        
        with col2:
            # Excel 下載
            try:
                import io
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='查詢結果')
                
                st.download_button(
                    label="📊 下載 Excel",
                    data=buffer.getvalue(),
                    file_name=f"查詢結果_{unique_hash}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key=f"excel_download_{unique_hash}"
                )
            except Exception as e:
                self.logger.warning(f"Excel 下載功能失敗: {str(e)}")
    
    def _render_query_input(self):
        """渲染查詢輸入區域"""
        # 查詢輸入框
        if prompt := st.chat_input("請輸入您的問題..."):
            self._process_question(prompt)
            st.rerun()
    
    def _process_question(self, question: str):
        """處理使用者問題 - 參考官方範例"""
        # 添加使用者訊息
        st.session_state.messages.append({
            "role": "user", 
            "content": question
        })
        
        # 顯示處理中狀態
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🤖 正在分析您的問題..."):
                # 使用 Vanna AI 處理問題
                result = self.vanna_config.ask_question(question)
        
        # 添加助手回應
        assistant_message = {
            "role": "assistant",
            **result
        }
        st.session_state.messages.append(assistant_message)
        
        # 添加到查詢歷史
        if result.get('success', False):
            history_item = {
                'question': question,
                'sql': result.get('sql', ''),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'result_count': len(result.get('data', pd.DataFrame()))
            }
            st.session_state.query_history.append(history_item)
            
            # 限制歷史記錄數量
            if len(st.session_state.query_history) > 50:
                st.session_state.query_history = st.session_state.query_history[-50:]
    
    def render_sidebar_content(self):
        """渲染側邊欄內容"""
        with st.sidebar:
            st.markdown("### 🤖 AI 查詢小幫手")
            
            # 模型狀態
            self._render_model_status()
            
            st.markdown("---")
            
            # 快速查詢按鈕
            self._render_quick_queries()
            
            st.markdown("---")
            
            # 查詢歷史
            self._render_query_history_sidebar()
            
            st.markdown("---")
            
            # 相關問題建議
            self._render_related_questions()
    
    def _render_model_status(self):
        """渲染模型狀態"""
        st.markdown("**🔧 模型狀態**")
        
        status = self.vanna_config.get_model_status()
        
        if status.get('status') == '正常':
            st.success("✅ AI 模型運行正常")
            st.info(f"📚 訓練資料: {status.get('training_data_count', 0)} 筆")
        else:
            st.error(f"❌ {status.get('error', '模型異常')}")
    
    def _render_quick_queries(self):
        """渲染快速查詢按鈕"""
        st.markdown("**⚡ 快速查詢**")
        
        quick_queries = [
            "配件狀態統計",
            "維修中配件",
            "客戶配件分佈",
            "最近變更記錄"
        ]
        
        for query in quick_queries:
            if st.button(query, key=f"quick_{query}", use_container_width=True):
                question_mapping = {
                    "配件狀態統計": "統計各種配件狀態的數量",
                    "維修中配件": "顯示所有正在維修的配件",
                    "客戶配件分佈": "顯示各客戶的配件數量統計",
                    "最近變更記錄": "顯示最近7天的配件變更記錄"
                }
                
                question = question_mapping.get(query, query)
                self._process_question(question)
                st.rerun()
    
    def _render_query_history_sidebar(self):
        """渲染查詢歷史（側邊欄版本）"""
        st.markdown("**📚 查詢歷史**")
        
        if not st.session_state.query_history:
            st.info("暫無查詢歷史")
            return
        
        # 顯示最近的5個查詢
        recent_queries = st.session_state.query_history[-5:]
        
        for i, item in enumerate(reversed(recent_queries)):
            question_short = item['question'][:25] + "..." if len(item['question']) > 25 else item['question']
            
            if st.button(f"🔍 {question_short}", key=f"history_{i}", use_container_width=True):
                self._process_question(item['question'])
                st.rerun()
        
        # 清除歷史按鈕
        if len(st.session_state.query_history) > 0:
            if st.button("🗑️ 清除歷史", use_container_width=True):
                st.session_state.query_history = []
                st.rerun()
    
    def _render_related_questions(self):
        """渲染相關問題建議"""
        st.markdown("**💡 相關問題**")
        
        # 獲取相關問題
        if st.session_state.messages:
            last_user_message = None
            for msg in reversed(st.session_state.messages):
                if msg['role'] == 'user':
                    last_user_message = msg['content']
                    break
            
            if last_user_message:
                related_questions = self.vanna_config.get_related_questions(last_user_message)
            else:
                related_questions = self._get_default_suggestions()
        else:
            related_questions = self._get_default_suggestions()
        
        for i, question in enumerate(related_questions[:3]):  # 只顯示前3個
            question_short = question[:30] + "..." if len(question) > 30 else question
            
            if st.button(f"💭 {question_short}", key=f"related_{i}", use_container_width=True):
                self._process_question(question)
                st.rerun()
    
    def _get_default_suggestions(self) -> List[str]:
        """獲取預設建議"""
        return [
            "顯示配件狀態統計",
            "查看維修中的配件",
            "顯示客戶配件分佈",
            "查看配件變更歷史",
            "統計配件種類數量"
        ]
    
    def render_training_interface(self):
        """渲染訓練介面"""
        st.markdown("### 🎓 AI 模型訓練")
        
        with st.expander("添加新的訓練資料"):
            new_question = st.text_input("問題", placeholder="例如：顯示所有配件")
            new_sql = st.text_area("對應的 SQL 查詢", placeholder="SELECT * FROM ...")
            
            if st.button("➕ 添加訓練資料"):
                if new_question and new_sql:
                    success = self.vanna_config.add_training_data(new_question, new_sql)
                    if success:
                        st.success("✅ 訓練資料已添加")
                    else:
                        st.error("❌ 添加失敗")
                else:
                    st.warning("請填寫問題和 SQL 查詢")
        
        # 顯示訓練資料摘要
        training_summary = self.vanna_config.get_training_data_summary()
        
        if 'error' not in training_summary:
            st.markdown("**📊 訓練資料摘要**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("總計", training_summary.get('total_count', 0))
            with col2:
                st.metric("SQL 範例", training_summary.get('sql_count', 0))
            with col3:
                st.metric("文檔說明", training_summary.get('documentation_count', 0))
    
    def clear_chat_history(self):
        """清除聊天記錄"""
        st.session_state.messages = []
        st.session_state.query_history = []
    
    def export_chat_history(self) -> str:
        """匯出聊天記錄"""
        try:
            chat_data = []
            
            for message in st.session_state.messages:
                if message['role'] == 'user':
                    chat_data.append({
                        '時間': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        '類型': '使用者問題',
                        '內容': message['content'],
                        'SQL': '',
                        '結果數量': ''
                    })
                elif message['role'] == 'assistant':
                    chat_data.append({
                        '時間': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        '類型': '系統回應',
                        '內容': message.get('explanation', ''),
                        'SQL': message.get('sql', ''),
                        '結果數量': len(message.get('data', pd.DataFrame())) if message.get('success') else 0
                    })
            
            df = pd.DataFrame(chat_data)
            return df.to_csv(index=False, encoding='utf-8-sig')
            
        except Exception as e:
            self.logger.error(f"聊天記錄匯出失敗: {str(e)}")
            return ""