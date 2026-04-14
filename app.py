import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
import os

# --- 基礎路徑設定 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "projects")
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

st.set_page_config(layout="wide", page_title="建築專案管理系統")

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
st.sidebar.title("🚀 主要功能")
menu = st.sidebar.radio(
    label="導覽選單", 
    options=["📝 專案進度", "📐 面積表", "🖼️ 基地照片", "⚖️ 相關法規"], 
    label_visibility="collapsed"
)

save_path = os.path.join(SAVE_DIR, f"{current_project}.csv")
df = load_project_data(save_path)

# --- 右側顯示區 ---

if menu == "📝 專案進度":
    st.title(f"🏢 專案進度：{current_project}")
    col_h1, col_h2 = st.columns([8.5, 1.5])
    with col_h1: st.subheader("📋 工作清單")
    with col_h2: save_btn = st.button("儲存變更", key="save_gantt")
    edited_df = st.data_editor(df, hide_index=True, use_container_width=True, key="main_editor")
    if save_btn:
        edited_df.to_csv(save_path, index=False)
        st.success("✅ 已儲存變更")
        st.rerun()
    st.divider()
    
    st.subheader("📊 工程進度表") 
    plot_list = []
    for i, row in edited_df.iterrows():
        plot_list.append(dict(
            階段ID=i, 階段名稱=f"{i+1}. {row['階段']}", 
            開始=row['預計開始'], 結束=row['預計結束'], 
            開始標籤=row['預計開始'].strftime('%m/%d'), 結束標籤=row['預計結束'].strftime('%m/%d')
        ))
    plot_data = pd.DataFrame(plot_list)
    fig = px.timeline(plot_data, x_start="開始", x_end="結束", y="階段ID", color_discrete_sequence=["#34C9A9"])
    
    new_annotations = []
    for i, row in plot_data.iterrows():
        new_annotations.append(dict(x=row['開始'], y=i, text=row['開始標籤'], showarrow=False, xanchor='right', xshift=-10, font=dict(size=12, color="#1A1A1A")))
        new_annotations.append(dict(x=row['結束'], y=i, text=row['結束標籤'], showarrow=False, xanchor='left', xshift=10, font=dict(size=12, color="#1A1A1A")))
    
    fig.update_layout(annotations=new_annotations, height=480, margin=dict(l=180, r=100, t=100, b=40), showlegend=False, font=dict(size=14))
    fig.update_xaxes(type="date", tickformat="%Y\n%m月", side="top")
    fig.update_yaxes(autorange="reversed", tickvals=plot_data['階段ID'], ticktext=plot_data['階段名稱'])
    st.plotly_chart(fig, use_container_width=True)

elif menu == "📐 面積表":
    st.title(f"📐 面積檢討總表：{current_project}")
    st.caption("※ 修改數值後請點擊下方「更新並計算」以同步數據")

    # 通用欄位設定
    area_config_base = {
        "編號": st.column_config.TextColumn("編號", width="small", alignment="center"),
        "項目": st.column_config.TextColumn("項目", width="medium"),
        "內容/數值": st.column_config.TextColumn("內容/數值", width="medium"),
        "備註": st.column_config.TextColumn("備註", width="large"),
    }

    # 對照式表格專用設定
    compare_config = {
        "編號": st.column_config.TextColumn("編號", width="small", alignment="center"),
        "項目": st.column_config.TextColumn("項目檢討", width="medium"),
        "法定": st.column_config.TextColumn("法定 (上限/應設)", width="medium"),
        "實設": st.column_config.TextColumn("實設", width="medium"),
        "備註": st.column_config.TextColumn("備註", width="large"),
    }

    # 1. 基地基本資料
    if 'area_block1' not in st.session_state:
        st.session_state.area_block1 = pd.DataFrame([
            {"編號": "1", "項目": "基地地號", "內容/數值": "大安區段001號", "備註": "-"},
            {"編號": "2", "項目": "使用分區", "內容/數值": "第三種住宅區", "備註": "-"},
            {"編號": "3", "項目": "謄本面積(㎡)", "內容/數值": "505.20", "備註": "-"},
            {"編號": "4", "項目": "基地面積(㎡)", "內容/數值": "500.00", "備註": "-"}
        ])

    # 2. 建蔽率與建築面積檢討 (對照式)
    if 'area_block2_compare' not in st.session_state:
        st.session_state.area_block2_compare = pd.DataFrame([
            {"編號": "1", "項目": "建蔽率 (%)", "法定": "45.0", "實設": "43.0", "備註": "-"},
            {"編號": "2", "項目": "建築面積 (㎡)", "法定": "225.00", "實設": "215.00", "備註": "自動計算"},
            {"編號": "3", "項目": "空地面積 (㎡)", "法定": "275.00", "實設": "285.00", "備註": "自動計算"}
        ])

    # 3. 開挖深度檢討 (對照式)
    if 'area_block_exc_compare' not in st.session_state:
        st.session_state.area_block_exc_compare = pd.DataFrame([
            {"編號": "1", "項目": "開挖率 (%)", "法定": "70.0", "實設": "68.5", "備註": "-"},
            {"編號": "2", "項目": "開挖面積 (㎡)", "法定": "350.00", "實設": "342.50", "備註": "自動計算"}
        ])

    # 4. 容積率與樓地板面積檢討
    if 'area_block_vol' not in st.session_state:
        st.session_state.area_block_vol = pd.DataFrame([
            {"編號": "1", "項目": "法定容積率(%)", "內容/數值": "225.0", "備註": "-"},
            {"編號": "2", "項目": "法定容積面積(㎡)", "內容/數值": "1125.00", "備註": "自動計算"},
            {"編號": "3", "項目": "容積獎勵(%)", "內容/數值": "10.0", "備註": "危老獎勵"},
            {"編號": "4", "項目": "容積獎勵面積(㎡)", "內容/數值": "112.50", "備註": "自動計算"},
            {"編號": "5", "項目": "容積移轉(%)", "內容/數值": "15.0", "備註": "代金繳納"},
            {"編號": "6", "項目": "容積移轉面積(㎡)", "內容/數值": "168.75", "備註": "自動計算"},
            {"編號": "7", "項目": "允建容積率(%)", "內容/數值": "281.25", "備註": "自動計算"},
            {"編號": "8", "項目": "允建容積面積(㎡)", "內容/數值": "1406.25", "備註": "自動計算"},
            {"編號": "9", "項目": "實設容積率(%)", "內容/數值": "248.5", "備註": "-"},
            {"編號": "10", "項目": "實設容積面積(㎡)", "內容/數值": "1242.50", "備註": "自動計算"}
        ])

    # 渲染表格
    st.markdown('<div style="background-color:#F0F2F6;padding:10px;border-radius:5px;margin-bottom:5px;"><b style="color:#1F4E79;">📍 基地基本資料</b></div>', unsafe_allow_html=True)
    ed1 = st.data_editor(st.session_state.area_block1, hide_index=True, use_container_width=True, key="ed1", column_config=area_config_base)

    st.markdown('<div style="background-color:#E8F4EA;padding:10px;border-radius:5px;margin-top:20px;margin-bottom:5px;"><b style="color:#2E7D32;">🏠 建蔽率與建築面積對照檢討</b></div>', unsafe_allow_html=True)
    ed2 = st.data_editor(st.session_state.area_block2_compare, hide_index=True, use_container_width=True, key="ed2", column_config=compare_config)

    st.markdown('<div style="background-color:#FDF5E6;padding:10px;border-radius:5px;margin-top:20px;margin-bottom:5px;"><b style="color:#8B4513;">🚜 開挖深度對照檢討</b></div>', unsafe_allow_html=True)
    ed_exc = st.data_editor(st.session_state.area_block_exc_compare, hide_index=True, use_container_width=True, key="ed_exc", column_config=compare_config)

    st.markdown('<div style="background-color:#FFF4E5;padding:10px;border-radius:5px;margin-top:20px;margin-bottom:5px;"><b style="color:#D35400;">🏢 容積率與樓地板面積檢討</b></div>', unsafe_allow_html=True)
    ed_vol = st.data_editor(st.session_state.area_block_vol, hide_index=True, use_container_width=True, key="ed_vol", column_config=area_config_base)

    # 更新計算邏輯
    col_s1, col_s2 = st.columns([8.5, 1.5])
    with col_s2:
        if st.button("更新並計算", key="save_area"):
            def get_f(df, row_no, col_name="內容/數值"):
                try:
                    val = df.loc[df['編號'] == str(row_no), col_name].values[0]
                    return float(str(val).replace(',', ''))
                except: return 0.0

            # 基礎值
            base_a = get_f(ed1, 4)
            
            # 建蔽率更新 (ed2)
            l_cov_p = get_f(ed2, 1, "法定") / 100
            a_cov_p = get_f(ed2, 1, "實設") / 100
            
            def update_ed2(df):
                df = df.copy()
                df.loc[df['編號'] == "2", "法定"] = f"{base_a * l_cov_p:,.2f}"
                df.loc[df['編號'] == "2", "實設"] = f"{base_a * a_cov_p:,.2f}"
                df.loc[df['編號'] == "3", "法定"] = f"{base_a * (1 - l_cov_p):,.2f}"
                df.loc[df['編號'] == "3", "實設"] = f"{base_a * (1 - a_cov_p):,.2f}"
                return df

            # 開挖率更新 (ed_exc)
            l_exc_p = get_f(ed_exc, 1, "法定") / 100
            a_exc_p = get_f(ed_exc, 1, "實設") / 100

            def update_exc(df):
                df = df.copy()
                df.loc[df['編號'] == "2", "法定"] = f"{base_a * l_exc_p:,.2f}"
                df.loc[df['編號'] == "2", "實設"] = f"{base_a * a_exc_p:,.2f}"
                return df

            # 容積更新 (ed_vol)
            v_l_p = get_f(ed_vol, 1) / 100
            v_b_p = get_f(ed_vol, 3) / 100
            v_t_p = get_f(ed_vol, 5) / 100
            v_a_p = get_f(ed_vol, 9) / 100

            def update_vol(df):
                df = df.copy()
                df.loc[df['編號'] == "2", '內容/數值'] = f"{base_a * v_l_p:,.2f}"
                df.loc[df['編號'] == "4", '內容/數值'] = f"{base_a * v_l_p * v_b_p:,.2f}"
                df.loc[df['編號'] == "6", '內容/數值'] = f"{base_a * v_l_p * v_t_p:,.2f}"
                all_ratio = v_l_p * (1 + v_b_p + v_t_p)
                df.loc[df['編號'] == "7", '內容/數值'] = f"{all_ratio*100:,.2f}"
                df.loc[df['編號'] == "8", '內容/數值'] = f"{base_a * all_ratio:,.2f}"
                df.loc[df['編號'] == "10", '內容/數值'] = f"{base_a * v_a_p:,.2f}"
                return df

            st.session_state.area_block1 = ed1
            st.session_state.area_block2_compare = update_ed2(ed2)
            st.session_state.area_block_exc_compare = update_exc(ed_exc)
            st.session_state.area_block_vol = update_vol(ed_vol)
            st.success("✅ 計算已完成對照更新")
            st.rerun()

elif menu == "🖼️ 基地照片":
    st.title("🖼️ 基地照片紀錄")
    st.file_uploader("上傳照片", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

elif menu == "⚖️ 相關法規":
    st.title("⚖️ 相關法規查詢")
    st.link_button("台北市法規查詢系統", "https://www.laws.taipei.gov.tw/")