import streamlit as st
import time

# --- 頁面與視覺設定 (針對 iPad Air 13" 最佳化) ---
st.set_page_config(page_title="社區健康挑戰賽 - 計分計時板", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #121212; }
    h1, h2, h3, p, span, div, label { color: #FFFFFF !important; }
    h1 { font-size: 3rem !important; }
    h2 { font-size: 2.5rem !important; }
    h3 { font-size: 2rem !important; }
    .stButton>button { 
        background-color: #2A2A2A !important; 
        color: #FFFFFF !important; 
        border: 2px solid #555555 !important; 
        font-weight: bold; 
        font-size: 24px !important;
        padding: 15px 30px !important;
        border-radius: 12px !important;
        min-height: 80px;
        width: 100%;
    }
    .stButton>button:hover { 
        border-color: #4CAF50 !important; 
        color: #4CAF50 !important; 
    }
    input[type="number"] {
        font-size: 30px !important;
        text-align: center !important;
        height: 60px !important;
        background-color: #333333 !important;
        color: #FFFFFF !important;
    }
    .winner-text { color: #FFD700 !important; font-size: 32px; font-weight: bold; }
    .seed-text { color: #00FFFF !important; font-size: 24px; font-weight: bold; }
    .vs-text { text-align: center; font-size: 40px; font-weight: 900; color: #888888; padding-top: 20px;}
</style>
""", unsafe_allow_html=True)

# --- 狀態初始化 ---
defaults = {
    'mode': "模式A: PK淘汰賽",
    'team_count': 5,
    'round_stage': 1,
    'mistakes': {},
    'advancing': [],
    'show_results': False,
    'tournament_state': {},
    'champion': None,          # ✅ 新增：儲存冠軍名稱
    'timer_end': None,         # ✅ 新增：計時器結束時間
    'timer_label': "",
    'timer_color': "#00FFFF",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def reset_game():
    st.session_state.round_stage = 1
    st.session_state.mistakes = {f"第{i}組": 0 for i in range(1, 9)}
    st.session_state.advancing = []
    st.session_state.show_results = False
    st.session_state.tournament_state = {}
    st.session_state.champion = None  # ✅ 重置冠軍

# --- 側邊欄控制中心 ---
with st.sidebar:
    st.title("⚙️ 裁判控制台")
    new_mode = st.radio("選擇賽制模式", ["模式A: PK淘汰賽", "模式B: 純計時賽"], index=0)
    if new_mode != st.session_state.mode:
        st.session_state.mode = new_mode
        reset_game()
        
    if st.session_state.mode == "模式A: PK淘汰賽":
        new_tc = st.selectbox("參賽總組數", [5, 6, 7, 8], index=0)
        if new_tc != st.session_state.team_count:
            st.session_state.team_count = new_tc
            reset_game()
            
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 重新開始賽事"):
        reset_game()
        st.rerun()
    
    st.markdown("---")
    st.markdown("### ⏱️ 快速計時器")
    timer_placeholder = st.empty()

    # ✅ 修正：非阻塞計時器，用 session_state 記錄結束時間
    col1, col2 = st.columns(2)
    with col1:
        if st.button("30秒\n暖身"):
            st.session_state.timer_end = time.time() + 30
            st.session_state.timer_label = "暖身倒數"
            st.session_state.timer_color = "#00FFFF"
    with col2:
        if st.button("2分鐘\n正式"):
            st.session_state.timer_end = time.time() + 120
            st.session_state.timer_label = "正式比賽"
            st.session_state.timer_color = "#4CAF50"

    # 顯示計時器狀態
    if st.session_state.timer_end:
        remaining = int(st.session_state.timer_end - time.time())
        if remaining > 0:
            timer_placeholder.markdown(
                f"<h2 style='text-align:center; color:{st.session_state.timer_color} !important;'>"
                f"{st.session_state.timer_label}: {remaining} 秒</h2>",
                unsafe_allow_html=True
            )
            time.sleep(1)
            st.rerun()
        else:
            timer_placeholder.markdown(
                f"<h2 style='text-align:center; color:#FF4444 !important;'>⏰ 時間到！</h2>",
                unsafe_allow_html=True
            )
            st.session_state.timer_end = None

# --- 主畫面區 ---
st.title("🏆 社區健康挑戰賽 - 賽況看板")

# ✅ 修正 Bug 1：冠軍已產生時直接顯示，不再依賴 advancing
if st.session_state.champion:
    st.balloons()
    st.markdown("<h1 style='text-align:center; color:#FFD700 !important;'>🏆 最終總冠軍誕生！ 🏆</h1>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center;'>恭喜：<span style='color:#FFD700;'>{st.session_state.champion}</span></h1>", unsafe_allow_html=True)
    st.stop()

# --- 模式 B ---
if st.session_state.mode == "模式B: 純計時賽":
    st.markdown("### 模式 B：純計時賽 (獨立進行，不捉對廝殺)")
    st.info("計分標準：結算正式比賽 2 分鐘內累計「失誤數最少」的組別獲勝。失誤包含：過低、偏離Range、停滯。")
    
    cols = st.columns(6)
    for i in range(1, 7):
        team_name = f"第{i}組"
        if team_name not in st.session_state.mistakes:
            st.session_state.mistakes[team_name] = 0
        with cols[i-1]:
            if i in [5, 6]:
                st.markdown(f"<h3>{team_name}<br><span class='seed-text'>(友善組)</span></h3>", unsafe_allow_html=True)
            else:
                st.markdown(f"<h3>{team_name}</h3>", unsafe_allow_html=True)
            st.session_state.mistakes[team_name] = st.number_input(
                "失誤數", min_value=0, value=st.session_state.mistakes[team_name], key=f"modeB_{team_name}"
            )
            
    st.markdown("---")
    if st.button("🏁 結算純計時賽總成績"):
        results = [(team, st.session_state.mistakes[team]) for team in [f"第{i}組" for i in range(1, 7)]]
        results.sort(key=lambda x: x[1])
        st.markdown("## 🏆 賽事結果")
        st.markdown(f"<span class='winner-text'>🥇 最終總冠軍：{results[0][0]} (失誤 {results[0][1]} 次)</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='winner-text'>🥈 亞軍隊伍：{results[1][0]} (失誤 {results[1][1]} 次)</span>", unsafe_allow_html=True)

# --- 模式 A ---
elif st.session_state.mode == "模式A: PK淘汰賽":
    tc = st.session_state.team_count
    stage = st.session_state.round_stage
    
    st.markdown(f"### 模式 A：PK 淘汰賽 ({tc} 組方案)")
    matchups = []
    
    if tc == 5:
        if stage == 1:
            matchups = [("第1組", "第2組"), ("第3組", "第4組")]
            st.markdown("<p class='seed-text'>💡 第 5 組為種子隊伍，直接進入最終決賽圈。</p>", unsafe_allow_html=True)
        elif stage == 2:
            matchups = [(st.session_state.tournament_state.get('w_1_2', '1/2勝方'), 
                         st.session_state.tournament_state.get('w_3_4', '3/4勝方'))]
        elif stage == 3:
            matchups = [(st.session_state.tournament_state.get('w_semi', '準決賽勝方'), "第5組(種子隊伍)")]
            
    elif tc == 6:
        if stage == 1:
            matchups = [("第1組", "第2組"), ("第3組", "第4組"), ("第5組(友善)", "第6組(友善)")]
            st.markdown("<p class='seed-text'>💡 第 5、6 組進行友善專屬對戰，勝方進入決賽圈。</p>", unsafe_allow_html=True)
        elif stage == 2:
            matchups = [(st.session_state.tournament_state.get('w_1_2', '1/2勝方'), 
                         st.session_state.tournament_state.get('w_3_4', '3/4勝方'))]
        elif stage == 3:
            matchups = [(st.session_state.tournament_state.get('w_semi', '準決賽勝方'), 
                         st.session_state.tournament_state.get('w_5_6', '5/6勝方'))]
            
    elif tc == 7:
        if stage == 1:
            matchups = [("第1組", "第2組"), ("第3組", "第4組"), ("第5組", "第6組")]
            st.markdown("<p class='seed-text'>💡 第 7 組為種子隊伍，首輪輪空，直接進入準決賽。</p>", unsafe_allow_html=True)
        elif stage == 2:
            # ✅ 修正 Bug 4：正確使用已儲存的 w_5_6 而非硬寫
            matchups = [(st.session_state.tournament_state.get('w_1_2', '1/2勝方'), 
                         st.session_state.tournament_state.get('w_3_4', '3/4勝方')),
                        (st.session_state.tournament_state.get('w_5_6', '5/6勝方'), 
                         "第7組(種子隊伍)")]
        elif stage == 3:
            matchups = [(st.session_state.tournament_state.get('w_semi_1', '準決賽A區勝方'), 
                         st.session_state.tournament_state.get('w_semi_2', '準決賽B區勝方'))]
            
    elif tc == 8:
        if stage == 1:
            matchups = [("第1組", "第2組"), ("第3組", "第4組"), ("第5組", "第6組"), ("第7組", "第8組")]
        elif stage == 2:
            matchups = [(st.session_state.tournament_state.get('w_1_2', '1/2勝方'), 
                         st.session_state.tournament_state.get('w_3_4', '3/4勝方')),
                        (st.session_state.tournament_state.get('w_5_6', '5/6勝方'), 
                         st.session_state.tournament_state.get('w_7_8', '7/8勝方'))]
        elif stage == 3:
            matchups = [(st.session_state.tournament_state.get('w_semi_1', '準決賽A區勝方'), 
                         st.session_state.tournament_state.get('w_semi_2', '準決賽B區勝方'))]

    # 顯示對戰 UI
    if matchups:
        st.markdown(f"## 📍 當前賽程：第 {stage} 輪")
        st.markdown("<br>", unsafe_allow_html=True)
        
        for idx, match in enumerate(matchups):
            col1, col2, col3 = st.columns([3, 1, 3])
            team_a, team_b = match
            
            with col1:
                st.markdown(f"<h3>{team_a}</h3>", unsafe_allow_html=True)
                if team_a not in st.session_state.mistakes:
                    st.session_state.mistakes[team_a] = 0
                st.session_state.mistakes[team_a] = st.number_input(
                    "失誤數", min_value=0, value=st.session_state.mistakes[team_a],
                    key=f"modeA_{team_a}_{stage}"  # ✅ 修正 Bug 5：前綴改為 modeA_
                )
            with col2:
                st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<h3>{team_b}</h3>", unsafe_allow_html=True)
                if team_b not in st.session_state.mistakes:
                    st.session_state.mistakes[team_b] = 0
                st.session_state.mistakes[team_b] = st.number_input(
                    "失誤數", min_value=0, value=st.session_state.mistakes[team_b],
                    key=f"modeA_{team_b}_{stage}"
                )
            st.markdown("<hr style='border:1px solid #444;'>", unsafe_allow_html=True)

    # 結算按鈕
    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔒 結算本輪成績 (鎖定分數)"):
            winners = []
            for match in matchups:
                t_a, t_b = match
                score_a = st.session_state.mistakes.get(t_a, 0)
                score_b = st.session_state.mistakes.get(t_b, 0)
                winner = t_a if score_a <= score_b else t_b
                winners.append(winner)
            st.session_state.advancing = winners
            st.session_state.show_results = False
            st.success("✅ 成績已鎖定！請點擊右側按鈕向全場揭曉晉級名單。")
    with col_btn2:
        if st.button("📢 大螢幕揭曉晉級名單"):
            st.session_state.show_results = True

    # 揭曉結果
    if st.session_state.show_results and st.session_state.advancing:
        st.markdown("## 🎉 本輪晉級名單 🎉")
        for w in st.session_state.advancing:
            st.markdown(f"<span class='winner-text'>⭐ 恭喜 【{w}】 晉級下一輪！</span>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)

        is_final = (stage == 3)  # ✅ 第3輪結束 = 決賽結束

        if is_final:
            # ✅ 修正 Bug 1 & 2：決賽後顯示冠軍按鈕，不再有「下一輪」
            if st.button("🏆 正式宣佈總冠軍！", type="primary"):
                st.session_state.champion = st.session_state.advancing[0]
                st.rerun()
        else:
            if st.button("➡️ 載入下一輪賽程", type="primary"):
                adv = st.session_state.advancing
                ts = st.session_state.tournament_state
                
                if tc == 5:
                    if stage == 1: ts['w_1_2'], ts['w_3_4'] = adv[0], adv[1]
                    elif stage == 2: ts['w_semi'] = adv[0]
                elif tc == 6:
                    if stage == 1: ts['w_1_2'], ts['w_3_4'], ts['w_5_6'] = adv[0], adv[1], adv[2]
                    elif stage == 2: ts['w_semi'] = adv[0]
                elif tc == 7:
                    if stage == 1: ts['w_1_2'], ts['w_3_4'], ts['w_5_6'] = adv[0], adv[1], adv[2]
                    elif stage == 2: ts['w_semi_1'], ts['w_semi_2'] = adv[0], adv[1]
                elif tc == 8:
                    if stage == 1: ts['w_1_2'], ts['w_3_4'], ts['w_5_6'], ts['w_7_8'] = adv[0], adv[1], adv[2], adv[3]
                    elif stage == 2: ts['w_semi_1'], ts['w_semi_2'] = adv[0], adv[1]
                    
                st.session_state.round_stage += 1
                st.session_state.advancing = []
                st.session_state.show_results = False
                for key in list(st.session_state.mistakes.keys()):
                    st.session_state.mistakes[key] = 0
                st.rerun()
