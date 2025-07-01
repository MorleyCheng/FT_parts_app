import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st
from typing import Dict, List, Any, Optional
import logging

class VisualizationManager:
    """視覺化管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 定義顏色主題
        self.color_palette = {
            'primary': '#FF6B6B',
            'secondary': '#4ECDC4',
            'success': '#45B7D1',
            'warning': '#FFA07A',
            'danger': '#FF6B6B',
            'info': '#6C7CE0'
        }
        
        # 狀態顏色映射
        self.status_colors = {
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
    
    def create_status_pie_chart(self, data: pd.DataFrame, title: str = "配件狀態分佈") -> go.Figure:
        """建立狀態分佈圓餅圖"""
        try:
            if data.empty:
                return self._create_empty_chart("暫無資料")
            
            # 準備顏色
            colors = [self.status_colors.get(status, '#6c757d') for status in data.iloc[:, 0]]
            
            fig = px.pie(
                data, 
                values=data.columns[1], 
                names=data.columns[0],
                title=title,
                color_discrete_sequence=colors
            )
            
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>數量: %{value}<br>百分比: %{percent}<extra></extra>'
            )
            
            fig.update_layout(
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.01
                ),
                margin=dict(t=50, b=50, l=50, r=150)
            )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"圓餅圖建立失敗: {str(e)}")
            return self._create_empty_chart("圖表建立失敗")
    
    def create_status_bar_chart(self, data: pd.DataFrame, title: str = "配件狀態統計") -> go.Figure:
        """建立狀態統計長條圖"""
        try:
            if data.empty:
                return self._create_empty_chart("暫無資料")
            
            # 準備顏色
            colors = [self.status_colors.get(status, '#6c757d') for status in data.iloc[:, 0]]
            
            fig = px.bar(
                data,
                x=data.columns[0],
                y=data.columns[1],
                title=title,
                color=data.columns[0],
                color_discrete_map=self.status_colors
            )
            
            fig.update_traces(
                hovertemplate='<b>%{x}</b><br>數量: %{y}<extra></extra>'
            )
            
            fig.update_layout(
                xaxis_title="配件狀態",
                yaxis_title="數量",
                showlegend=False,
                xaxis_tickangle=-45
            )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"長條圖建立失敗: {str(e)}")
            return self._create_empty_chart("圖表建立失敗")
    
    def create_customer_analysis_chart(self, data: pd.DataFrame) -> go.Figure:
        """建立客戶分析圖表"""
        try:
            if data.empty:
                return self._create_empty_chart("暫無客戶資料")
            
            # 取前10名客戶
            top_customers = data.head(10)
            
            fig = go.Figure()
            
            # 添加配件總數長條
            fig.add_trace(go.Bar(
                name='配件總數',
                x=top_customers['客戶名稱'],
                y=top_customers['配件數量'],
                marker_color=self.color_palette['primary'],
                hovertemplate='<b>%{x}</b><br>配件總數: %{y}<extra></extra>'
            ))
            
            # 如果有維修資料，添加維修配件長條
            if '維修中配件' in top_customers.columns:
                fig.add_trace(go.Bar(
                    name='維修中配件',
                    x=top_customers['客戶名稱'],
                    y=top_customers['維修中配件'],
                    marker_color=self.color_palette['danger'],
                    hovertemplate='<b>%{x}</b><br>維修中配件: %{y}<extra></extra>'
                ))
            
            fig.update_layout(
                title='客戶配件統計 (前10名)',
                xaxis_title='客戶名稱',
                yaxis_title='配件數量',
                barmode='group',
                xaxis_tickangle=-45,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"客戶分析圖表建立失敗: {str(e)}")
            return self._create_empty_chart("客戶分析圖表建立失敗")
    
    def create_trend_line_chart(self, data: pd.DataFrame) -> go.Figure:
        """建立趨勢線圖"""
        try:
            if data.empty:
                return self._create_empty_chart("暫無趨勢資料")
            
            fig = go.Figure()
            
            # 假設資料格式為：日期, 狀態, 數量
            if len(data.columns) >= 3:
                date_col = data.columns[0]
                status_col = data.columns[1]
                value_col = data.columns[2]
                
                # 按狀態分組繪製線圖
                for status in data[status_col].unique():
                    status_data = data[data[status_col] == status]
                    
                    fig.add_trace(go.Scatter(
                        x=status_data[date_col],
                        y=status_data[value_col],
                        mode='lines+markers',
                        name=status,
                        line=dict(color=self.status_colors.get(status, '#6c757d')),
                        hovertemplate=f'<b>{status}</b><br>日期: %{{x}}<br>數量: %{{y}}<extra></extra>'
                    ))
            
            fig.update_layout(
                title='配件狀態變化趨勢',
                xaxis_title='時間',
                yaxis_title='數量',
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"趨勢線圖建立失敗: {str(e)}")
            return self._create_empty_chart("趨勢線圖建立失敗")
    
    def create_maintenance_analysis_chart(self, data: pd.DataFrame) -> go.Figure:
        """建立維修分析圖表"""
        try:
            if data.empty:
                return self._create_empty_chart("暫無維修資料")
            
            # 建立維修天數分佈直方圖
            fig = px.histogram(
                data,
                x='維修天數',
                nbins=20,
                title='維修週期分佈',
                color_discrete_sequence=[self.color_palette['warning']]
            )
            
            fig.update_traces(
                hovertemplate='維修天數: %{x}<br>配件數量: %{y}<extra></extra>'
            )
            
            fig.update_layout(
                xaxis_title='維修天數',
                yaxis_title='配件數量',
                bargap=0.1
            )
            
            # 添加平均線
            if '維修天數' in data.columns:
                avg_days = data['維修天數'].mean()
                fig.add_vline(
                    x=avg_days,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"平均: {avg_days:.1f}天"
                )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"維修分析圖表建立失敗: {str(e)}")
            return self._create_empty_chart("維修分析圖表建立失敗")
    
    def create_change_log_chart(self, data: pd.DataFrame) -> go.Figure:
        """建立變更記錄圖表"""
        try:
            if data.empty:
                return self._create_empty_chart("暫無變更記錄")
            
            # 按日期統計變更次數
            if 'timestamp' in data.columns:
                data['日期'] = pd.to_datetime(data['timestamp']).dt.date
                daily_changes = data.groupby('日期').size().reset_index(name='變更次數')
                
                fig = px.line(
                    daily_changes,
                    x='日期',
                    y='變更次數',
                    title='每日變更次數趨勢',
                    markers=True,
                    color_discrete_sequence=[self.color_palette['info']]
                )
                
                fig.update_traces(
                    hovertemplate='日期: %{x}<br>變更次數: %{y}<extra></extra>'
                )
                
                fig.update_layout(
                    xaxis_title='日期',
                    yaxis_title='變更次數'
                )
                
                return fig
            else:
                return self._create_empty_chart("資料格式不正確")
            
        except Exception as e:
            self.logger.error(f"變更記錄圖表建立失敗: {str(e)}")
            return self._create_empty_chart("變更記錄圖表建立失敗")
    
    def create_comprehensive_dashboard(self, status_data: Dict[str, pd.DataFrame]) -> go.Figure:
        """建立綜合儀表板"""
        try:
            # 建立子圖
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('PAT 配件狀態', 'KYEC 配件狀態', '客戶配件統計', '維修週期分析'),
                specs=[[{"type": "pie"}, {"type": "pie"}],
                       [{"type": "bar"}, {"type": "histogram"}]]
            )
            
            # PAT 狀態圓餅圖
            if 'pat_status' in status_data and not status_data['pat_status'].empty:
                pat_data = status_data['pat_status']
                fig.add_trace(
                    go.Pie(
                        labels=pat_data.iloc[:, 0],
                        values=pat_data.iloc[:, 1],
                        name="PAT"
                    ),
                    row=1, col=1
                )
            
            # KYEC 狀態圓餅圖
            if 'kyec_status' in status_data and not status_data['kyec_status'].empty:
                kyec_data = status_data['kyec_status']
                fig.add_trace(
                    go.Pie(
                        labels=kyec_data.iloc[:, 0],
                        values=kyec_data.iloc[:, 1],
                        name="KYEC"
                    ),
                    row=1, col=2
                )
            
            # 客戶統計長條圖
            if 'customer_stats' in status_data and not status_data['customer_stats'].empty:
                customer_data = status_data['customer_stats'].head(10)
                fig.add_trace(
                    go.Bar(
                        x=customer_data['客戶名稱'],
                        y=customer_data['配件數量'],
                        name="客戶配件數"
                    ),
                    row=2, col=1
                )
            
            # 維修週期直方圖
            if 'maintenance_data' in status_data and not status_data['maintenance_data'].empty:
                maintenance_data = status_data['maintenance_data']
                if '維修天數' in maintenance_data.columns:
                    fig.add_trace(
                        go.Histogram(
                            x=maintenance_data['維修天數'],
                            name="維修週期"
                        ),
                        row=2, col=2
                    )
            
            fig.update_layout(
                height=800,
                title_text="配件管理綜合儀表板",
                showlegend=False
            )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"綜合儀表板建立失敗: {str(e)}")
            return self._create_empty_chart("綜合儀表板建立失敗")
    
    def create_kpi_metrics(self, data: Dict[str, Any]) -> None:
        """建立 KPI 指標顯示"""
        try:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="📦 配件總數",
                    value=data.get('total_parts', 0),
                    delta=data.get('total_parts_delta', None)
                )
            
            with col2:
                st.metric(
                    label="🔧 維修中",
                    value=data.get('repair_parts', 0),
                    delta=data.get('repair_parts_delta', None),
                    delta_color="inverse"
                )
            
            with col3:
                st.metric(
                    label="✅ 正常生產",
                    value=data.get('normal_parts', 0),
                    delta=data.get('normal_parts_delta', None)
                )
            
            with col4:
                repair_rate = 0
                if data.get('total_parts', 0) > 0:
                    repair_rate = (data.get('repair_parts', 0) / data.get('total_parts', 1)) * 100
                
                st.metric(
                    label="🔧 維修率",
                    value=f"{repair_rate:.1f}%",
                    delta=data.get('repair_rate_delta', None),
                    delta_color="inverse"
                )
                
        except Exception as e:
            self.logger.error(f"KPI 指標顯示失敗: {str(e)}")
            st.error("KPI 指標載入失敗")
    
    def _create_empty_chart(self, message: str) -> go.Figure:
        """建立空白圖表"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            plot_bgcolor='white'
        )
        return fig
    
    def create_interactive_filter_chart(self, data: pd.DataFrame, 
                                      filter_column: str, value_column: str) -> go.Figure:
        """建立互動式篩選圖表"""
        try:
            if data.empty:
                return self._create_empty_chart("暫無資料")
            
            # 建立下拉選單選項
            unique_values = data[filter_column].unique()
            
            # 建立初始圖表
            fig = go.Figure()
            
            # 為每個唯一值建立軌跡
            for value in unique_values:
                filtered_data = data[data[filter_column] == value]
                
                fig.add_trace(go.Bar(
                    x=filtered_data.index,
                    y=filtered_data[value_column],
                    name=str(value),
                    visible=True if value == unique_values[0] else False
                ))
            
            # 建立下拉選單
            dropdown_buttons = []
            for i, value in enumerate(unique_values):
                visibility = [False] * len(unique_values)
                visibility[i] = True
                
                dropdown_buttons.append(
                    dict(
                        label=str(value),
                        method="update",
                        args=[{"visible": visibility}]
                    )
                )
            
            fig.update_layout(
                updatemenus=[
                    dict(
                        buttons=dropdown_buttons,
                        direction="down",
                        showactive=True,
                        x=0.1,
                        xanchor="left",
                        y=1.15,
                        yanchor="top"
                    )
                ],
                title=f"按 {filter_column} 篩選的 {value_column}",
                xaxis_title="項目",
                yaxis_title=value_column
            )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"互動式篩選圖表建立失敗: {str(e)}")
            return self._create_empty_chart("互動式圖表建立失敗")
    
    def apply_theme(self, fig: go.Figure, theme: str = "default") -> go.Figure:
        """套用主題樣式"""
        try:
            if theme == "dark":
                fig.update_layout(
                    plot_bgcolor='#2E2E2E',
                    paper_bgcolor='#1E1E1E',
                    font_color='white',
                    xaxis=dict(gridcolor='#404040'),
                    yaxis=dict(gridcolor='#404040')
                )
            elif theme == "minimal":
                fig.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=False)
                )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"主題套用失敗: {str(e)}")
            return fig