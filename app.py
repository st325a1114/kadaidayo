import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# --- 1. アプリの設定 ---
st.set_page_config(page_title="24hスケジュール管理", layout="wide")

# セッションステートの初期化
if 'events' not in st.session_state:
    st.session_state.events = []

st.title("⏰ 24時間スケジュール可視化アプリ")

# --- 2. サイドバー：予定の入力 ---
st.sidebar.header("📝 予定を追加")

with st.sidebar.form("input_form", clear_on_submit=True):
    name = st.text_input("活動名", placeholder="例：昼食、睡眠、仕事")
    
    col1, col2 = st.columns(2)
    start = col1.time_input("開始時刻", datetime.time(9, 0))
    end = col2.time_input("終了時刻", datetime.time(10, 0))
    
    submitted = st.form_submit_button("追加する")
    
    if submitted:
        if name:
            # 時刻を分単位に変換
            start_m = start.hour * 60 + start.minute
            end_m = end.hour * 60 + end.minute
            
            if start_m < end_m:
                duration = end_m - start_m
                st.session_state.events.append({
                    "活動名": name,
                    "開始時刻": start,
                    "終了時刻": end,
                    "開始(分)": start_m,
                    "終了(分)": end_m,
                    "所要時間(分)": duration
                })
                st.success(f"「{name}」を追加しました！")
            else:
                st.error("終了時刻は開始時刻より後にしてください。")
        else:
            st.error("活動名を入力してください。")

# --- 3. データ処理（24時間を埋めるロジック） ---
def get_plot_data():
    # 1440分（24時間）の配列を作成
    day_map = ["予定なし"] * 1440
    
    # 入力された予定を配列に書き込む
    for event in st.session_state.events:
        for m in range(event["開始(分)"], event["終了(分)"]):
            if m < 1440:
                day_map[m] = event["活動名"]
    
    # 連続した活動をまとめてリスト化
    processed_data = []
    if not day_map: return pd.DataFrame()
    
    current_act = day_map[0]
    start_time = 0
    
    for i in range(1, 1440):
        if day_map[i] != current_act:
            processed_data.append({
                "活動名": current_act,
                "時間(分)": i - start_time,
                "開始": start_time
            })
            current_act = day_map[i]
            start_time = i
    # 最後の要素を追加
    processed_data.append({
        "活動名": current_act,
        "時間(分)": 1440 - start_time,
        "開始": start_time
    })
    
    return pd.DataFrame(processed_data)

df_plot = get_plot_data()

# --- 4. メイン画面：グラフ表示 ---
if not st.session_state.events:
    st.info("左側のメニューから予定を追加してください。")
else:
    # Plotlyで円グラフ作成
    fig = px.pie(
        df_plot, 
        values='時間(分)', 
        names='活動名',
        hole=0.4,
        color='活動名',
        # 「予定なし」をグレーにするなどの色指定（任意）
        color_discrete_map={"予定なし": "#f0f2f6"} 
    )

    # 0時を真上（90度）にし、時計回りに回転させる
    fig.update_traces(
        direction='clockwise', 
        sort=False, 
        rotation=90,
        textinfo='label+percent',
        hovertemplate="<b>%{label}</b><br>時間: %{value}分<extra></extra>"
    )

    # 中心に合計時間を表示
    fig.add_annotation(text="24時間", showarrow=False, font_size=20)

    st.plotly_chart(fig, use_container_width=True)
    
    

# --- 5. データの管理（テーブル表示と削除） ---
st.subheader("現在のリスト")
if st.session_state.events:
    df_list = pd.DataFrame(st.session_state.events)[["活動名", "開始時刻", "終了時刻", "所要時間(分)"]]
    st.table(df_list)
    
    if st.button("全データをリセット"):
        st.session_state.events = []
        st.rerun()