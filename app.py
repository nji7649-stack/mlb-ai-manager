import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date, timedelta
import random
from collections import Counter
import time

# 앱 전체 기본 설정 (반드시 맨 위에 있어야 함)
st.set_page_config(page_title="글로벌 AI 스포츠 분석실", layout="wide")

# ==========================================
# 🇺🇸 MLB 전용 설정 및 함수 (V16.0 기반)
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
# 🇰🇷 KBO 전용 설정 및 함수 (V1.0 기반)
# ==========================================
KBO_PARK_FACTORS = {
    '삼성 라이온즈': 1.06, 'SSG 랜더스': 1.05, '롯데 자이언츠': 1.02, 'NC 다이노스': 1.01,
    'KT 위즈': 1.00, '한화 이글스': 1.00, 'KIA 타이거즈': 0.99, '키움 히어로즈': 0.97,
    'LG 트윈스': 0.95, '두산 베어스': 0.95
}
KBO_TEAMS = list(KBO_PARK_FACTORS.keys())

@st.cache_data
def load_dummy_kbo_data():
    pitchers, hitters = [], []
    for team in KBO_TEAMS:
        pitchers.append({'이름': f'{team} 1선발', '팀': team, 'ERA': round(random.uniform(2.5, 4.5), 2), 'FIP': round(random.uniform(2.8, 4.8), 2), '평균이닝': random.uniform(5.0, 6.5)})
        pitchers.append({'이름': f'{team} 2선발', '팀': team, 'ERA': round(random.uniform(3.5, 5.0), 2), 'FIP': round(random.uniform(3.8, 5.2), 2), '평균이닝': random.uniform(4.5, 6.0)})
        for i in range(1, 10):
            hitters.append({'이름': f'{team} {i}번타자', '팀': team, 'OPS': round(random.uniform(0.650, 0.950), 3), 'batSide': random.choice(['L', 'R'])})
    df_p = pd.DataFrame(pitchers)
    df_h = pd.DataFrame(hitters)
    team_bp_fip = {team: round(random.uniform(3.5, 5.5), 2) for team in KBO_TEAMS}
    return df_h, df_p, team_bp_fip

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
# 📺 메인 UI - 사이드바(좌측 메뉴) 구성
# ==========================================
st.sidebar.title("⚾ 통합 AI 스포츠 분석실")
st.sidebar.markdown("클릭 한 번으로 리그를 전환하세요.")

league_choice = st.sidebar.radio(
    "분석할 리그를 선택하세요:", 
    ["🇺🇸 메이저리그 (MLB)", "🇰🇷 한국프로야구 (KBO)"]
    # 추후 "🇯🇵 일본프로야구 (NPB)", "⚽ 챔피언스리그" 등을 여기에 추가 가능합니다.
)

st.sidebar.markdown("---")
st.sidebar.info("해외 야구는 크롬의 '한국어로 번역' 기능을 켜시면 더욱 쾌적하게 이용할 수 있습니다.")

# ==========================================
# 🇺🇸 MLB 모드 렌더링
# ==========================================
if league_choice == "🇺🇸 메이저리그 (MLB)":
    st.header("🇺🇸 MLB AI 감독 모드 (배당 및 분석 탑재)")
    st.write("🔄 메이저리그 30개 구단 데이터베이스 동기화 중...")

    try:
        df_hitter, df_pitcher, team_bp_fip_dict = load_mlb_all_data()
        momentum_dict = load_mlb_team_momentum()
        
        selected_date = st.date_input("🗓️ 분석 날짜를 선택하세요:", date.today())
        df_schedule = load_mlb_schedule(selected_date)
        
        tab1, tab2, tab3 = st.tabs(["📅 매치업 및 실시간 라인업", "投 전체 투수 스탯", "🏃‍♂️ 전체 타자 스탯"])
        
        with tab1:
            if not df_schedule.empty:
                st.markdown("<p style='font-size:13px; color:#cccccc; margin-bottom:5px;'>※ 팀 이름 옆 숫자는 <b>'AI 자체 예상 배당(Implied Odds)'</b>입니다.</p>", unsafe_allow_html=True)
                html_table = "<table style='width:100%; border-collapse: collapse; margin-bottom: 20px; text-align: center; font-size: 15px;'>"
                html_table += "<tr style='background-color: #262730; color: white; border-bottom: 2px solid #555;'><th style='padding: 12px;'>경기시간(KST)</th><th style='padding: 12px;'>상태</th><th style='padding: 12px; text-align: left;'>홈 팀 <span style='color:#ffcc00; font-size:12px;'>[AI 배당]</span></th><th style='padding: 12px;'>홈 선발투수</th><th style='padding: 12px; text-align: left;'>어웨이 팀 (원정) <span style='color:#ffcc00; font-size:12px;'>[AI 배당]</span></th><th style='padding: 12px;'>어웨이 선발투수</th></tr>"
                for _, row in df_schedule.iterrows():
                    html_table += f"<tr style='border-bottom: 1px solid #333;'><td style='padding: 10px;'>{row['경기시간(KST)']}</td><td style='padding: 10px;'>{row['상태']}</td><td style='padding: 10px; text-align: left;'>{row['홈표시']}</td><td style='padding: 10px;'>{row['홈 선발투수']}</td><td style='padding: 10px; text-align: left;'>{row['원정표시']}</td><td style='padding: 10px;'>{row['어웨이 선발투수']}</td></tr>"
                html_table += "</table>"
                st.markdown(html_table, unsafe_allow_html=True)
                
                game_options = df_schedule['홈 팀'] + " (홈) vs " + df_schedule['어웨이 팀 (원정)'] + " (원정)"
                selected_game = st.selectbox("🔮 정밀 시뮬레이션 경기 선택:", game_options)
                
                row = df_schedule[game_options == selected_game].iloc[0]
                h_team, a_team, h_id, a_id = row['홈 팀'], row['어웨이 팀 (원정)'], row['홈 ID'], row['원정 ID']
                h_p, a_p, game_pk = row['홈 선발투수'], row['어웨이 선발투수'], row['gamePk']
                
                c1, c2, c3 = st.columns([2, 1, 2])
                with c1: st.markdown(f"#### <img src='https://www.mlbstatic.com/team-logos/{h_id}.svg' width='24' style='vertical-align: middle; margin-right: 8px;'> **홈: {h_team}**", unsafe_allow_html=True)
                with c2: st.markdown("<h4 style='text-align: center;'>VS</h4>", unsafe_allow_html=True)
                with c3: st.markdown(f"#### <img src='https://www.mlbstatic.com/team-logos/{a_id}.svg' width='24' style='vertical-align: middle; margin-right: 8px;'> **원정: {a_team}**", unsafe_allow_html=True)
                
                st.markdown("---")
                h_lineup, a_lineup, h_p_hand, a_p_hand = load_mlb_live_lineup(game_pk)
                
                if h_lineup and a_lineup:
                    st.success(f"✨ 라인업 확정! (투수 손에 맞춘 '플래툰 OPS' 자동 적용)")
                    col_l1, col_l2 = st.columns(2)
                    with col_l1:
                        st.markdown(f"**🏠 {h_team} 선발 타순 (vs {'좌완' if a_p_hand=='L' else '우완'} 투수)**")
                        for i, p in enumerate(h_lineup): st.write(f"{i+1}. {p['name']} <span style='color:#ffcc00;'>({p['pos']}/{p['batSide']}타)</span>", unsafe_allow_html=True)
                    with col_l2:
                        st.markdown(f"**✈️ {a_team} 선발 타순 (vs {'좌완' if h_p_hand=='L' else '우완'} 투수)**")
                        for i, p in enumerate(a_lineup): st.write(f"{i+1}. {p['name']} <span style='color:#ffcc00;'>({p['pos']}/{p['batSide']}타)</span>", unsafe_allow_html=True)
                    h_ops = calculate_platoon_ops(h_lineup, df_hitter, a_p_hand)
                    a_ops = calculate_platoon_ops(a_lineup, df_hitter, h_p_hand)
                else:
                    st.warning("🚨 라인업 준비중 - 팀 평균 스탯으로 임시 연산합니다.")
                    h_ops = df_hitter[(df_hitter['팀'] == h_team) & (df_hitter['타수'] > 100)]['OPS'].mean() or 0.720
                    a_ops = df_hitter[(df_hitter['팀'] == a_team) & (df_hitter['타수'] > 100)]['OPS'].mean() or 0.720
                    
                if st.button("🚀 MLB 최종 시뮬레이션 돌리기"):
                    my_bar = st.progress(0, text="분석 코멘터리를 작성 중입니다...")
                    for p in range(100):
                        time.sleep(0.01)
                        my_bar.progress(p + 1)
                    my_bar.empty()
                    
                    h_bp_fip = team_bp_fip_dict.get(h_team, 4.00)
                    a_bp_fip = team_bp_fip_dict.get(a_team, 4.00)
                    h_l10 = momentum_dict.get(h_team, {'rate': 0.5, 'str': '5 W - 5 L'})
                    a_l10 = momentum_dict.get(a_team, {'rate': 0.5, 'str': '5 W - 5 L'})
                    pf = MLB_PARK_FACTORS.get(h_team, 1.00)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.error(f"🏠 **{h_team} 전력**")
                        h_p_data = df_pitcher[df_pitcher['이름'] == h_p]
                        h_s_fip = h_p_data['FIP'].values[0] if not h_p_data.empty else 4.50
                        h_s_ip = h_p_data['평균이닝'].values[0] if not h_p_data.empty else 5.0
                        st.write(f"⚾ 선발 FIP: **{h_s_fip:.2f}** | 🔋 소화 이닝: **{h_s_ip:.1f}회**")
                        st.write(f"🛡️ 불펜 FIP: **{h_bp_fip:.2f}** | 🔥 보정 OPS: **{h_ops:.3f}**")
                    with col2:
                        st.info(f"✈️ **{a_team} 전력**")
                        a_p_data = df_pitcher[df_pitcher['이름'] == a_p]
                        a_s_fip = a_p_data['FIP'].values[0] if not a_p_data.empty else 4.50
                        a_s_ip = a_p_data['평균이닝'].values[0] if not a_p_data.empty else 5.0
                        st.write(f"⚾ 선발 FIP: **{a_s_fip:.2f}** | 🔋 소화 이닝: **{a_s_ip:.1f}회**")
                        st.write(f"🛡️ 불펜 FIP: **{a_bp_fip:.2f}** | 🔥 보정 OPS: **{a_ops:.3f}**")
                    
                    h_win, a_win, top3_scores, h_eff, a_eff, _ = run_mlb_simulation(h_s_fip, a_s_fip, h_s_ip, a_s_ip, h_ops, a_ops, h_bp_fip, a_bp_fip, h_l10['rate'], a_l10['rate'], pf)
                    
                    st.markdown("---")
                    st.subheader("🏆 세이버메트릭스 최종 리포트")
                    col_res1, col_res2 = st.columns(2)
                    with col_res1:
                        st.success(f"**{h_team} (홈) 승리 확률:** {h_win:.1f}%")
                        st.info(f"**{a_team} (원정) 승리 확률:** {a_win:.1f}%")
                    with col_res2:
                        st.warning(f"🎯 **예상 스코어 TOP 3**")
                        st.write(f"🥇 1순위: **{top3_scores[0]}** | 🥈 2순위: **{top3_scores[1]}** | 🥉 3순위: **{top3_scores[2]}**")
                    
                    st.markdown("### 📝 AI 전력 분석 브리핑")
                    comments = generate_ai_commentary(h_team, a_team, h_eff, a_eff, h_ops, a_ops, h_l10['rate'], a_l10['rate'], h_win)
                    for comment in comments:
                        st.markdown(f"> {comment}")
            else:
                st.info("예정된 경기가 없습니다.")
                
        with tab2:
            st.write("2026 시즌 전체 투수 세부 스탯")
            st.dataframe(df_pitcher[['이름', '팀', 'ERA', 'FIP', '평균이닝', '승', '패', '세이브', '출장', '선발', '이닝', '탈삼진', '볼넷', 'WHIP']], use_container_width=True)
            
        with tab3:
            st.write("2026 시즌 전체 타자 세부 스탯")
            st.dataframe(df_hitter[['이름', '팀', '타수', '안타', '홈런', '타점', '득점', '볼넷', '타율', 'OPS']], use_container_width=True)
            
    except Exception as e:
        st.error(f"오류 발생: {e}")

# ==========================================
# 🇰🇷 KBO 모드 렌더링
# ==========================================
elif league_choice == "🇰🇷 한국프로야구 (KBO)":
    st.header("🇰🇷 KBO AI 감독 모드 (테스트 버전)")
    st.info("🚨 현재 공식 API가 없어 임시 가상 데이터로 작동 중입니다.")

    df_h_kbo, df_p_kbo, bp_fip_dict_kbo = load_dummy_kbo_data()

    col1, col2 = st.columns(2)
    with col1:
        h_team_kbo = st.selectbox("🏠 홈 팀 선택", KBO_TEAMS, index=0)
        h_pitcher_kbo = st.selectbox(f"{h_team_kbo} 선발 투수", df_p_kbo[df_p_kbo['팀'] == h_team_kbo]['이름'].tolist())
    with col2:
        a_team_kbo = st.selectbox("✈️ 원정 팀 선택", KBO_TEAMS, index=1)
        a_pitcher_kbo = st.selectbox(f"{a_team_kbo} 선발 투수", df_p_kbo[df_p_kbo['팀'] == a_team_kbo]['이름'].tolist())

    st.markdown("---")

    if st.button("🚀 KBO 매치업 시뮬레이션 돌리기"):
        my_bar = st.progress(0, text="대구/잠실 등 구장 파크팩터를 적용하여 연산 중...")
        for p in range(100):
            time.sleep(0.01)
            my_bar.progress(p + 1)
        my_bar.empty()
        
        h_ops_k = df_h_kbo[df_h_kbo['팀'] == h_team_kbo]['OPS'].mean()
        a_ops_k = df_h_kbo[df_h_kbo['팀'] == a_team_kbo]['OPS'].mean()
        h_s_fip_k = df_p_kbo[df_p_kbo['이름'] == h_pitcher_kbo]['FIP'].values[0]
        h_s_ip_k = df_p_kbo[df_p_kbo['이름'] == h_pitcher_kbo]['평균이닝'].values[0]
        h_bp_k = bp_fip_dict_kbo[h_team_kbo]
        a_s_fip_k = df_p_kbo[df_p_kbo['이름'] == a_pitcher_kbo]['FIP'].values[0]
        a_s_ip_k = df_p_kbo[df_p_kbo['이름'] == a_pitcher_kbo]['평균이닝'].values[0]
        a_bp_k = bp_fip_dict_kbo[a_team_kbo]
        pf_k = KBO_PARK_FACTORS[h_team_kbo]
        
        c1, c2 = st.columns(2)
        with c1:
            st.error(f"🏠 **{h_team_kbo} 전력**")
            st.write(f"⚾ 선발 FIP: **{h_s_fip_k:.2f}** | 🔋 평균 소화 이닝: **{h_s_ip_k:.1f}회**")
            st.write(f"🛡️ 팀 불펜 FIP: **{h_bp_k:.2f}** | 🔥 타선 평균 OPS: **{h_ops_k:.3f}**")
        with c2:
            st.info(f"✈️ **{a_team_kbo} 전력**")
            st.write(f"⚾ 선발 FIP: **{a_s_fip_k:.2f}** | 🔋 평균 소화 이닝: **{a_s_ip_k:.1f}회**")
            st.write(f"🛡️ 팀 불펜 FIP: **{a_bp_k:.2f}** | 🔥 타선 평균 OPS: **{a_ops_k:.3f}**")
            
        st.markdown(f"**🏟️ 구장 환경 변수:** {h_team_kbo} 홈구장 (KBO 파크 팩터: **{pf_k}**)")
        
        h_win_k, a_win_k, top3_scores_k = run_kbo_simulation(h_s_fip_k, a_s_fip_k, h_s_ip_k, a_s_ip_k, h_ops_k, a_ops_k, h_bp_k, a_bp_k, pf_k)
        
        st.markdown("---")
        st.subheader("🏆 KBO 세이버메트릭스 최종 리포트")
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.success(f"**{h_team_kbo} (홈) 승리 확률:** {h_win_k:.1f}%")
            st.info(f"**{a_team_kbo} (원정) 승리 확률:** {a_win_k:.1f}%")
        with col_res2:
            st.warning(f"🎯 **가장 많이 나온 예상 스코어 TOP 3**")
            st.write(f"🥇 1순위: **{top3_scores_k[0][0]} ({top3_scores_k[0][1]/100:.1f}%)**")
            st.write(f"🥈 2순위: **{top3_scores_k[1][0]} ({top3_scores_k[1][1]/100:.1f}%)**")
            st.write(f"🥉 3순위: **{top3_scores_k[2][0]} ({top3_scores_k[2][1]/100:.1f}%)**")
