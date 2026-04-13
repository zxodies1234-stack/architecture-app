import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
import os

# --- 基礎設定 ---
SAVE_DIR = "projects"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

st.set_page_config(layout="wide", page_title="建築專案管理系統")

# --- 狀態選項 ---
STATUS_OPTIONS = ["未開始", "作業中", "掛件中", "已完成", "🟣 作業要徑", "🔴 遇到問題"]

# --- 讀取資料函式 ---
def load_project_data(path):
    if os.path.exists(path) and os.path.getsize(path) > 10: 
        df = pd.read_csv(path)
        df['預計開始'] = pd.to_datetime(df['預計開始']).dt.date
        df['預計結束'] = pd.to_datetime(df['預計結束']).dt.date
        df['實際結束'] = pd.to_datetime(df['實際結束']).dt.date
        return df
    else:
        stages = ["設計初期", "圖面規劃", "圖面檢討", "都審", "建照", "施工圖"]
        data = [{
            "階段": s, "狀態": "未開始",
            "預計開始": date.today(), "預計結束": date.today() + timedelta(days=60),
            "實際結束": date.today() + timedelta(days=60), "子任務數": 5, "完成數": 0, "進度(%)": 0
        } for s in stages]
        return pd.DataFrame(data)

# --- 側邊欄 ---
st.sidebar.title("🏢 專案選擇")
all_projects = [f.replace(".csv", "") for f in os.listdir(SAVE_DIR) if f.endswith(".csv")]
if not all_projects:
    all_projects = ["預設專案"]
current_project = st.sidebar.selectbox(label="當前專案", options=all_projects, label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.title("🚀 Project Data")
menu = st.sidebar.radio(label="導覽選單", options=["📝 專案進度", "🖼️ 基地照片", "⚖️ 相關法規"], label_visibility="collapsed")

save_path = os.path.join(SAVE_DIR, f"{current_project}.csv")
df = load_project_data(save_path)

# --- 右側顯示區 ---

if menu == "📝 專案進度":
    st.title(f"🏢 專案進度：{current_project}")
    
    # --- 修改點：將標題與按鈕並列，並縮小按鈕 ---
    col1, col2 = st.columns([9, 1])
    with col1:
        st.subheader("📋 工作清單")
    with col2:
        # 移除 primary 類型與容器寬度，並更名為「儲存」
        save_btn = st.button("儲存")

    edited_df = st.data_editor(
        df,
        column_config={
            "狀態": st.column_config.SelectboxColumn("狀態", options=STATUS_OPTIONS, required=True),
            "預計開始": st.column_config.DateColumn("預計開始", format="YYYY-MM-DD"),
            "預計結束": st.column_config.DateColumn("預計結束", format="YYYY-MM-DD"),
            "實際結束": st.column_config.DateColumn("實際結束", format="YYYY-MM-DD"),
            "進度(%)": st.column_config.NumberColumn("進度(%)", format="%d%%", min_value=0, max_value=100),
        },
        hide_index=True,
        use_container_width=True,
        key="main_editor"
    )

    if save_btn:
        edited_df.to_csv(save_path, index=False)
        st.success("✅ 已儲存")
        st.rerun()

    st.divider()

    st.subheader("📊 工程進度表") 
    
    plot_list = []
    y_labels = [f"{i+1}. {row['階段']}" for i, row in edited_df.iterrows()] 
    
    for i, row in edited_df.iterrows():
        plot_list.append(dict(
            階段ID=i,
            階段名稱=y_labels[i],
            開始=row['預計開始'], 
            結束=row['預計結束'],
            開始標籤=row['預計開始'].strftime('%m/%d'),
            結束標籤=row['預計結束'].strftime('%m/%d')
        ))
    
    plot_data = pd.DataFrame(plot_list)
    
    start_view = plot_data['開始'].min() - timedelta(days=25)
    end_view = plot_data['結束'].max() + timedelta(days=25)
    
    fig = px.timeline(
        plot_data, 
        x_start="開始", 
        x_end="結束", 
        y="階段ID", 
        color_discrete_sequence=["#34C9A9"]
    )
    
    new_annotations = []
    for i, row in plot_data.iterrows():
        new_annotations.append(dict(
            x=row['開始'], y=i, text=row['開始標籤'],
            showarrow=False, xanchor='right', xshift=-10,
            font=dict(size=12, color="#1A1A1A")
        ))
        new_annotations.append(dict(
            x=row['結束'], y=i, text=row['結束標籤'],
            showarrow=False, xanchor='left', xshift=10,
            font=dict(size=12, color="#1A1A1A")
        ))
    
    fig.update_layout(annotations=new_annotations)
    
    fig.update_xaxes(
        type="date",
        range=[start_view, end_view],
        tickformat="%Y\n%m月", 
        dtick="M1", 
        showgrid=True,
        gridcolor='LightGrey', 
        side="top",
        title=None,
        rangeslider=dict(visible=False),
        tickfont=dict(size=14, color="#1A1A1A", family="Arial, sans-serif")
    )
    
    fig.update_yaxes(
        title=None, 
        autorange="reversed",
        automargin=True,
        tickmode="array",
        tickvals=plot_data['階段ID'],
        ticktext=plot_data['階段名稱'],
        ticklabelstandoff=15, 
        tickfont=dict(size=18, color="#1A1A1A", family="Arial, sans-serif"),
        side="left"
    )
    
    fig.update_layout(
        height=480, 
        margin=dict(l=180, r=100, t=100, b=40),
        showlegend=False,
        dragmode="pan", 
        font=dict(size=14, color="#1A1A1A")
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True, 'modeBarButtonsToRemove': ['select2d', 'lasso2d']})

elif menu == "🖼️ 基地照片":
    st.title("🖼️ 基地照片紀錄")
    st.info(f"當前檢視專案：{current_project}")
    st.file_uploader("請選擇照片上傳", type=["jpg", "png", "jpeg"])

elif menu == "⚖️ 相關法規":
    st.title("⚖️ 相關法規查詢")
    st.text_input("🔍 請輸入關鍵字搜尋")
    st.link_button("全國法規資料庫", "https://law.moj.gov.tw/")