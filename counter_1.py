import streamlit as st
import time

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
    .silver-text { color: #C0C0C0 !important; font-size: 28px; font-weight: bold; }
    .fewest-award-box {
        background: linear-gradient(135deg, #0d1a2d, #1a2d40);
        border: 3px solid #4FC3F7;
        border-radius: 16px;
        padding: 24px 32px;
        margin: 20px 0;
        box-shadow: 0 0 30px rgba(79, 195, 247, 0.35);
    }
    .fewest-award-title {
        color: #4FC3F7 !important;
        font-size: 24px !important;
        font-weight: 900 !important;
        letter-spacing: 2px;
        margin-bottom: 8px;
    }
    .fewest-award-winner {
        color: #E1F5FE !important;
        font-size: 26px !important;
        font-weight: bold;
    }
    .seed-text { color: #00FFFF !important; font-size: 24px; font-weight: bold; }
    .vs-text { text-align: center; font-size: 40px; font-weight: 900; color: #888888; padding-top: 20px;}

    .tie-box {
        background: linear-gradient(135deg, #1a0a00, #2d1500);
        border: 3px solid #FF6600;
        border-radius: 16px;
        padding: 28px 32px;
        margin: 16px 0;
        box-shadow: 0 0 30px rgba(255, 102, 0, 0.4);
    }
    .tie-title {
        color: #FF6600 !important;
        font-size: 26px !important;
        font-weight: 900 !important;
        letter-spacing: 2px;
    }
    .tie-rule {
        color: #FFB366 !important;
        font-size: 20px !important;
        background-color: rgba(255,102,0,0.12);
        border-left: 4px solid #FF6600;
        padding: 10px 16px;
        border-radius: 6px;
        margin: 12px 0 20px 0;
    }
    .tie-teams {
        color: #FFFFFF !important;
        font-size: 22px !important;
        margin-bottom: 6px;
    }
    .tie-score {
        color: #FF6600 !important;
        font-size: 28px !important;
        font-weight: bold;
    }
    .tie-btn > div > button {
        background-color: #3D1A00 !important;
        border: 2px solid #FF6600 !important;
        color: #FFB366 !important;
        font-size: 22px !important;
    }
    .tie-btn > div > button:hover {
        background-color: #FF6600 !important;
        color: #FFFFFF !important;
        border-color: #FFFFFF !important;
    }
    .resolved-badge {
        color: #4CAF50 !important;
        font-size: 20px;
        font-weight: bold;
        padding: 8px 0;
    }
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
    'champion': None,
    'fewest_mistakes_winner': None,   # ✅ 最佳單場失誤最少獎得主
    'all_mistakes_log': {},           # ✅ 模式A: 記錄每隊各輪最佳（最少）單場失誤
    'timer_end': None,
    'timer_label': "",
    'timer_color': "#00FFFF",
    'tie_matches': [],
    'tie_resolutions': {},
    'locked_winners': [],
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
    st.session_state.champion = None
    st.session_state.fewest_mistakes_winner = None
    st.session_state.all_mistakes_log = {}
    st.session_state.tie_matches = []
    st.session_state.tie_resolutions = {}
    st.session_state.locked_winners = []

def accumulate_mistakes_log(matchups):
    """
    記錄本輪各隊失誤數。
    每隊只保留「歷輪最少」的那場（最佳單場），不累加。
    這樣打多輪的隊伍不會因場次多而吃虧。
    """
    log = st.session_state.all_mistakes_log
    for match in matchups:
        for team in match:
            score = st.session_state.mistakes.get(team, 0)
            if team not in log:
                log[team] = score
            else:
                log[team] = min(log[team], score)
    st.session_state.all_mistakes_log = log

def compute_fewest_mistakes_award_modeA(champion):
    """
    模式A：在所有曾參賽的隊伍中（排除冠軍），
    以「最佳單場失誤數」比較，找出最少者。
    若與冠軍最佳單場同分，則順延至次少者。
    """
    log = st.session_state.all_mistakes_log
    champion_score = log.get(champion, 0)
    candidates = [(team, score) for team, score in log.items() if team != champion]
    candidates.sort(key=lambda x: x[1])
    for team, score in candidates:
        if score != champion_score:
            return team, score
        # 若同分，繼續往下找
    # 若全同分（極端情況），取第一個非冠軍
    if candidates:
        return candidates[0][0], candidates[0][1]
    return None, None

def compute_fewest_mistakes_award_modeB(results):
    """
    模式B：results 為 [(team, score), ...] 已排序（失誤由少到多）。
    冠軍為 results[0]，最少失誤獎為 results[1]（第二少）。
    """
    if len(results) >= 2:
        return results[1][0], results[1][1]
    return None, None

# --- 側邊欄 ---
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
                "<h2 style='text-align:center; color:#FF4444 !important;'>⏰ 時間到！</h2>",
                unsafe_allow_html=True
            )
            st.session_state.timer_end = None

# --- 主畫面 ---
st.title("🏆 社區健康挑戰賽 - 賽況看板")

# ==================== 冠軍公布畫面（含最少失誤獎）====================
if st.session_state.champion:
    st.balloons()
    st.markdown("<h1 style='text-align:center; color:#FFD700 !important;'>🏆 最終總冠軍誕生！ 🏆</h1>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center;'>恭喜：<span style='color:#FFD700;'>{st.session_state.champion}</span></h1>", unsafe_allow_html=True)

    # ✅ 顯示失誤最少獎
    if st.session_state.fewest_mistakes_winner:
        fw, fs = st.session_state.fewest_mistakes_winner
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class='fewest-award-box'>
            <div class='fewest-award-title'>🎖️ 全場失誤最少特別獎</div>
            <div class='fewest-award-winner'>恭喜 【{fw}】<br>
                <span style='font-size:20px; color:#B3E5FC;'>最佳單場僅 {fs} 次失誤（排除總冠軍後最少）</span></div>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# ==================== 模式 B ====================
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

        champion_b = results[0][0]
        fw, fs = compute_fewest_mistakes_award_modeB(results)

        st.markdown("## 🏆 賽事結果")
        st.markdown(f"<span class='winner-text'>🥇 最終總冠軍：{champion_b} (失誤 {results[0][1]} 次)</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='winner-text'>🥈 亞軍隊伍：{results[1][0]} (失誤 {results[1][1]} 次)</span>", unsafe_allow_html=True)

        # ✅ 模式B：失誤第二少者為特別獎（即亞軍，非冠軍）
        if fw:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class='fewest-award-box'>
                <div class='fewest-award-title'>🎖️ 全場失誤最少特別獎</div>
                <div class='fewest-award-winner'>恭喜 【{fw}】<br>
                <span style='font-size:20px; color:#B3E5FC;'>失誤 {fs} 次（全場第二少，排除總冠軍）</span></div>
            </div>
            """, unsafe_allow_html=True)

# ==================== 模式 A ====================
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

    # --- 對戰 UI ---
    if matchups:
        st.markdown(f"## 📍 當前賽程：第 {stage} 輪")
        st.markdown("<br>", unsafe_allow_html=True)
        
        for match in matchups:
            col1, col2, col3 = st.columns([3, 1, 3])
            team_a, team_b = match
            
            with col1:
                st.markdown(f"<h3>{team_a}</h3>", unsafe_allow_html=True)
                if team_a not in st.session_state.mistakes:
                    st.session_state.mistakes[team_a] = 0
                st.session_state.mistakes[team_a] = st.number_input(
                    "失誤數", min_value=0, value=st.session_state.mistakes[team_a],
                    key=f"modeA_{team_a}_{stage}"
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

    # --- 結算按鈕 ---
    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button("🔒 結算本輪成績 (鎖定分數)"):
            clear_winners = []
            tie_list = []

            for match in matchups:
                t_a, t_b = match
                score_a = st.session_state.mistakes.get(t_a, 0)
                score_b = st.session_state.mistakes.get(t_b, 0)

                if score_a == score_b:
                    tie_list.append((t_a, t_b, score_a))
                else:
                    winner = t_a if score_a < score_b else t_b
                    clear_winners.append((match, winner))

            # ✅ 鎖定時累加本輪失誤到 log
            accumulate_mistakes_log(matchups)

            st.session_state.tie_matches = tie_list
            st.session_state.tie_resolutions = {}
            st.session_state.locked_winners = clear_winners
            st.session_state.show_results = False

            if tie_list:
                st.warning(f"⚠️ 偵測到 {len(tie_list)} 場同分！請在下方殊決窗格中由裁判選出晉級方。")
            else:
                st.success("✅ 成績已鎖定！無同分情況，請揭曉晉級名單。")

    with col_btn2:
        all_ties_resolved = len(st.session_state.tie_resolutions) == len(st.session_state.tie_matches)
        has_locked = bool(st.session_state.locked_winners) or bool(st.session_state.tie_matches)

        if st.button("📢 大螢幕揭曉晉級名單", disabled=(not has_locked or not all_ties_resolved)):
            final_winners = [w for (_, w) in st.session_state.locked_winners]
            for (t_a, t_b, _) in st.session_state.tie_matches:
                key = (t_a, t_b)
                if key in st.session_state.tie_resolutions:
                    final_winners.append(st.session_state.tie_resolutions[key])
            st.session_state.advancing = final_winners
            st.session_state.show_results = True

    # ✅ 同分殊決窗格
    if st.session_state.tie_matches:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("## ⚡ 同分殊決")

        for (t_a, t_b, tied_score) in st.session_state.tie_matches:
            key = (t_a, t_b)
            already_resolved = key in st.session_state.tie_resolutions
            resolved_winner = st.session_state.tie_resolutions.get(key, None)

            st.markdown(f"""
            <div class='tie-box'>
                <div class='tie-title'>🔥 同分殊決通知</div>
                <div class='tie-rule'>📋 殊決規則：先落地者輸（失誤同分時，以氣球/道具最先落地的隊伍判負）</div>
                <div class='tie-teams'>對戰雙方：<strong>{t_a}</strong> vs <strong>{t_b}</strong></div>
                <div class='tie-score'>同分：各 {tied_score} 次失誤</div>
            </div>
            """, unsafe_allow_html=True)

            if already_resolved:
                st.markdown(f"<div class='resolved-badge'>✅ 已選定晉級方：【{resolved_winner}】</div>", unsafe_allow_html=True)
                if st.button(f"↩️ 重新選擇（{t_a} vs {t_b}）", key=f"redo_{t_a}_{t_b}"):
                    del st.session_state.tie_resolutions[key]
                    st.session_state.show_results = False
                    st.rerun()
            else:
                st.markdown("<p style='color:#FFB366; font-size:20px;'>👇 裁判請點選晉級隊伍：</p>", unsafe_allow_html=True)
                tie_col1, tie_col2 = st.columns(2)
                with tie_col1:
                    st.markdown("<div class='tie-btn'>", unsafe_allow_html=True)
                    if st.button(f"🏅 {t_a} 晉級", key=f"tie_win_{t_a}_{t_b}_A"):
                        st.session_state.tie_resolutions[key] = t_a
                        st.session_state.show_results = False
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                with tie_col2:
                    st.markdown("<div class='tie-btn'>", unsafe_allow_html=True)
                    if st.button(f"🏅 {t_b} 晉級", key=f"tie_win_{t_a}_{t_b}_B"):
                        st.session_state.tie_resolutions[key] = t_b
                        st.session_state.show_results = False
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

        if len(st.session_state.tie_resolutions) == len(st.session_state.tie_matches):
            st.success("✅ 所有同分殊決已完成！可點擊「大螢幕揭曉晉級名單」。")
        else:
            remaining = len(st.session_state.tie_matches) - len(st.session_state.tie_resolutions)
            st.warning(f"⏳ 尚有 {remaining} 場殊決待裁判選擇，完成後才可揭曉。")

    # --- 揭曉晉級結果 ---
    if st.session_state.show_results and st.session_state.advancing:
        st.markdown("## 🎉 本輪晉級名單 🎉")
        for w in st.session_state.advancing:
            st.markdown(f"<span class='winner-text'>⭐ 恭喜 【{w}】 晉級下一輪！</span>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        is_final = (stage == 3)

        if is_final:
            if st.button("🏆 正式宣佈總冠軍！", type="primary"):
                champion_a = st.session_state.advancing[0]
                # ✅ 計算失誤最少獎，並存入 session_state
                fw, fs = compute_fewest_mistakes_award_modeA(champion_a)
                st.session_state.fewest_mistakes_winner = (fw, fs) if fw else None
                st.session_state.champion = champion_a
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
                st.session_state.tie_matches = []
                st.session_state.tie_resolutions = {}
                st.session_state.locked_winners = []
                for key in list(st.session_state.mistakes.keys()):
                    st.session_state.mistakes[key] = 0
                st.rerun()
