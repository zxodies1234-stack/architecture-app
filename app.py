import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
import os
import matplotlib.pyplot as plt
from io import BytesIO

# --- 基礎設定 ---
# 修正點：確保在雲端能正確定位專案資料夾
SAVE_DIR = "projects"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

st.set_page_config(layout="wide", page_title="建築專案管理系統")

# --- 定義狀態選項 ---
STATUS_OPTIONS = [
    "未開始", 
    "作業中", 
    "掛件中", 
    "已完成", 
    "🟣 作業要徑", 
    "🔴 遇到問題"
]

# --- 讀取資料函式 ---
def load_project_data(path):
    # 修正點：增加檔案存在且有內容的判斷
    if os.path.exists(path) and os.path.getsize(path) > 10: 
        df = pd.read_csv(path)
        if "狀態" not in df.columns:
            df["狀態"] = "未開始"
        
        # 數據清理
        df["狀態"] = df["狀態"].replace({
            "★作業要徑": "🟣 作業要徑",
            "🟣 ★作業要徑": "🟣 作業要徑",
            "!遇到問題!": "🔴 遇到問題",
            "🔴 !遇到問題!": "🔴 遇到問題"
        })
        
        df['預計開始'] = pd.to_datetime(df['預計開始']).dt.date
        df['預計結束'] = pd.to_datetime(df['預計結束']).dt.date
        df['實際結束'] = pd.to_datetime(df['實際結束']).dt.date
        return df
    else:
        # 初始範例資料
        stages = ["設計初期", "圖面規劃", "圖面檢討", "都審", "建照", "施工圖"]
        data = []
        for s in stages:
            data.append({
                "階段": s, "狀態": "未開始",
                "預計開始": date.today(), "預計結束": date.today() + timedelta(days=30),
                "實際結束": date.today() + timedelta(days=30), "子任務數": 5, "完成數": 0, "進度(%)": 0
            })
        return pd.DataFrame(data)

# --- 專案管理側邊欄 ---
st.sidebar.title("🏢 專案管理")

# 修正點：列出所有 CSV 並排除隱藏檔案
all_projects = [f.replace(".csv", "") for f in os.listdir(SAVE_DIR) if f.endswith(".csv")]

if not all_projects:
    # 如果 GitHub 上沒抓到資料夾，先建立一個預設檔防止崩潰
    default_name = "預設專案"
    default_path = os.path.join(SAVE_DIR, f"{default_name}.csv")
    if not os.path.exists(default_path):
        load_project_data(default_path).to_csv(default_path, index=False)
    all_projects = [default_name]

current_project = st.sidebar.selectbox("📂 切換現有專案", all_projects)
save_path = os.path.join(SAVE_DIR, f"{current_project}.csv")
df = load_project_data(save_path)

# --- 數據更新面板 ---
st.sidebar.divider()
st.sidebar.header(f"📝 編輯：{current_project}")
updated_rows = []

for i, row in df.iterrows():
    with st.sidebar.expander(f"📌 {row['階段']} ({row['狀態']})"):
        # 防止狀態不在選項中導致出錯
        state_idx = STATUS_OPTIONS.index(row['狀態']) if row['狀態'] in STATUS_OPTIONS else 0
        selected_status = st.selectbox("修改狀態", STATUS_OPTIONS, index=state_idx, key=f"st_{i}")
        
        c1, c2 = st.columns(2)
        p_start = c1.date_input("預計開始", value=row['預計開始'], key=f"ps_{i}")
        p_end = c2.date_input("預計結束", value=row['預計結束'], key=f"pe_{i}")
        
        col_sub1, col_sub2 = st.columns(2)
        total_sub = col_sub1.number_input("子任務數", value=int(row['子任務數']), min_value=1, key=f"ts_{i}")
        done_sub = col_sub2.number_input("完成數", value=int(row['完成數']), min_value=0, max_value=total_sub, key=f"ds_{i}")
        
        r_end = st.date_input("實際結束", value=row['實際結束'], key=f"re_{i}")
        prog = int((done_sub / total_sub) * 100)
        
        final_status = selected_status
        if prog == 100 and final_status not in ["🟣 作業要徑", "🔴 遇到問題"]:
            final_status = "已完成"
        elif prog > 0 and final_status == "未開始":
            final_status = "作業中"

        updated_rows.append({
            "階段": row['階段'], "狀態": final_status, "預計開始": p_start, "預計結束": p_end, 
            "實際結束": r_end, "子任務數": total_sub, "完成數": done_sub, "進度(%)": prog
        })

if st.sidebar.button("💾 儲存數據"):
    pd.DataFrame(updated_rows).to_csv(save_path, index=False)
    st.sidebar.success("✅ 數據已更新！(注意：雲端版重整後將恢復 GitHub 初始狀態)")
    st.rerun()

# --- 主畫面視覺化 ---
st.title(f"🏢 建築專案進度：{current_project}")

# 甘特圖修正：確保圖表資料不為空
if not df.empty:
    chart_list = []
    for _, r in df.iterrows():
        chart_list.append(dict(階段=r['階段'], 時間=r['預計開始'], 類型='預計', 結束=r['預計結束'], 狀態=r['狀態']))
        chart_list.append(dict(階段=r['階段'], 時間=r['預計開始'], 類型='實際', 結束=r['實際結束'], 狀態=r['狀態']))

    fig = px.timeline(pd.DataFrame(chart_list), x_start="時間", x_end="結束", y="階段", color="類型",
                     color_discrete_map={"預計": "#E5ECF6", "實際": "#19D3AF"}, 
                     hover_data={"狀態": True})
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

# --- 詳細表格 ---
st.subheader("📋 詳細進度清單")

def highlight_status(val):
    if val == "已完成": return 'background-color: #d4edda; color: #155724;'
    if val == "作業中": return 'background-color: #fff3cd; color: #856404;'
    if val == "掛件中": return 'background-color: #cce5ff; color: #004085;'
    if "作業要徑" in val: return 'background-color: #f3e5f5; color: #6a1b9a; font-weight: bold;'
    if "遇到問題" in val: return 'background-color: #fdecea; color: #c62828; font-weight: bold;'
    return ''

styled_df = df.style.map(highlight_status, subset=['狀態'])
st.dataframe(styled_df, use_container_width=True, hide_index=True)

# --- PDF 匯出 (雲端環境字體警告處理) ---
def export_pdf(df_to_pdf):
    # 注意：Streamlit Cloud (Linux) 通常沒有微軟正黑體，這部分在雲端可能會亂碼
    # 建議之後改用 HTML 轉 PDF 或僅限本地端使用
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans'] # 改用雲端通用字體，但中文會變豆腐塊
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axis('tight'); ax.axis('off')
    ax.table(cellText=[df_to_pdf.columns.tolist()] + df_to_pdf.values.tolist(), loc='center', cellLoc='center').scale(1.2, 2)
    buf = BytesIO()
    plt.savefig(buf, format="pdf", bbox_inches='tight')
    buf.seek(0)
    return buf

st.download_button("📥 匯出 PDF 報告 (中文在雲端版可能受限)", data=export_pdf(df), file_name=f"{current_project}_report.pdf")