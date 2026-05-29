import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date, timedelta
import random
from collections import Counter
import time

st.set_page_config(page_title="글로벌 AI 스포츠 분석실", layout="wide")

# ==========================================
# 🇺🇸 MLB 전용 설정 및 함수 (V16.0 유지)
# ==========================================
MLB_PARK_FACTORS = {
    'Colorado Rockies': 1.12, 'Cincinnati Reds': 1.08, 'Boston Red Sox': 1.07, 'Texas Rangers': 1.05,
    'Chicago White Sox': 1.04, 'Atlanta Braves': 1.03, 'Los Angeles Dodgers': 1.03, 'Philadelphia Phillies': 1.02,
    'Houston Astros': 1.01, 'Baltimore Orioles': 1.00, 'Toronto Blue Jays': 1.00, 'Minnesota Twins': 1.00,
    'Chicago Cubs': 1.00, 'New York Yankees': 1.00, 'Kansas City Royals': 0.99, 'Arizona Diamondbacks': 0.99,
    'Milwaukee Brewers': 0.98, 'Los Angeles Angels': 0.98, 'Washington Nationals': 0.98, 'San Francisco Giants': 0.97,
    'Miami Marlins': 0.97, 'Pittsburgh Pirates': 0.96, 'Cleveland Guardians': 0.96, 'St. Louis Cardinals': 0.96,
    'Detroit Tigers': 0.95, 'Tampa Bay Rays': 0.95, 'New York Mets': 0.95, 'Athletics': 0.94,
    'San Diego Padres': 0.94, 'Seattle Mariners': 0.93
}

POSITION_TRANSLATIONS = {
    'P': '투수', 'C': '포수', '1B': '1루수', '2B': '2루수', '3B': '3루수',
    'SS': '유격수', 'LF': '좌익수', 'CF': '중견수', 'RF': '우익수', 'DH': '지명타자',
    'TWP': '투타겸업', 'O': '외야수', 'IF': '내야수', 'B': '야수', 'PH': '대타', 'PR': '대주자'
}

@st.cache_data(ttl=3600)
def load_mlb_all_data():
    hitter_url = "https://statsapi.mlb.com/api/v1/stats?stats=season&group=hitting&gameType=R&season=2026&playerPool=ALL&limit=1500"
    h_splits = requests.get(hitter_url).json()['stats'][0]['splits']
    hitter_list = [{
        '이름': r['player']['fullName'], '팀': r['team']['name'], 
        '타수': r['stat'].get('atBats', 0), '안타': r['stat'].get('hits', 0),
        '2루타': r['stat'].get('doubles', 0), '3루타': r['stat'].get('triples', 0),
        '홈런': r['stat'].get('homeRuns', 0), '타점': r['stat'].get('rbi', 0),
        '득점': r['stat'].get('runs', 0), '볼넷': r['stat'].get('baseOnBalls', 0),
        '삼진': r['stat'].get('strikeOuts', 0), '도루': r['stat'].get('stolenBases', 0),
        '타율': r['stat'].get('avg', '.000'), '출루율': r['stat'].get('obp', '.000'),
        '장타율': r['stat'].get('slg', '.000'), 'OPS': r['stat'].get('ops', '.000')
    } for r in h_splits]
    df_h = pd.DataFrame(hitter_list)
    df_h['OPS'] = pd.to_numeric(df_h['OPS'], errors='coerce').fillna(0.0)
    df_h['타수'] = pd.to_numeric(df_h['타수'], errors='coerce').fillna(0)
    
    pitcher_url = "https://statsapi.mlb.com/api/v1/stats?stats=season&group=pitching&gameType=R&season=2026&playerPool=ALL&limit=1500"
    p_splits = requests.get(pitcher_url).json()['stats'][0]['splits']
    pitcher_list = [{
        '이름': r['player']['fullName'], '팀': r['team']['name'], 
        '승': r['stat'].get('wins', 0), '패': r['stat'].get('losses', 0),
        '세이브': r['stat'].get('saves', 0), '출장': r['stat'].get('gamesPlayed', 0), 
        '선발': r['stat'].get('gamesStarted', 0), '이닝': r['stat'].get('inningsPitched', '0.0'),
        '피안타율': r['stat'].get('avg', '.000'), 'WHIP': r['stat'].get('whip', '0.00'),
        '탈삼진': r['stat'].get('strikeOuts', 0), '볼넷': r['stat'].get('baseOnBalls', 0),
        '피홈런': r['stat'].get('homeRuns', 0), 'ERA': r['stat'].get('era', '99.99')
    } for r in p_splits]
    df_p = pd.DataFrame(pitcher_list)
    df_p['ERA_num'] = pd.to_numeric(df_p['ERA'], errors='coerce').fillna(4.50)
    df_p['이닝_num'] = pd.to_numeric(df_p['이닝'], errors='coerce').fillna(0.0)
    
    df_p['평균이닝'] = df_p.apply(lambda x: x['이닝_num'] / x['선발'] if x['선발'] > 0 else 4.0, axis=1).clip(3.0, 7.5)
    df_p['FIP'] = df_p.apply(lambda x: ((13*x['피홈런'] + 3*x['볼넷'] - 2*x['탈삼진']) / x['이닝_num']) + 3.10 if x['이닝_num'] > 0 else 4.50, axis=1)
    
    df_bullpen = df_p[(df_p['출장'] > df_p['선발']) & (df_p['이닝_num'] >= 5.0)]
    team_bullpen_fip = df_bullpen.groupby('팀')['FIP'].mean().to_dict()
    return df_h, df_p, team_bullpen_fip

@st.cache_data(ttl=3600)
def load_mlb_team_momentum():
    url = "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104"
    res = requests.get(url).json()
    l10_dict = {}
    for record in res['records']:
        for team in record['teamRecords']:
            name = team['team']['name']
            splits = team.get('records', {}).get('splitRecords', [])
            l10_win_rate = 0.5
            l10_str = "5-5"
            for split in splits:
                if split['type'] == 'lastTen':
                    l10_str = f"{split['wins']} W - {split['losses']} L"
                    if (split['wins'] + split['losses']) > 0:
                        l10_win_rate = split['wins'] / (split['wins'] + split['losses'])
                    break
            l10_dict[name] = {'rate': l10_win_rate, 'str': l10_str}
    return l10_dict

def calculate_mlb_ai_odds(h_team, a_team, h_p, a_p, df_h, df_p, team_bp_fip):
    h_ops = df_h[(df_h['팀'] == h_team) & (df_h['타수'] > 50)]['OPS'].mean() or 0.720
    a_ops = df_h[(df_h['팀'] == a_team) & (df_h['타수'] > 50)]['OPS'].mean() or 0.720
    h_p_data = df_p[df_p['이름'] == h_p]
    a_p_data = df_p[df_p['이름'] == a_p]
    h_s_fip = h_p_data['FIP'].values[0] if not h_p_data.empty else 4.50
    a_s_fip = a_p_data['FIP'].values[0] if not a_p_data.empty else 4.50
    h_bp_fip = team_bp_fip.get(h_team, 4.00)
    a_bp_fip = team_bp_fip.get(a_team, 4.00)
    h_eff_fip = (h_s_fip * 0.6) + (h_bp_fip * 0.4)
    a_eff_fip = (a_s_fip * 0.6) + (a_bp_fip * 0.4)
    h_attack = h_ops / 0.720
    a_attack = a_ops / 0.720
    pf = MLB_PARK_FACTORS.get(h_team, 1.00)
    h_exp_runs = ((a_eff_fip * h_attack) + 0.2) * pf
    a_exp_runs = (h_eff_fip * a_attack) * pf
    win_prob = (h_exp_runs ** 1.83) / ((h_exp_runs ** 1.83) + (a_exp_runs ** 1.83))
    h_odds = max(1.10, min(round(0.94 / win_prob, 2), 6.00))
    a_odds = max(1.10, min(round(0.94 / (1 - win_prob), 2), 6.00))
    return f"{h_odds:.2f}", f"{a_odds:.2f}"

@st.cache_data(ttl=300)
def load_mlb_schedule(target_date):
    date_str = target_date.strftime("%Y-%m-%d")
    schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}&hydrate=probablePitcher"
    res = requests.get(schedule_url).json()
    games = []
    df_h, df_p, team_bp_fip = load_mlb_all_data()
    if 'dates' in res and len(res['dates']) > 0:
        for game in res['dates'][0]['games']:
            away_team = game['teams']['away']['team']['name']
            home_team = game['teams']['home']['team']['name']
            away_id = game['teams']['away']['team']['id']
            home_id = game['teams']['home']['team']['id']
            away_pitcher = game['teams']['away'].get('probablePitcher', {}).get('fullName', 'TBD')
            home_pitcher = game['teams']['home'].get('probablePitcher', {}).get('fullName', 'TBD')
            game_time_utc = game.get('gameDate')
            if game_time_utc:
                utc_time = datetime.strptime(game_time_utc, "%Y-%m-%dT%H:%M:%SZ")
                kst_time = utc_time + timedelta(hours=9)
                time_str = kst_time.strftime("%H:%M")
            else: time_str = "TBD"
            status = game['status']['abstractGameState']
            h_score = game['teams']['home'].get('score', 0)
            a_score = game['teams']['away'].get('score', 0)
            if status == 'Final': status_str = f"✅ 종료 ({h_score}:{a_score})"
            elif status == 'Live': status_str = f"🔥 진행중 ({h_score}:{a_score})"
            else: status_str = "⏳ 예정"
            h_odds, a_odds = calculate_mlb_ai_odds(home_team, away_team, home_pitcher, away_pitcher, df_h, df_p, team_bp_fip)
            home_display = f"<img src='https://www.mlbstatic.com/team-logos/{home_id}.svg' width='22' style='vertical-align:middle; margin-right:8px;'> <b>{home_team}</b> <span style='color:#ffcc00; font-size:13px; margin-left:10px;'>[{h_odds}]</span>"
            away_display = f"<img src='https://www.mlbstatic.com/team-logos/{away_id}.svg' width='22' style='vertical-align:middle; margin-right:8px;'> <b>{away_team}</b> <span style='color:#ffcc00; font-size:13px; margin-left:10px;'>[{a_odds}]</span>"
            games.append({
                '경기시간(KST)': time_str, '상태': status_str,
                '홈 팀': home_team, '홈 ID': home_id, '홈 선발투수': home_pitcher, '홈표시': home_display,
                '어웨이 팀 (원정)': away_team, '원정 ID': away_id, '어웨이 선발투수': away_pitcher, '원정표시': away_display,
                'gamePk': game.get('gamePk')
            })
    df = pd.DataFrame(games)
    if not df.empty: df = df.sort_values('경기시간(KST)').reset_index(drop=True)
    return df

@st.cache_data(ttl=60)
def load_mlb_live_lineup(game_pk):
    try:
        url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
        res = requests.get(url).json()
        home_order = res['teams']['home'].get('battingOrder', [])
        away_order = res['teams']['away'].get('battingOrder', [])
        h_pitchers = res['teams']['home'].get('pitchers', [])
        a_pitchers = res['teams']['away'].get('pitchers', [])
        h_starter_hand = res['teams']['home']['players'].get(f"ID_{h_pitchers[0]}", {}).get('person', {}).get('pitchHand', {}).get('code', 'R') if h_pitchers else 'R'
        a_starter_hand = res['teams']['away']['players'].get(f"ID_{a_pitchers[0]}", {}).get('person', {}).get('pitchHand', {}).get('code', 'R') if a_pitchers else 'R'
        if len(home_order) == 0 or len(away_order) == 0: return None, None, h_starter_hand, a_starter_hand
        h_players = res['teams']['home']['players']
        a_players = res['teams']['away']['players']
        h_lookup, a_lookup = {}, {}
        for k, p in h_players.items():
            if 'person' in p and 'id' in p['person']:
                pos_code = p.get('position', {}).get('abbreviation', 'B')
                bat_side = p.get('person', {}).get('batSide', {}).get('code', 'R')
                h_lookup[p['person']['id']] = {'name': p['person']['fullName'], 'pos': POSITION_TRANSLATIONS.get(pos_code, pos_code), 'batSide': bat_side}
        for k, p in a_players.items():
            if 'person' in p and 'id' in p['person']:
                pos_code = p.get('position', {}).get('abbreviation', 'B')
                bat_side = p.get('person', {}).get('batSide', {}).get('code', 'R')
                a_lookup[p['person']['id']] = {'name': p['person']['fullName'], 'pos': POSITION_TRANSLATIONS.get(pos_code, pos_code), 'batSide': bat_side}
        home_lineup = [h_lookup.get(pid, {'name': 'Unknown', 'pos': '야수', 'batSide': 'R'}) for pid in home_order]
        away_lineup = [a_lookup.get(pid, {'name': 'Unknown', 'pos': '야수', 'batSide': 'R'}) for pid in away_order]
        return home_lineup, away_lineup, h_starter_hand, a_starter_hand
    except:
        return None, None, 'R', 'R'

def calculate_platoon_ops(lineup, df_hitters, opp_pitcher_hand):
    total_ops = 0
    valid_batters = 0
    for p in lineup:
        batter_data = df_hitters[df_hitters['이름'] == p['name']]
        base_ops = batter_data['OPS'].values[0] if not batter_data.empty else 0.720
        bat_side = p['batSide']
        if opp_pitcher_hand == 'L':
            if bat_side == 'L': base_ops *= 0.90
            elif bat_side == 'R': base_ops *= 1.05
        elif opp_pitcher_hand == 'R':
            if bat_side == 'R': base_ops *= 0.95
            elif bat_side == 'L': base_ops *= 1.03
        total_ops += base_ops
        valid_batters += 1
    return total_ops / valid_batters if valid_batters > 0 else 0.720

def run_mlb_simulation(h_fip, a_fip, h_avg_ip, a_avg_ip, h_ops, a_ops, h_bp_fip, a_bp_fip, h_l10_rate, a_l10_rate, park_factor, num_sims=10000):
    h_starter_weight = h_avg_ip / 9.0
    a_starter_weight = a_avg_ip / 9.0
    h_eff_fip = (h_fip * h_starter_weight) + (h_bp_fip * (1 - h_starter_weight))
    a_eff_fip = (a_fip * a_starter_weight) + (a_bp_fip * (1 - a_starter_weight))
    h_momentum = 1.0 + (h_l10_rate - 0.5) * 0.1
    a_momentum = 1.0 + (a_l10_rate - 0.5) * 0.1
    h_attack = (h_ops / 0.720) * h_momentum if h_ops > 0 else 1.0 * h_momentum
    a_attack = (a_ops / 0.720) * a_momentum if a_ops > 0 else 1.0 * a_momentum
    h_expected_runs = ((a_eff_fip * h_attack) + 0.2) * park_factor
    a_expected_runs = (h_eff_fip * a_attack) * park_factor
    h_wins, a_wins = 0, 0
    scores = []
    for _ in range(num_sims):
        h_score = max(0, int(random.gauss(h_expected_runs, 2.5)))
        a_score = max(0, int(random.gauss(a_expected_runs, 2.5)))
        if h_score == a_score:
            if random.random() > 0.5: h_score += 1
            else: a_score += 1
        if h_score > a_score: h_wins += 1
        elif a_score > h_score: a_wins += 1
        scores.append(f"{h_score} : {a_score}")
    top3_scores = Counter(scores).most_common(3)
    formatted_top3 = [f"{score} ({(count / num_sims) * 100:.1f}%)" for score, count in top3_scores]
    return (h_wins / num_sims) * 100, (a_wins / num_sims) * 100, formatted_top3, h_eff_fip, a_eff_fip, park_factor

def generate_ai_commentary(h_team, a_team, h_eff_fip, a_eff_fip, h_ops, a_ops, h_l10_rate, a_l10_rate, h_win_prob):
    comments = []
    if h_eff_fip < 3.5 and a_eff_fip < 3.5: comments.append("🔥 **[마운드] 팽팽한 투수전 양상:** 양 팀 투수진의 실점 억제력이 최상급입니다. 끈적한 승부가 예상됩니다.")
    elif h_eff_fip > 4.7 and a_eff_fip > 4.7: comments.append("🔥 **[마운드] 다득점 난타전 경고:** 양 팀 마운드가 모두 불안정하여 다득점 타격전이 전개될 가능성이 농후합니다.")
    else:
        if a_eff_fip - h_eff_fip > 0.5: comments.append(f"⚾ **[마운드] {h_team} 우위:** 홈팀 투수진이 객관적인 구위(FIP)에서 확고한 우위를 점하고 있습니다.")
        elif a_eff_fip - h_eff_fip < -0.5: comments.append(f"⚾ **[마운드] {a_team} 우위:** 원정팀 마운드의 안정감이 더 돋보입니다. 홈팀 타선이 고전할 확률이 높습니다.")
        else: comments.append("⚾ **[마운드] 백중세:** 투수진의 진짜 실력(FIP)이 비슷합니다. 불펜 운영 타이밍이 핵심 변수입니다.")
    ops_diff = h_ops - a_ops
    if ops_diff > 0.050: comments.append(f"🏏 **[타선] {h_team} 우세:** 플래툰 상성까지 고려했을 때, 홈팀 타선의 파괴력이 더 매섭습니다.")
    elif ops_diff < -0.050: comments.append(f"🏏 **[타선] {a_team} 우세:** 원정팀 타선이 상대 투수와의 상성에서 유리한 고지를 점하고 있습니다.")
    else: comments.append("🏏 **[타선] 화력 팽팽:** 양 팀 화력 기대치가 대등합니다. 클러치 상황의 집중력이 승부를 가를 것입니다.")
    if h_win_prob >= 62.0: comments.append(f"💡 **[종합 요약]** 투타 전반에서 **{h_team}**의 우세가 뚜렷합니다. 이변이 없는 한 승리 가능성이 높습니다.")
    elif h_win_prob <= 38.0: comments.append(f"💡 **[종합 요약]** 원정팀 **{a_team}**의 전력이 압도합니다. 원정팀 역배당(또는 정배) 가치가 높습니다.")
    else: comments.append(f"💡 **[종합 요약]** 전력이 팽팽한 **박빙 매치(Toss-up)**입니다. 선발 이닝 소화력과 벤치 개입이 승패를 가릅니다.")
    return comments

# ==========================================
# 🇰🇷 KBO 전용 설정 및 함수
# ==========================================
KBO_PARK_FACTORS = {
    '삼성 라이온즈': 1.06, 'SSG 랜더스': 1.05, '롯데 자이언츠': 1.02, 'NC 다이노스': 1.01,
    'KT 위즈': 1.00, '한화 이글스': 1.00, 'KIA 타이거즈': 0.99, '키움 히어로즈': 0.97,
    'LG 트윈스': 0.95, '두산 베어스': 0.95
}
KBO_TEAMS = list(KBO_PARK_FACTORS.keys())

def run_kbo_simulation(h_fip, a_fip, h_avg_ip, a_avg_ip, h_ops, a_ops, h_bp_fip, a_bp_fip, park_factor, num_sims=10000):
    h_starter_weight = h_avg_ip / 9.0
    a_starter_weight = a_avg_ip / 9.0
    h_eff_fip = (h_fip * h_starter_weight) + (h_bp_fip * (1 - h_starter_weight))
    a_eff_fip = (a_fip * a_starter_weight) + (a_bp_fip * (1 - a_starter_weight))
    h_attack = (h_ops / 0.740) 
    a_attack = (a_ops / 0.740) 
    h_expected_runs = ((a_eff_fip * h_attack) + 0.2) * park_factor
    a_expected_runs = (h_eff_fip * a_attack) * park_factor
    h_wins, a_wins = 0, 0
    scores = []
    for _ in range(num_sims):
        h_score = max(0, int(random.gauss(h_expected_runs, 2.5)))
        a_score = max(0, int(random.gauss(a_expected_runs, 2.5)))
        if h_score == a_score:
            if random.random() > 0.5: h_score += 1
            else: a_score += 1
        if h_score > a_score: h_wins += 1
        elif a_score > h_score: a_wins += 1
        scores.append(f"{h_score} : {a_score}")
    top3_scores = Counter(scores).most_common(3)
    return (h_wins / num_sims) * 100, (a_wins / num_sims) * 100, top3_scores

# ==========================================
# 📺 메인 UI
# ==========================================
st.sidebar.title("⚾ 통합 AI 스포츠 분석실")
league_choice = st.sidebar.radio("분석할 리그:", ["🇺🇸 메이저리그 (MLB)", "🇰🇷 한국프로야구 (KBO)"])

if league_choice == "🇺🇸 메이저리그 (MLB)":
    st.header("🇺🇸 MLB AI 감독 모드")
    try:
        df_hitter, df_pitcher, team_bp_fip_dict = load_mlb_all_data()
        momentum_dict = load_mlb_team_momentum()
        selected_date = st.date_input("🗓️ 날짜 선택:", date.today())
        df_schedule = load_mlb_schedule(selected_date)
        if not df_schedule.empty:
            game_options = df_schedule['홈 팀'] + " vs " + df_schedule['어웨이 팀 (원정)']
            selected_game = st.selectbox("🔮 경기 선택:", game_options, key="mlb_g")
            row = df_schedule[game_options == selected_game].iloc[0]
            if st.button("🚀 MLB 시뮬레이션 시작"):
                h_team, a_team, h_p, a_p = row['홈 팀'], row['어웨이 팀 (원정)'], row['홈 선발투수'], row['어웨이 선발투수']
                h_ops = df_hitter[(df_hitter['팀'] == h_team) & (df_hitter['타수'] > 100)]['OPS'].mean() or 0.720
                a_ops = df_hitter[(df_hitter['팀'] == a_team) & (df_hitter['타수'] > 100)]['OPS'].mean() or 0.720
                h_p_data = df_pitcher[df_pitcher['이름'] == h_p]
                a_p_data = df_pitcher[df_pitcher['이름'] == a_p]
                h_win, a_win, top3, h_eff, a_eff, _ = run_mlb_simulation(h_p_data['FIP'].values[0] if not h_p_data.empty else 4.5, a_p_data['FIP'].values[0] if not a_p_data.empty else 4.5, 5.0, 5.0, h_ops, a_ops, team_bp_fip_dict.get(h_team, 4.0), team_bp_fip_dict.get(a_team, 4.0), 0.5, 0.5, MLB_PARK_FACTORS.get(h_team, 1.0))
                st.success(f"{h_team} 승률: {h_win:.1f}% | {a_team} 승률: {a_win:.1f}%")
                st.warning(f"🎯 TOP 3 스코어: {top3}")
    except Exception as e: st.error(f"MLB 오류: {e}")

elif league_choice == "🇰🇷 한국프로야구 (KBO)":
    st.header("🇰🇷 KBO AI 감독 모드 (구글 시트 연동)")
    st.info("시트 주소: '웹에 게시'된 CSV 주소를 입력하세요.")
    url = st.text_input("🔗 구글 시트 게시 URL (CSV):")
    if url:
        try:
            df = pd.read_csv(url)
            st.write("데이터 로드 성공!", df.head())
            st.warning("데이터가 로드되었습니다. 이제 데이터 연동 로직을 마무리합니다.")
        except: st.error("주소를 확인해주세요.")
