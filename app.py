import sys
import os

# 將專案根目錄添加到 Python 模組搜尋路徑
# 這確保了 'components' 和 'utils' 等頂層套件可以被正確導入
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
print(f"sys.path: {sys.path}") # <-- 添加這一行

import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from components.database_manager import DatabaseManager
from components.chat_interface import ChatInterface
from components.query_processor import QueryProcessor
from components.report_generator import ReportGenerator
from components.visualization import VisualizationManager
from utils.vanna_config import VannaConfig
from utils.helpers import format_dataframe, get_status_color

# 頁面配置
st.set_page_config(
    page_title="FT配件查詢",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF6B6B;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #FF6B6B;
    }
    .status-normal { color: #28a745; }
    .status-repair { color: #dc3545; }
    .status-maintenance { color: #ffc107; }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

class MainApp:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.chat_interface = ChatInterface()
        self.query_processor = QueryProcessor()
        self.report_generator = ReportGenerator()
        self.viz_manager = VisualizationManager()
        self.vanna_config = VannaConfig()
        
        # 初始化 session state
        if 'database_loaded' not in st.session_state:
            st.session_state.database_loaded = False
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'query_results' not in st.session_state:
            st.session_state.query_results = None

    def run(self):
        """主應用程式運行函數"""
        # 側邊欄導航
        with st.sidebar:

            # 使用按鈕替代下拉選單
            if 'current_page' not in st.session_state:
                st.session_state.current_page = "🏠 儀表板"

            # 定義按鈕樣式
            button_style = """
            <style>
            /* Base style for all sidebar buttons */
            .stButton > button {
                width: 100%;
                text-align: left;
                margin-bottom: 1px;
                background-color: transparent !important; /* Ensure background is always transparent */
                color: var(--text-color); /* Default text color from theme */
                border: 1px solid transparent !important; /* ALWAYS transparent border */
            }

            /* Style for the ACTIVE button */
            .stButton > button[kind="primary"] {
                color: var(--primary-color) !important; /* Active button text color */
            }

            /* Hover style for ANY button (active or not) */
            .stButton > button:hover {
                color: red !important; /* On hover, all buttons get red text */
                background-color: transparent !important; /* Explicitly keep background transparent on hover */
            }

            /* Remove focus outline */
            .stButton > button:focus {
                outline: none !important;
                box-shadow: none !important;
            }
            </style>
            """
            st.markdown(button_style, unsafe_allow_html=True)

            # 功能按鈕
            pages = [
                "🏠 儀表板",
                "🤖 AI幫你查",
                "📊 統計分析",
                "📋 變更紀錄",
                "📄 報表匯出",
                "⚙️ 系統設定"
            ]

            for page in pages:
                if st.button(page, key=page,
                             type="primary" if page == st.session_state.current_page else "secondary"):
                    st.session_state.current_page = page

            st.markdown("---")

            # 資料庫狀態
            self.show_database_status()

            st.markdown("---")


        # 主要內容區域
        if st.session_state.current_page == "🏠 儀表板":
            self.show_dashboard()
        elif st.session_state.current_page == "🤖 AI幫你查":
            self.show_chat_interface()
        elif st.session_state.current_page == "📊 統計分析":
            self.show_statistics()
        elif st.session_state.current_page == "📋 變更紀錄":
            self.show_change_logs()
        elif st.session_state.current_page == "📄 報表匯出":
            self.show_report_export()
        elif st.session_state.current_page == "⚙️ 系統設定":
            self.show_settings()

    def show_database_status(self):
        """顯示資料庫連接狀態"""
        st.subheader("📊 資料庫狀態")
        
        if self.db_manager.check_database_connection():
            st.success("✅ 資料庫已連接")
            last_update = self.db_manager.get_last_update_time()
            if last_update:
                st.info(f"📅 最後更新: {last_update}")
            st.session_state.database_loaded = True
        else:
            st.error("❌ 資料庫連接失敗")
            if st.button("🔄 重新連接"):
                st.rerun()


    def show_dashboard(self):
        """顯示首頁儀表板"""
        st.markdown('<h1 class="main-header">配件狀態</h1>', unsafe_allow_html=True)
        
        if not st.session_state.database_loaded:
            st.warning("⚠️ 請先確保資料庫連接正常")
            return
        
        # 總覽統計
        col1, col2, col3, col4 = st.columns(4)
        
        try:
            overview_stats = self.db_manager.get_overview_statistics()
            
            with col1:
                st.subheader("配件總數")
                st.metric("",overview_stats.get('total_parts', 0))
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.subheader("正常生產")
                st.metric("",overview_stats.get('normal_parts', 0))
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.subheader("維修中")
                st.metric("",overview_stats.get('repair_parts', 0))
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col4:
                st.subheader("客戶借出")
                st.metric("",overview_stats.get('borrowed_parts', 0))
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # 狀態分佈圖表
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("PAT狀態分佈")
                pat_status_data = self.db_manager.get_pat_status_distribution()
                if not pat_status_data.empty:
                    custom_colors = [ "#3D58F0", "#EF63FC", "#3375FF", "#FF7E33", "#79D7EE" ]

                    fig = px.pie(
                        pat_status_data,
                        values='數量',
                        names='配件狀態',
                        color='配件狀態',  # 保證顏色對應分類
                        color_discrete_sequence=custom_colors
                    )

                    fig.update_layout(
                        legend=dict(
                            orientation="h", 
                            x=0.5,           
                            y=-0.2,          
                            xanchor='center',
                            yanchor='top'
                        )
                    )

                    st.plotly_chart(fig, use_container_width=True)

                else:
                    st.info("暫無 PAT 配件資料")
            
            with col2:
                st.subheader("KYEC狀態分佈")
                kyec_status_data = self.db_manager.get_kyec_status_distribution()
                if not kyec_status_data.empty:
                    custom_colors = [ "#3D58F0", "#CFE289", "#EF63FC", "#79D7EE" ,"#FF7E33"]

                    fig = px.pie(
                        kyec_status_data,
                        values='數量',
                        names='配件狀態',
                        color='配件狀態',  # 保證顏色對應分類
                        color_discrete_sequence=custom_colors
                    )

                    fig.update_layout(
                        legend=dict(
                            orientation="h", 
                            x=0.5,           
                            y=-0.2,          
                            xanchor='center',
                            yanchor='top'
                        )
                    )

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("暫無 KYEC 配件資料")
            
                
        except Exception as e:
            st.error(f"儀表板載入失敗: {str(e)}")

    def show_chat_interface(self):
        """顯示聊天查詢介面"""
        st.markdown('<h1 class="main-header">🤖 AI查詢小幫手</h1>', unsafe_allow_html=True)
        
        if not st.session_state.database_loaded:
            st.warning("⚠️ 請先確保資料庫連接正常")
            return
        
        
        
        # 聊天介面
        self.chat_interface.render_chat_interface()

    def show_statistics(self):
        """顯示統計分析頁面"""
        st.markdown('<h1 class="main-header">📊 統計分析</h1>', unsafe_allow_html=True)
        
        if not st.session_state.database_loaded:
            st.warning("⚠️ 請先確保資料庫連接正常")
            return
        
        # 分析選項
        analysis_type = st.selectbox(
            "選擇分析類型",
            ["配件狀態統計","維修週期分析"]          #先將"客戶別分析" 與 "趨勢分析" 比較無用的功能不顯示
        )
        
        if analysis_type == "配件狀態統計":
            self.show_status_statistics()
        elif analysis_type == "客戶別分析":
            self.show_customer_analysis()
        elif analysis_type == "趨勢分析":
            self.show_trend_analysis()
        elif analysis_type == "維修週期分析":
            self.show_maintenance_cycle_analysis()

    def show_status_statistics(self):
        """顯示配件狀態統計"""
        st.subheader("📊 配件狀態詳細統計")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**PAT 配件狀態統計**")
            pat_stats = self.db_manager.get_detailed_pat_statistics()
            if not pat_stats.empty:
                st.dataframe(pat_stats, use_container_width=True)
            else:
                st.info("暫無 PAT 統計資料")
        
        with col2:
            st.write("**KYEC 配件狀態統計**")
            kyec_stats = self.db_manager.get_detailed_kyec_statistics()
            if not kyec_stats.empty:
                st.dataframe(kyec_stats, use_container_width=True)
            else:
                st.info("暫無 KYEC 統計資料")

    def show_customer_analysis(self):
        """顯示客戶別分析"""
        st.subheader("👥 客戶別配件分析")
        
        customer_stats = self.db_manager.get_customer_statistics()
        if not customer_stats.empty:
            # 客戶配件數量排行
            fig = px.bar(customer_stats.head(10), x='客戶名稱', y='配件數量',
                        title='客戶配件數量排行榜 (前10名)')
            st.plotly_chart(fig, use_container_width=True)
            
            # 詳細統計表
            st.subheader("📋 客戶詳細統計")
            st.dataframe(customer_stats, use_container_width=True)
        else:
            st.info("暫無客戶統計資料")

    def show_trend_analysis(self):
        """顯示趨勢分析"""
        st.subheader("📈 配件狀態趨勢分析")
        
        # 時間範圍選擇
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("開始日期", datetime.now().replace(day=1))
        with col2:
            end_date = st.date_input("結束日期", datetime.now())
        
        if start_date <= end_date:
            trend_data = self.db_manager.get_trend_analysis(start_date, end_date)
            if not trend_data.empty:
                fig = px.line(trend_data, x='日期', y='數量', color='狀態',
                            title=f'{start_date} 至 {end_date} 配件狀態趨勢')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("選定時間範圍內暫無資料")
        else:
            st.error("開始日期不能晚於結束日期")

    def show_maintenance_cycle_analysis(self):
        """顯示維修週期分析"""
        st.subheader("🔧 維修週期分析")
        
        maintenance_data = self.db_manager.get_maintenance_cycle_data()
        if not maintenance_data.empty:
            # 平均維修週期
            avg_cycle = maintenance_data['維修天數'].mean()
            st.metric("平均維修週期", f"{avg_cycle:.1f} 天")
            
            # 維修週期分佈
            fig = px.histogram(maintenance_data, x='維修天數', nbins=20,
                             title='維修週期分佈')
            st.plotly_chart(fig, use_container_width=True)
            
            # 詳細資料
            st.subheader("📋 維修週期詳細資料")
            st.dataframe(maintenance_data, use_container_width=True)
        else:
            st.info("暫無維修週期資料")

    def show_change_logs(self):
        """顯示變更紀錄頁面"""
        st.markdown('<h1 class="main-header">📋 配件變更紀錄</h1>', unsafe_allow_html=True)
        
        if not st.session_state.database_loaded:
            st.warning("⚠️ 請先確保資料庫連接正常")
            return
        
        # 篩選選項
        col1, col2, col3 = st.columns(3)
        
        with col1:
            table_filter = st.selectbox("資料表", ["全部", "pat_parts_all", "kyec_parts_all"])
        
        with col2:
            operation_filter = st.selectbox("操作類型", ["全部", "INSERT", "UPDATE", "DELETE"])
        
        with col3:
            days_filter = st.selectbox("時間範圍", ["全部", "最近7天", "最近30天", "最近90天"])
        
        # 搜尋框
        search_term = st.text_input("🔍 搜尋配件編號或關鍵字")
        
        # 獲取變更紀錄
        change_logs = self.db_manager.get_change_logs(
            table_filter, operation_filter, days_filter, search_term
        )
        
        if not change_logs.empty:
            st.subheader(f"📊 找到 {len(change_logs)} 筆變更紀錄")
            
            # 變更統計
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("新增", len(change_logs[change_logs['operation'] == 'INSERT']))
            with col2:
                st.metric("更新", len(change_logs[change_logs['operation'] == 'UPDATE']))
            with col3:
                st.metric("刪除", len(change_logs[change_logs['operation'] == 'DELETE']))
            
            # 變更紀錄表格
            st.dataframe(change_logs, use_container_width=True)
            
            # 變更趨勢圖
            if len(change_logs) > 1:
                daily_changes = change_logs.groupby(change_logs['timestamp'].dt.date).size().reset_index()
                daily_changes.columns = ['日期', '變更次數']
                
                fig = px.line(daily_changes, x='日期', y='變更次數',
                            title='每日變更次數趨勢')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("未找到符合條件的變更紀錄")

    def show_report_export(self):
        """顯示報表匯出頁面"""
        st.markdown('<h1 class="main-header">📄 報表匯出</h1>', unsafe_allow_html=True)
        
        if not st.session_state.database_loaded:
            st.warning("⚠️ 請先確保資料庫連接正常")
            return
        
        st.subheader("📊 選擇報表類型")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 配件狀態報表", type="primary", use_container_width=True):
                with st.spinner("正在生成報表..."):
                    excel_data = self.report_generator.generate_status_report()
                    if excel_data:
                        st.download_button(
                            label="📥 下載配件狀態報表",
                            data=excel_data,
                            file_name=f"配件狀態報表_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                        st.success("✅ 報表生成成功！")
                    else:
                        st.error("❌ 報表生成失敗")
        
        with col2:
            if st.button("📈 趨勢分析報表", use_container_width=True):
                # 日期範圍選擇
                date_range = st.date_input(
                    "選擇分析期間",
                    value=[datetime.now().replace(day=1), datetime.now()],
                    key="trend_date_range"
                )
                
                if len(date_range) == 2:
                    with st.spinner("正在生成趨勢報表..."):
                        excel_data = self.report_generator.generate_trend_report(date_range)
                        if excel_data:
                            st.download_button(
                                label="📥 下載趨勢分析報表",
                                data=excel_data,
                                file_name=f"趨勢分析報表_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                            st.success("✅ 趨勢報表生成成功！")
                        else:
                            st.error("❌ 趨勢報表生成失敗")
        
        with col3:
            if st.button("📋 變更紀錄報表", use_container_width=True):
                with st.spinner("正在生成變更紀錄報表..."):
                    excel_data = self.report_generator.generate_change_log_report()
                    if excel_data:
                        st.download_button(
                            label="📥 下載變更紀錄報表",
                            data=excel_data,
                            file_name=f"變更紀錄報表_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                        st.success("✅ 變更紀錄報表生成成功！")
                    else:
                        st.error("❌ 變更紀錄報表生成失敗")
        
        st.markdown("---")
        
        # 自訂報表選項
        st.subheader("🎨 自訂報表")
        
        with st.expander("自訂報表設定"):
            report_name = st.text_input("報表名稱", "自訂配件報表")
            
            # 資料表選擇
            tables = st.multiselect(
                "選擇資料表",
                ["pat_parts_all", "kyec_parts_all", "pat_stats_weekly", "kyec_stats_weekly", "table_change_log"],
                default=["pat_parts_all", "kyec_parts_all"]
            )
            
            # 欄位選擇
            if tables:
                available_columns = self.db_manager.get_available_columns(tables)
                selected_columns = st.multiselect("選擇欄位", available_columns)
                
                # 篩選條件
                filter_conditions = st.text_area("篩選條件 (SQL WHERE 語法)", "")
                
                if st.button("生成自訂報表", type="primary"):
                    if selected_columns:
                        with st.spinner("正在生成自訂報表..."):
                            excel_data = self.report_generator.generate_custom_report(
                                report_name, tables, selected_columns, filter_conditions
                            )
                            if excel_data:
                                st.download_button(
                                    label=f"📥 下載 {report_name}",
                                    data=excel_data,
                                    file_name=f"{report_name}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                                st.success("✅ 自訂報表生成成功！")
                            else:
                                st.error("❌ 自訂報表生成失敗")
                    else:
                        st.warning("請至少選擇一個欄位")

    def show_settings(self):
        """顯示系統設定頁面"""
        st.markdown('<h1 class="main-header">⚙️ 系統設定</h1>', unsafe_allow_html=True)
        
        # 資料庫設定
        st.subheader("🗄️ 資料庫設定")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("📊 資料庫資訊")
            db_info = self.db_manager.get_database_info()
            for key, value in db_info.items():
                st.write(f"**{key}**: {value}")
        
        with col2:
            st.info("🔄 同步設定")
            st.write("**同步頻率**: 每週一早上 1:00")
            st.write("**最後同步**: ", self.db_manager.get_last_sync_time())
            
            if st.button("🔄 手動同步資料庫"):
                with st.spinner("正在同步資料庫..."):
                    success = self.db_manager.manual_sync()
                    if success:
                        st.success("✅ 資料庫同步成功！")
                        st.rerun()
                    else:
                        st.error("❌ 資料庫同步失敗")
        
        st.markdown("---")
        
        # Vanna AI 設定
        st.subheader("🤖 AI 查詢設定")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("🧠 AI 模型狀態")
            ai_status = self.vanna_config.get_model_status()
            st.write(f"**模型狀態**: {ai_status['status']}")
            st.write(f"**訓練資料數量**: {ai_status['training_data_count']}")
            st.write(f"**最後訓練時間**: {ai_status['last_training']}")

            with st.expander("上傳 JSON/CSV 訓練檔"):
                uploaded_file = st.file_uploader("選擇訓練資料檔案", type=["json", "csv"])
                
                if uploaded_file is not None:
                    try:
                        # 讀取資料
                        if uploaded_file.name.lower().endswith(".json"):
                            training_df = pd.read_json(uploaded_file)
                        else:
                            training_df = pd.read_csv(uploaded_file)

                        st.write("📄 資料預覽", training_df.head())

                        # 匯入按鈕
                        if st.button("🚀 開始匯入訓練資料"):
                            success_cnt = 0
                            for _, row in training_df.iterrows():
                                question = row.get("question") or row.get("Question")
                                sql = row.get("sql") or row.get("SQL")
                                if question and sql:
                                    if self.vanna_config.add_training_data(question, sql):
                                        success_cnt += 1
                            st.success(f"✅ 匯入完成，共新增 {success_cnt} 筆訓練資料")
                    except Exception as e:
                        st.error(f"❌ 讀取訓練資料失敗: {str(e)}")
        
        with col2:
            st.info("🎯 查詢設定")
            max_results = st.number_input("最大查詢結果數", min_value=10, max_value=1000, value=100)
            query_timeout = st.number_input("查詢超時時間(秒)", min_value=5, max_value=60, value=30)
            
            if st.button("💾 儲存設定"):
                self.vanna_config.update_settings(max_results, query_timeout)
                st.success("✅ 設定已儲存！")


        st.markdown("---")

        
        # 系統資訊
        st.subheader("ℹ️ 系統資訊")
        
        system_info = {
            "應用程式版本": "demo verion 2025/7/1",
            "Streamlit 版本": st.__version__,
            "Python 版本": "3.12+",
            "部署環境": "Streamlit Cloud"
            #"最後更新": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        for key, value in system_info.items():
            st.write(f"**{key}**: {value}")

# 主程式入口
if __name__ == "__main__":
    app = MainApp()
    app.run()