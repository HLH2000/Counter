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
    .stButton>button:hover { border-color: #4CAF50 !important; color: #4CAF50 !important; }
    input[type="number"] {
        font-size: 30px !important; text-align: center !important;
        height: 60px !important; background-color: #333333 !important; color: #FFFFFF !important;
    }
    .winner-text  { color: #FFD700 !important; font-size: 32px; font-weight: bold; }
    .silver-text  { color: #C0C0C0 !important; font-size: 28px; font-weight: bold; }
    .seed-text    { color: #00FFFF !important; font-size: 24px; font-weight: bold; }
    .vs-text      { text-align: center; font-size: 40px; font-weight: 900; color: #888888; padding-top: 20px; }
    .resolved-badge { color: #4CAF50 !important; font-size: 20px; font-weight: bold; padding: 8px 0; }

    .fewest-award-box {
        background: linear-gradient(135deg, #0d1a2d, #1a2d40);
        border: 3px solid #4FC3F7; border-radius: 16px; padding: 24px 32px; margin: 20px 0;
        box-shadow: 0 0 30px rgba(79,195,247,0.35);
    }
    .fewest-award-title  { color: #4FC3F7 !important; font-size: 24px !important; font-weight: 900 !important; letter-spacing: 2px; margin-bottom: 8px; }
    .fewest-award-winner { color: #E1F5FE !important; font-size: 26px !important; font-weight: bold; }

    .tie-box {
        background: linear-gradient(135deg, #1a0a00, #2d1500);
        border: 3px solid #FF6600; border-radius: 16px; padding: 28px 32px; margin: 16px 0;
        box-shadow: 0 0 30px rgba(255,102,0,0.4);
    }
    .tie-title { color: #FF6600 !important; font-size: 26px !important; font-weight: 900 !important; letter-spacing: 2px; }
    .tie-rule  { color: #FFB366 !important; font-size: 20px !important; background-color: rgba(255,102,0,0.12); border-left: 4px solid #FF6600; padding: 10px 16px; border-radius: 6px; margin: 12px 0 20px 0; }
    .tie-teams { color: #FFFFFF !important; font-size: 22px !important; margin-bottom: 6px; }
    .tie-score { color: #FF6600 !important; font-size: 28px !important; font-weight: bold; }
    .tie-btn > div > button { background-color: #3D1A00 !important; border: 2px solid #FF6600 !important; color: #FFB366 !important; font-size: 22px !important; }
    .tie-btn > div > button:hover { background-color: #FF6600 !important; color: #FFFFFF !important; border-color: #FFFFFF !important; }

    .janken-box {
        background: linear-gradient(135deg, #0a001a, #1a0033);
        border: 3px solid #AA44FF; border-radius: 16px; padding: 28px 32px; margin: 16px 0;
        box-shadow: 0 0 30px rgba(170,68,255,0.45);
    }
    .janken-title { color: #CC88FF !important; font-size: 26px !important; font-weight: 900 !important; letter-spacing: 2px; }
    .janken-sub   { color: #DDC0FF !important; font-size: 19px !important; margin: 10px 0 6px 0; }
    .janken-round { color: #FFFFFF !important; font-size: 22px !important; font-weight: bold; margin-bottom: 4px; }
    .janken-score { color: #AA44FF !important; font-size: 28px !important; font-weight: bold; }
    .janken-win   { color: #FF44AA !important; font-size: 22px !important; font-weight: bold; }
    .janken-btn > div > button { background-color: #25004a !important; border: 2px solid #AA44FF !important; color: #CC88FF !important; font-size: 20px !important; }
    .janken-btn > div > button:hover { background-color: #AA44FF !important; color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════
#  狀態初始化
# ═══════════════════════════════════════════
defaults = {
    'mode': "模式A: PK淘汰賽",
    'team_count': 5,
    'round_stage': 1,
    'mistakes': {},
    'round_history': {},       # {team: [r1,r2,r3...]}  各輪失誤
    'advancing': [],
    'show_results': False,
    'tournament_state': {},
    'champion': None,
    'fewest_mistakes_winner': None,
    'all_mistakes_log': {},    # {team: best_single_round}
    'timer_end': None,
    'timer_label': "",
    'timer_color': "#00FFFF",
    # 晉級同分（舊邏輯：歷史輪次 → 先落地）
    'tie_matches': [],         # [(t_a, t_b, score)]
    'tie_resolutions': {},     # {(t_a,t_b): winner}
    'locked_winners': [],      # [(match, winner)]
    # 猜拳 PK（只在「失誤最少特別獎」同分時啟動，冠軍公布後）
    'award_janken_matches': [],   # [(t_a, t_b)]  待猜拳的特別獎候選對
    'award_janken_state': {},     # {(t_a,t_b): {rounds,score_a,score_b}}
    'award_janken_winner': None,  # 猜拳決出的特別獎得主
    # 模式B 猜拳（主賽同分）
    'b_janken_pairs': [],
    'b_janken_state': {},
    'b_janken_resolutions': {},
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def reset_game():
    for k, v in defaults.items():
        st.session_state[k] = v
    st.session_state.mistakes = {f"第{i}組": 0 for i in range(1, 9)}


# ───────────────────────────────────────────
#  工具函式
# ───────────────────────────────────────────
def record_round_history(matchups):
    stage = st.session_state.round_stage
    for match in matchups:
        for team in match:
            score = st.session_state.mistakes.get(team, 0)
            hist = st.session_state.round_history.setdefault(team, [])
            while len(hist) < stage - 1:
                hist.append(None)
            if len(hist) < stage:
                hist.append(score)
            else:
                hist[stage - 1] = score


def update_best_log(matchups):
    log = st.session_state.all_mistakes_log
    for match in matchups:
        for team in match:
            score = st.session_state.mistakes.get(team, 0)
            log[team] = score if team not in log else min(log[team], score)
    st.session_state.all_mistakes_log = log


def resolve_tie_modeA(t_a, t_b):
    """
    比較兩隊歷史各輪失誤：
    - 找到第一個不同的輪次 → 失誤少的勝
    - 某輪只有一方有記錄 → 有記錄方勝（有比過的贏）
    - 所有輪次完全相同 → 回傳 'tie'（先落地裁決）
    """
    hist_a = st.session_state.round_history.get(t_a, [])
    hist_b = st.session_state.round_history.get(t_b, [])
    max_rounds = max(len(hist_a), len(hist_b), 1)
    for i in range(max_rounds):
        va = hist_a[i] if i < len(hist_a) else None
        vb = hist_b[i] if i < len(hist_b) else None
        if va is None and vb is None:
            continue
        if va is None:
            return t_b
        if vb is None:
            return t_a
        if va < vb:
            return t_a
        if vb < va:
            return t_b
    return 'tie'   # 完全相同 → 先落地裁決


def find_fewest_mistakes_candidates(champion):
    """
    模式A：排除冠軍後，找出最佳單場失誤最少的隊伍。
    若有複數隊伍並列最少（且與冠軍不同分），回傳清單供猜拳。
    回傳 (winner_or_None, score, [tied_teams])
    """
    log = st.session_state.all_mistakes_log
    champion_score = log.get(champion, 0)
    candidates = sorted(
        [(t, s) for t, s in log.items() if t != champion],
        key=lambda x: x[1]
    )
    if not candidates:
        return None, None, []
    best_score = candidates[0][1]
    # 找所有並列最少的（且分數不能等於冠軍最佳單場）
    tied = [t for t, s in candidates if s == best_score and s != champion_score]
    non_tied = [t for t, s in candidates if s == best_score]  # 含同冠軍分數者

    if not tied:
        # 全部都跟冠軍同分 → 順延至下一名
        for t, s in candidates:
            if s != champion_score:
                return t, s, []
        # 真的全同分，取第一個
        return candidates[0][0], candidates[0][1], []

    if len(tied) == 1:
        return tied[0], best_score, []
    else:
        return None, best_score, tied   # 需猜拳決定


def compute_fewest_mistakes_award_modeB(results):
    if len(results) >= 2:
        return results[1][0], results[1][1]
    return None, None


# ───────────────────────────────────────────
#  猜拳 PK 面板（通用）
#  state_dict: session_state 裡存放該場猜拳狀態的 dict key
#  resolution_key: session_state 裡存放結果的 key（字串）
#  pair: (t_a, t_b)
#  key_prefix: widget key 前綴
# ───────────────────────────────────────────
def render_janken_panel(pair, state_key, resolution_key, key_prefix="jk"):
    t_a, t_b = pair
    TOTAL = 5

    state_dict = st.session_state[state_key]
    if pair not in state_dict:
        state_dict[pair] = {'rounds': [], 'score_a': 0, 'score_b': 0}

    js = state_dict[pair]
    completed = len(js['rounds'])
    sa, sb = js['score_a'], js['score_b']
    remaining = TOTAL - completed
    already_won = st.session_state[resolution_key] is not None if isinstance(st.session_state[resolution_key], str) \
                  else pair in (st.session_state[resolution_key] or {})

    # 判斷提前決出 or 5局結束
    def check_decide():
        rem = TOTAL - len(js['rounds'])
        if js['score_a'] > js['score_b'] and js['score_b'] + rem < js['score_a']:
            return t_a
        if js['score_b'] > js['score_a'] and js['score_a'] + rem < js['score_b']:
            return t_b
        if len(js['rounds']) >= TOTAL:
            if js['score_a'] > js['score_b']: return t_a
            if js['score_b'] > js['score_a']: return t_b
        return None

    decided = check_decide()
    # 寫入結果（支援 dict 或直接字串型態）
    if decided and not already_won:
        if isinstance(st.session_state[resolution_key], dict):
            st.session_state[resolution_key][pair] = decided
        else:
            st.session_state[resolution_key] = decided
        st.rerun()

    # 取得目前結果
    if isinstance(st.session_state[resolution_key], dict):
        current_winner = st.session_state[resolution_key].get(pair)
    else:
        current_winner = st.session_state[resolution_key]

    st.markdown(f"""
    <div class='janken-box'>
        <div class='janken-title'>✊ 猜拳 PK 大戰（5人制）</div>
        <div class='janken-sub'>雙方各派 5 名成員（含對輔）依序猜拳，多數勝者晉級。</div>
        <div class='janken-round'>對戰：<strong>{t_a}</strong> vs <strong>{t_b}</strong></div>
        <div class='janken-score'>
            目前比分 ── {t_a}：{sa} 勝　{t_b}：{sb} 勝　（共 {completed} 局）
        </div>
    </div>
    """, unsafe_allow_html=True)

    if current_winner:
        st.markdown(f"<div class='resolved-badge'>✅ 猜拳結果：【{current_winner}】勝出！（{sa} : {sb}）</div>",
                    unsafe_allow_html=True)
        if st.button(f"↩️ 重置猜拳（{t_a} vs {t_b}）", key=f"{key_prefix}_reset_{t_a}_{t_b}"):
            state_dict.pop(pair, None)
            if isinstance(st.session_state[resolution_key], dict):
                st.session_state[resolution_key].pop(pair, None)
            else:
                st.session_state[resolution_key] = None
            st.rerun()
        return

    # 顯示歷史
    if js['rounds']:
        lines = []
        for idx, r in enumerate(js['rounds'], 1):
            ra = "✅勝" if r['a'] == 'W' else ("❌負" if r['a'] == 'L' else "🤝平")
            rb = "✅勝" if r['b'] == 'W' else ("❌負" if r['b'] == 'L' else "🤝平")
            lines.append(f"第{idx}局：{t_a} {ra}　{t_b} {rb}")
        st.markdown(
            "<br>".join([f"<span style='color:#CCCCCC;font-size:17px;'>{l}</span>" for l in lines]),
            unsafe_allow_html=True
        )

    round_no = completed + 1
    can_play = completed < TOTAL or (completed >= TOTAL and sa == sb)

    if can_play:
        if completed >= TOTAL and sa == sb:
            st.warning(f"⚡ {TOTAL} 局全平！進入加賽，繼續直到分出勝負。")
        st.markdown(f"<p class='janken-win'>👇 第 {round_no} 局結果（裁判請選）：</p>", unsafe_allow_html=True)
        jc1, jc2, jc3 = st.columns(3)
        with jc1:
            st.markdown("<div class='janken-btn'>", unsafe_allow_html=True)
            if st.button(f"🏅 {t_a} 勝", key=f"{key_prefix}_Awin_{t_a}_{t_b}_{round_no}"):
                js['rounds'].append({'a': 'W', 'b': 'L'})
                js['score_a'] += 1
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with jc2:
            st.markdown("<div class='janken-btn'>", unsafe_allow_html=True)
            if st.button(f"🤝 平局", key=f"{key_prefix}_draw_{t_a}_{t_b}_{round_no}"):
                js['rounds'].append({'a': 'D', 'b': 'D'})
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with jc3:
            st.markdown("<div class='janken-btn'>", unsafe_allow_html=True)
            if st.button(f"🏅 {t_b} 勝", key=f"{key_prefix}_Bwin_{t_a}_{t_b}_{round_no}"):
                js['rounds'].append({'a': 'L', 'b': 'W'})
                js['score_b'] += 1
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    if js['rounds']:
        if st.button(f"↩️ 撤回上一局（{t_a} vs {t_b}）", key=f"{key_prefix}_undo_{t_a}_{t_b}"):
            last = js['rounds'].pop()
            if last['a'] == 'W': js['score_a'] -= 1
            if last['b'] == 'W': js['score_b'] -= 1
            st.rerun()


# ═══════════════════════════════════════════
#  側邊欄
# ═══════════════════════════════════════════
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
                unsafe_allow_html=True)
            time.sleep(1)
            st.rerun()
        else:
            timer_placeholder.markdown(
                "<h2 style='text-align:center; color:#FF4444 !important;'>⏰ 時間到！</h2>",
                unsafe_allow_html=True)
            st.session_state.timer_end = None


# ═══════════════════════════════════════════
#  主畫面
# ═══════════════════════════════════════════
st.title("🏆 社區健康挑戰賽 - 賽況看板")


# ────────────────────────────────────────────
#  冠軍公布畫面（含失誤最少特別獎 & 猜拳決定）
# ────────────────────────────────────────────
if st.session_state.champion:
    st.balloons()
    st.markdown("<h1 style='text-align:center; color:#FFD700 !important;'>🏆 最終總冠軍誕生！ 🏆</h1>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center;'>恭喜：<span style='color:#FFD700;'>{st.session_state.champion}</span></h1>", unsafe_allow_html=True)

    st.markdown("<hr style='border:2px solid #444; margin:30px 0;'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;'>🎖️ 全場失誤最少特別獎</h2>", unsafe_allow_html=True)

    champion = st.session_state.champion
    winner_direct, best_score, tied_teams = find_fewest_mistakes_candidates(champion)

    if st.session_state.award_janken_winner:
        # 猜拳已決出
        fw = st.session_state.award_janken_winner
        fs = st.session_state.all_mistakes_log.get(fw, 0)
        st.markdown(f"""
        <div class='fewest-award-box'>
            <div class='fewest-award-title'>🎖️ 全場失誤最少特別獎（猜拳決出）</div>
            <div class='fewest-award-winner'>恭喜 【{fw}】<br>
            <span style='font-size:20px; color:#B3E5FC;'>最佳單場僅 {fs} 次失誤</span></div>
        </div>
        """, unsafe_allow_html=True)

    elif winner_direct:
        # 直接決出，不需猜拳
        st.markdown(f"""
        <div class='fewest-award-box'>
            <div class='fewest-award-title'>🎖️ 全場失誤最少特別獎</div>
            <div class='fewest-award-winner'>恭喜 【{winner_direct}】<br>
            <span style='font-size:20px; color:#B3E5FC;'>最佳單場僅 {best_score} 次失誤（排除總冠軍後最少）</span></div>
        </div>
        """, unsafe_allow_html=True)

    elif tied_teams:
        # 並列需猜拳
        st.warning(f"⚠️ 以下 {len(tied_teams)} 隊最佳單場均為 {best_score} 次失誤，需猜拳決定特別獎！")
        for i in range(len(tied_teams) - 1):
            pair = (tied_teams[i], tied_teams[i + 1])
            if pair not in st.session_state.award_janken_matches:
                st.session_state.award_janken_matches.append(pair)

        st.markdown("## ✊ 特別獎猜拳 PK")
        for pair in st.session_state.award_janken_matches:
            render_janken_panel(
                pair,
                state_key='award_janken_state',
                resolution_key='award_janken_winner',
                key_prefix="award_jk"
            )
    else:
        st.info("無法決定特別獎（所有隊伍均與冠軍同分）。")

    st.stop()


# ═══════════════════════════════════════════
#  模式 B：純計時賽
# ═══════════════════════════════════════════
if st.session_state.mode == "模式B: 純計時賽":
    st.markdown("### 模式 B：純計時賽 (獨立進行，不捉對廝殺)")
    st.info("計分標準：2 分鐘內失誤數最少的組別獲勝。失誤包含：過低、偏離Range、停滯。")

    cols = st.columns(6)
    for i in range(1, 7):
        team_name = f"第{i}組"
        st.session_state.mistakes.setdefault(team_name, 0)
        with cols[i - 1]:
            label = f"<h3>{team_name}<br><span class='seed-text'>(友善組)</span></h3>" if i in [5, 6] \
                    else f"<h3>{team_name}</h3>"
            st.markdown(label, unsafe_allow_html=True)
            st.session_state.mistakes[team_name] = st.number_input(
                "失誤數", min_value=0, value=st.session_state.mistakes[team_name], key=f"modeB_{team_name}"
            )

    st.markdown("---")
    if st.button("🏁 結算純計時賽總成績"):
        results = sorted(
            [(f"第{i}組", st.session_state.mistakes[f"第{i}組"]) for i in range(1, 7)],
            key=lambda x: x[1]
        )
        champion_b = results[0][0]
        fw, fs = compute_fewest_mistakes_award_modeB(results)

        st.markdown("## 🏆 賽事結果")
        st.markdown(f"<span class='winner-text'>🥇 最終總冠軍：{champion_b} (失誤 {results[0][1]} 次)</span>", unsafe_allow_html=True)
        if fw:
            st.markdown(f"""
            <div class='fewest-award-box'>
                <div class='fewest-award-title'>🎖️ 全場失誤最少特別獎</div>
                <div class='fewest-award-winner'>恭喜 【{fw}】<br>
                <span style='font-size:20px; color:#B3E5FC;'>失誤 {fs} 次（全場第二少，排除總冠軍）</span></div>
            </div>
            """, unsafe_allow_html=True)

    # ── 模式B 同分猜拳區 ──
    st.markdown("---")
    st.markdown("### ⚡ 同分猜拳 PK")
    st.caption("若有隊伍失誤相同，請加入對組進行猜拳決勝。")

    teams_b = [f"第{i}組" for i in range(1, 7)]
    bcol1, bcol2, bcol3 = st.columns([2, 2, 1])
    with bcol1:
        b_team_a = st.selectbox("隊伍 A", teams_b, key="b_janken_a")
    with bcol2:
        b_team_b = st.selectbox("隊伍 B", [t for t in teams_b if t != b_team_a], key="b_janken_b")
    with bcol3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("＋ 加入猜拳", key="b_add_janken"):
            pair = (b_team_a, b_team_b)
            rev = (b_team_b, b_team_a)
            if pair not in st.session_state.b_janken_pairs and rev not in st.session_state.b_janken_pairs:
                st.session_state.b_janken_pairs.append(pair)
                st.rerun()

    for pair in st.session_state.b_janken_pairs:
        render_janken_panel(pair, 'b_janken_state', 'b_janken_resolutions', key_prefix="b_jk")

    if st.session_state.b_janken_pairs:
        if st.button("🗑️ 清除所有猜拳對組"):
            st.session_state.b_janken_pairs = []
            st.session_state.b_janken_state = {}
            st.session_state.b_janken_resolutions = {}
            st.rerun()


# ═══════════════════════════════════════════
#  模式 A：PK 淘汰賽
# ═══════════════════════════════════════════
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
                        (st.session_state.tournament_state.get('w_5_6', '5/6勝方'), "第7組(種子隊伍)")]
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

    # ── 對戰輸入 UI ──
    if matchups:
        st.markdown(f"## 📍 當前賽程：第 {stage} 輪")
        st.markdown("<br>", unsafe_allow_html=True)
        for match in matchups:
            col1, col2, col3 = st.columns([3, 1, 3])
            team_a, team_b = match
            with col1:
                st.markdown(f"<h3>{team_a}</h3>", unsafe_allow_html=True)
                st.session_state.mistakes.setdefault(team_a, 0)
                st.session_state.mistakes[team_a] = st.number_input(
                    "失誤數", min_value=0, value=st.session_state.mistakes[team_a], key=f"modeA_{team_a}_{stage}")
            with col2:
                st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<h3>{team_b}</h3>", unsafe_allow_html=True)
                st.session_state.mistakes.setdefault(team_b, 0)
                st.session_state.mistakes[team_b] = st.number_input(
                    "失誤數", min_value=0, value=st.session_state.mistakes[team_b], key=f"modeA_{team_b}_{stage}")
            st.markdown("<hr style='border:1px solid #444;'>", unsafe_allow_html=True)

    # ── 結算按鈕 ──
    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button("🔒 結算本輪成績 (鎖定分數)"):
            record_round_history(matchups)
            update_best_log(matchups)

            clear_winners = []
            tie_list = []

            for match in matchups:
                t_a, t_b = match
                score_a = st.session_state.mistakes.get(t_a, 0)
                score_b = st.session_state.mistakes.get(t_b, 0)
                if score_a != score_b:
                    winner = t_a if score_a < score_b else t_b
                    clear_winners.append((match, winner))
                else:
                    result = resolve_tie_modeA(t_a, t_b)
                    if result != 'tie':
                        clear_winners.append((match, result))
                        st.info(f"⚖️ {t_a} vs {t_b} 本輪同分，依歷史輪次判定：【{result}】晉級。")
                    else:
                        tie_list.append((t_a, t_b, score_a))

            st.session_state.locked_winners = clear_winners
            st.session_state.tie_matches = tie_list
            st.session_state.tie_resolutions = {}
            st.session_state.show_results = False

            if tie_list:
                st.warning(f"⚠️ {len(tie_list)} 場歷史完全相同！請在下方由裁判選出先落地判負方。")
            else:
                st.success("✅ 成績已鎖定！請揭曉晉級名單。")

    with col_btn2:
        ties_all_done = len(st.session_state.tie_resolutions) == len(st.session_state.tie_matches)
        has_locked = bool(st.session_state.locked_winners) or bool(st.session_state.tie_matches)

        if st.button("📢 大螢幕揭曉晉級名單",
                     disabled=(not has_locked or not ties_all_done)):
            final_winners = [w for (_, w) in st.session_state.locked_winners]
            for (t_a, t_b, _) in st.session_state.tie_matches:
                key = (t_a, t_b)
                if key in st.session_state.tie_resolutions:
                    final_winners.append(st.session_state.tie_resolutions[key])
            st.session_state.advancing = final_winners
            st.session_state.show_results = True

    # ── 先落地裁決窗格（歷史完全相同時）──
    if st.session_state.tie_matches:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("## ⚡ 先落地裁決")
        for (t_a, t_b, tied_score) in st.session_state.tie_matches:
            key = (t_a, t_b)
            resolved = key in st.session_state.tie_resolutions
            st.markdown(f"""
            <div class='tie-box'>
                <div class='tie-title'>🔥 歷史成績完全相同</div>
                <div class='tie-rule'>📋 裁決規則：氣球/道具最先落地的隊伍判負</div>
                <div class='tie-teams'>對戰雙方：<strong>{t_a}</strong> vs <strong>{t_b}</strong></div>
                <div class='tie-score'>各輪失誤完全相同</div>
            </div>
            """, unsafe_allow_html=True)
            if resolved:
                winner = st.session_state.tie_resolutions[key]
                st.markdown(f"<div class='resolved-badge'>✅ 已選定晉級方：【{winner}】</div>", unsafe_allow_html=True)
                if st.button(f"↩️ 重新選擇（{t_a} vs {t_b}）", key=f"redo_{t_a}_{t_b}"):
                    del st.session_state.tie_resolutions[key]
                    st.session_state.show_results = False
                    st.rerun()
            else:
                st.markdown("<p style='color:#FFB366;font-size:20px;'>👇 裁判請點選落地失敗方（判負）的對手晉級：</p>", unsafe_allow_html=True)
                tc1, tc2 = st.columns(2)
                with tc1:
                    st.markdown("<div class='tie-btn'>", unsafe_allow_html=True)
                    if st.button(f"🏅 {t_a} 晉級", key=f"tie_A_{t_a}_{t_b}"):
                        st.session_state.tie_resolutions[key] = t_a
                        st.session_state.show_results = False
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                with tc2:
                    st.markdown("<div class='tie-btn'>", unsafe_allow_html=True)
                    if st.button(f"🏅 {t_b} 晉級", key=f"tie_B_{t_a}_{t_b}"):
                        st.session_state.tie_resolutions[key] = t_b
                        st.session_state.show_results = False
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

        if ties_all_done := (len(st.session_state.tie_resolutions) == len(st.session_state.tie_matches)):
            st.success("✅ 所有裁決完成！可點擊「大螢幕揭曉晉級名單」。")
        else:
            st.warning(f"⏳ 尚有 {len(st.session_state.tie_matches) - len(st.session_state.tie_resolutions)} 場待裁決。")

    # ── 揭曉晉級結果 ──
    if st.session_state.show_results and st.session_state.advancing:
        st.markdown("## 🎉 本輪晉級名單 🎉")
        for w in st.session_state.advancing:
            st.markdown(f"<span class='winner-text'>⭐ 恭喜 【{w}】 晉級下一輪！</span>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        is_final = (stage == 3)

        if is_final:
            if st.button("🏆 正式宣佈總冠軍！", type="primary"):
                st.session_state.champion = st.session_state.advancing[0]
                # 重置特別獎猜拳狀態
                st.session_state.award_janken_matches = []
                st.session_state.award_janken_state = {}
                st.session_state.award_janken_winner = None
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
                for k in list(st.session_state.mistakes.keys()):
                    st.session_state.mistakes[k] = 0
                st.rerun()
