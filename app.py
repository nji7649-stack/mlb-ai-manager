import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date, timedelta
import random
from collections import Counter
import time

# --- [앱 설정] ---
st.set_page_config(page_title="통합 AI 스포츠 분석실", layout="wide")

# --- [NBA 데이터 로드 함수] ---
@st.cache_data(ttl=600)
def load_nba_schedule(target_date):
    date_str = target_date.strftime('%Y-%m-%d')
    url = f"https://www.balldontlie.io/api/v1/games?start_date={date_str}&end_date={date_str}"
    try:
        res = requests.get(url, timeout=10).json()
        games = res.get('data', [])
        data = []
        for g in games:
            data.append({
                '경기날짜': date_str,
                '대진': f"{g['visitor_team']['abbreviation']} vs {g['home_team']['abbreviation']}",
                '결과': f"{g['visitor_score']} : {g['home_score']}"
            })
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

# --- [MLB/KBO 함수들] ---
# (기존 MLB_PARK_FACTORS 등 모든 함수들을 여기에 넣습니다)
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date, timedelta
import random
from collections import Counter
import time

# 앱 전체 기본 설정
st.set_page_config(page_title="통합 AI 스포츠 분석실", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #f5f5f5; }
    .stMetric { background-color: #1a1c23; padding: 20px; border-radius: 8px; border-left: 5px solid #ff4b4b; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🇺🇸 MLB 전용 설정 및 함수
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
def load_mlb_schedule(target_date_kst):
    # 💡 MLB 시차 반영: 한국 시간 기준에서 하루를 빼서 미국 현지 경기 날짜로 변환
    us_date = target_date_kst - timedelta(days=1)
    date_str = us_date.strftime("%Y-%m-%d")
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
    
    h_tie_win_prob = h_expected_runs / (h_expected_runs + a_expected_runs) if (h_expected_runs + a_expected_runs) > 0 else 0.5

    for _ in range(num_sims):
        h_score = max(0, int(random.gauss(h_expected_runs, 2.3)))
        a_score = max(0, int(random.gauss(a_expected_runs, 2.3)))
        
        if h_score == a_score:
            if random.random() < h_tie_win_prob: h_score += 1
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
    if ops_diff > 0.050: comments.append(f"🏏 **[타선] {h_team} 우세:** 전반적인 타선의 파괴력이 상대 마운드를 압도합니다.")
    elif ops_diff < -0.050: comments.append(f"🏏 **[타선] {a_team} 우세:** 원정팀 타선이 화력에서 우위를 점하고 있습니다.")
    else: comments.append("🏏 **[타선] 화력 팽팽:** 양 팀 화력 기대치가 대등합니다. 클러치 상황의 집중력이 승부를 가를 것입니다.")
    if h_win_prob >= 62.0: comments.append(f"💡 **[종합 요약]** 투타 전반에서 **{h_team}**의 우세가 뚜렷합니다. 이변이 없는 한 승리 가능성이 높습니다.")
    elif h_win_prob <= 38.0: comments.append(f"💡 **[종합 요약]** 원정팀 **{a_team}**의 전력이 압도합니다. 원정팀 역배당(또는 정배) 가치가 높습니다.")
    else: comments.append(f"💡 **[종합 요약]** 전력이 팽팽한 **박빙 매치(Toss-up)**입니다. 선발 이닝 소화력과 벤치 개입이 승패를 가릅니다.")
    return comments


# ==========================================
# 📺 메인 UI - 사이드바(좌측 메뉴) 구성
# ==========================================
st.sidebar.title("⚾ 통합 AI 스포츠 분석실")
st.sidebar.markdown("클릭 한 번으로 리그를 전환하세요.")

# 💡 'us', 'KR' 국기 텍스트 깔끔하게 제거
league_choice = st.sidebar.radio(
    "분석할 리그를 선택하세요:", 
    ["메이저리그 (MLB)", "한국프로야구 (KBO)"]
)

st.sidebar.markdown("---")
st.sidebar.info("해외 야구는 크롬의 '한국어로 번역' 기능을 켜시면 더욱 쾌적하게 이용할 수 있습니다.")


# ==========================================
# 🇺🇸 MLB 모드 렌더링
# ==========================================
if league_choice == "메이저리그 (MLB)":
    st.header("🇺🇸 MLB AI 감독 모드 (배당 및 분석 탑재)")
    st.write("🔄 메이저리그 30개 구단 데이터베이스 동기화 중...")

    try:
        df_hitter, df_pitcher, team_bp_fip_dict = load_mlb_all_data()
        momentum_dict = load_mlb_team_momentum()
        
        kst_now = datetime.utcnow() + timedelta(hours=9)
        st.info("※ 달력에서 '오늘(한국 날짜)'을 선택하면 시차가 자동 계산되어 어제 열린 미국 현지 경기가 표시됩니다.")
        selected_date = st.date_input("🗓️ 분석 날짜를 선택하세요 (한국시간 기준):", kst_now.date())
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
                selected_game = st.selectbox("🔮 정밀 시뮬레이션 경기 선택:", game_options, key="mlb_game_selector")
                
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
elif league_choice == "한국프로야구 (KBO)":
    st.header("🇰🇷 KBO AI 감독 모드 (최종 V5.0)")
    st.caption("✅ 파이썬 전용 크롤링 엔진 및 커스텀 라인업 시뮬레이터 탑재")

    KBO_PARK_FACTORS = {
        '삼성': 1.06, 'SSG': 1.05, '롯데': 1.02, 'NC': 1.01,
        'KT': 1.00, '한화': 1.00, 'KIA': 0.99, '키움': 0.97,
        'LG': 0.95, '두산': 0.95
    }

    kst_now = datetime.utcnow() + timedelta(hours=9)
    selected_kbo_date = st.date_input("🗓️ 분석 날짜를 선택하세요:", kst_now.date(), key="kbo_date_picker")

    # 💡 네이버 봇 차단을 뚫기 위한 강력한 파이썬 스크래핑 함수
    @st.cache_data(ttl=60)
    def load_kbo_schedule(target_date):
        date_str = target_date.strftime('%Y-%m-%d')
        # ✅ 한글 지우고 진짜 변수명(date_str)으로 교체 완료!
        url = f"https://api-gw.sports.naver.com/schedule/games?upperCategoryId=kbaseball&categoryId=kbo&fromDate={date_str}&toDate={date_str}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://sports.naver.com/"
        }
        games = []
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                games_data = res.json().get('result', {}).get('games', [])
                for game in games_data:
                    # KBO 경기만 확실하게 필터링 (대소문자 차이 방어)
                    if str(game.get('categoryId', '')).lower() != 'kbo': continue
                    
                    h_score = game.get('homeTeamScore', 0)
                    a_score = game.get('awayTeamScore', 0)
                    status_code = game.get('statusCode', '')
                    if status_code == 'RESULT': status_str = f"✅ 종료 ({h_score}:{a_score})"
                    elif status_code == 'STARTED': status_str = f"🔥 진행중 ({h_score}:{a_score})"
                    elif status_code == 'CANCELED': status_str = "☔ 취소"
                    else: status_str = "⏳ 예정"
                    
                    game_time = game.get('gameStartTime') or game.get('gameTime') or 'TBD'
                    if game_time != 'TBD' and len(game_time) >= 5: game_time = game_time[:5]
                    
                    # 숨겨진 선발 투수 데이터 철저하게 수집
                    h_starter = game.get('homeStarterName') or game.get('homeStarter') or '미발표'
                    a_starter = game.get('awayStarterName') or game.get('awayStarter') or '미발표'
                    
                    games.append({
                        '경기시간': game_time, '상태': status_str,
                        '홈 팀': game.get('homeTeamName', '홈팀'), '홈 선발투수': h_starter,
                        '원정 팀': game.get('awayTeamName', '원정팀'), '원정 선발투수': a_starter
                    })
        except Exception as e:
            pass 
        return pd.DataFrame(games)

    PITCHER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=0&single=true&output=csv"
    BATTER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=779417540&single=true&output=csv"

    @st.cache_data(ttl=10)
    def load_kbo_data(url, data_type):
        df = pd.read_csv(url, header=None, dtype=str)
        df = df.dropna(subset=[1])
        df = df[df[1] != '선수명']
        
        def parse_innings(ip_val):
            try:
                s = str(ip_val).strip()
                if '1/3' in s: return float(s.split()[0]) + 0.333 if ' ' in s else 0.333
                if '2/3' in s: return float(s.split()[0]) + 0.667 if ' ' in s else 0.667
                return float(s)
            except:
                return 1.0

        if data_type == 'pitcher':
            cols = {
                0: '순위', 1: '선수명', 2: '소속팀', 3: '방어율', 4: '경기수', 5: '승리', 6: '패배', 
                7: '세이브', 8: '홀드', 9: '승률', 10: '소화이닝', 11: '피안타', 12: '피홈런', 13: '볼넷', 
                14: '데드볼', 15: '탈삼진', 16: '실점', 17: '자책점', 18: '이닝당출루허용'
            }
            df = df.rename(columns=cols)
            df['소화이닝_num'] = df['소화이닝'].apply(parse_innings)
            df['피홈런'] = pd.to_numeric(df['피홈런'], errors='coerce').fillna(0)
            df['볼넷'] = pd.to_numeric(df['볼넷'], errors='coerce').fillna(0)
            df['탈삼진'] = pd.to_numeric(df['탈삼진'], errors='coerce').fillna(0)
            df['방어율'] = pd.to_numeric(df['방어율'], errors='coerce').fillna(4.50)
            
            df['FIP_계산'] = df.apply(lambda x: ((13*x['피홈런'] + 3*x['볼넷'] - 2*x['탈삼진']) / x['소화이닝_num']) + 3.10 if x['소화이닝_num'] > 0 else x['방어율'], axis=1)
            df['FIP'] = df.apply(lambda x: x['FIP_계산'] if 0 < x['FIP_계산'] < 15 else x['방어율'], axis=1)
        else:
            cols = {
                0: '순위', 1: '선수명', 2: '소속팀', 3: '타율', 4: '경기수', 5: '타석', 6: '타수', 
                7: '득점', 8: '안타', 9: '2루타', 10: '3루타', 11: '홈런', 12: '루타', 13: '타점', 
                14: '희생번트', 15: '희생플라이'
            }
            df = df.rename(columns=cols)
            df['타율'] = pd.to_numeric(df['타율'], errors='coerce').fillna(0.0)
            df['타수'] = pd.to_numeric(df['타수'], errors='coerce').fillna(1)
            df['루타'] = pd.to_numeric(df['루타'], errors='coerce').fillna(0)
            df['장타율'] = df.apply(lambda x: x['루타'] / x['타수'] if x['타수'] > 0 else 0, axis=1)
            df['가상OPS'] = df['타율'] + df['장타율']
        return df

    try:
        with st.spinner("KBO 일정표 및 구글 시트 데이터 로딩 중..."):
            df_p = load_kbo_data(PITCHER_URL, 'pitcher')
            df_h = load_kbo_data(BATTER_URL, 'batter')
            
            p_format_dict = {}
            for _, r in df_p.iterrows():
                name = str(r['선수명'])
                w = r.get('승리', '0')
                l = r.get('패배', '0')
                try: era = float(r.get('방어율', 4.50))
                except: era = 4.50
                try: ip = max(float(r.get('소화이닝_num', 1)), 0.1)
                except: ip = 1.0
                try: k = float(r.get('탈삼진', 0))
                except: k = 0.0
                try: bb = float(r.get('볼넷', 0))
                except: bb = 0.0
                k9 = (k / ip) * 9
                bb9 = (bb / ip) * 9
                p_format_dict[name] = f"{name} ({w}승 {l}패 | ERA {era:.2f} | 9이닝 평균삼진 {k9:.1f} | 9이닝 평균볼넷 {bb9:.1f})"

            b_format_dict = {}
            for _, r in df_h.iterrows():
                name = str(r['선수명'])
                try: avg = float(r.get('타율', 0.000))
                except: avg = 0.000
                try: ops = float(r.get('가상OPS', 0.000))
                except: ops = 0.000
                b_format_dict[name] = f"{name} (타율 {avg:.3f} | 가상OPS {ops:.3f})"

        tab1, tab2, tab3 = st.tabs(["🔥 매치업 분석", "⚾ 투수 기록실", "🏏 타자 기록실"])

        with tab1:
            st.subheader(f"📅 {selected_kbo_date.strftime('%Y년 %m월 %d일')} KBO 일정 및 스코어")
            df_kbo_schedule = load_kbo_schedule(selected_kbo_date)
            
            if not df_kbo_schedule.empty:
                st.dataframe(df_kbo_schedule, use_container_width=True, hide_index=True)
            else:
                st.info("선택하신 날짜에 진행된 KBO 경기가 없거나 정보를 불러올 수 없습니다.")
                
            st.markdown("<br><hr>", unsafe_allow_html=True)
            
            st.subheader("🔥 커스텀 라인업 승부 예측 시뮬레이션")
            st.write("원하시는 팀의 선발투수와 **선발 타자 9명**을 직접 골라 팀의 진짜 파괴력을 측정하세요.")
            
            teams = df_p['소속팀'].dropna().unique().tolist()
            col1, col2 = st.columns(2)
            
            h_lineup = []
            a_lineup = []
            
            with col1:
                st.error("🏠 **홈 팀 라인업 편성**")
                h_team = st.selectbox("홈 팀", teams, key='ht')
                h_p_list = df_p[df_p['소속팀'] == h_team]['선수명'].dropna().tolist()
                h_p = st.selectbox("선발투수", h_p_list if h_p_list else ["선수없음"], format_func=lambda x: p_format_dict.get(x, x), key='hp')
                
                st.markdown("##### 🏏 홈팀 1~9번 타순")
                h_b_list = df_h[df_h['소속팀'] == h_team]['선수명'].dropna().tolist()
                for i in range(1, 10):
                    default_idx = i - 1 if i - 1 < len(h_b_list) else 0
                    batter = st.selectbox(f"{i}번 타자", h_b_list if h_b_list else ["선수없음"], index=default_idx, format_func=lambda x: b_format_dict.get(x, x), key=f'h_b_{i}')
                    h_lineup.append(batter)
                
            with col2:
                st.info("✈️ **원정 팀 라인업 편성**")
                a_teams = [t for t in teams if t != h_team]
                a_team = st.selectbox("원정 팀", a_teams if a_teams else teams, key='at')
                a_p_list = df_p[df_p['소속팀'] == a_team]['선수명'].dropna().tolist()
                a_p = st.selectbox("선발투수", a_p_list if a_p_list else ["선수없음"], format_func=lambda x: p_format_dict.get(x, x), key='ap')
                
                st.markdown("##### 🏏 원정팀 1~9번 타순")
                a_b_list = df_h[df_h['소속팀'] == a_team]['선수명'].dropna().tolist()
                for i in range(1, 10):
                    default_idx = i - 1 if i - 1 < len(a_b_list) else 0
                    batter = st.selectbox(f"{i}번 타자", a_b_list if a_b_list else ["선수없음"], index=default_idx, format_func=lambda x: b_format_dict.get(x, x), key=f'a_b_{i}')
                    a_lineup.append(batter)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 KBO 몬테카를로 시뮬레이션 실행 (10,000회)", use_container_width=True):
                my_bar = st.progress(0, text="선택하신 타선의 기대 득점을 연산 중입니다...")
                for p in range(100):
                    time.sleep(0.01)
                    my_bar.progress(p + 1)
                my_bar.empty()

                h_p_stat = df_p[df_p['선수명'] == h_p]
                h_fip = h_p_stat['FIP'].iloc[0] if not h_p_stat.empty else 4.50
                a_p_stat = df_p[df_p['선수명'] == a_p]
                a_fip = a_p_stat['FIP'].iloc[0] if not a_p_stat.empty else 4.50
                
                if len(h_lineup) > 0: h_ops = df_h[df_h['선수명'].isin(h_lineup)]['가상OPS'].mean()
                else: h_ops = df_h[df_h['소속팀'] == h_team]['가상OPS'].mean()
                
                if len(a_lineup) > 0: a_ops = df_h[df_h['선수명'].isin(a_lineup)]['가상OPS'].mean()
                else: a_ops = df_h[df_h['소속팀'] == a_team]['가상OPS'].mean()
                
                h_ops = 0.720 if pd.isna(h_ops) else h_ops
                a_ops = 0.720 if pd.isna(a_ops) else a_ops

                pf = KBO_PARK_FACTORS.get(h_team, 1.00)
                
                h_win, a_win, top3_scores, h_eff, a_eff, _ = run_mlb_simulation(
                    h_fip, a_fip, 5.0, 5.0, h_ops, a_ops, 4.0, 4.0, 0.5, 0.5, pf
                )
                
                st.markdown("---")
                col_i1, col_i2 = st.columns(2)
                with col_i1:
                    st.error(f"🏠 **{h_team} 선택 라인업 전력**")
                    st.write(f"⚾ 선발 FIP (수비무관 방어율): **{h_fip:.2f}**")
                    st.write(f"🔥 타선 평균 가상 OPS: **{h_ops:.3f}**")
                with col_i2:
                    st.info(f"✈️ **{a_team} 선택 라인업 전력**")
                    st.write(f"⚾ 선발 FIP (수비무관 방어율): **{a_fip:.2f}**")
                    st.write(f"🔥 타선 평균 가상 OPS: **{a_ops:.3f}**")
                    
                st.markdown("### 🏆 최종 세이버메트릭스 리포트")
                col_res1, col_res2 = st.columns(2)
                with col_res1:
                    st.success(f"**{h_team} (홈) 승리 확률:** {h_win:.1f}%")
                    st.info(f"**{a_team} (원정) 승리 확률:** {a_win:.1f}%")
                with col_res2:
                    st.warning(f"🎯 **가장 많이 나온 시뮬레이션 스코어 TOP 3**")
                    st.write(f"🥇 1순위: **{top3_scores[0]}** | 🥈 2순위: **{top3_scores[1]}** | 🥉 3순위: **{top3_scores[2]}**")
                    
                st.markdown("### 📝 AI 전력 분석 브리핑")
                comments = generate_ai_commentary(h_team, a_team, h_fip, a_fip, h_ops, a_ops, 0.5, 0.5, h_win)
                for comment in comments:
                    st.markdown(f"> {comment}")

        with tab2:
            st.write("2026 시즌 투수 기록실 (FIP 수치 보정 완료)")
            st.dataframe(df_p, use_container_width=True)
            
        with tab3:
            st.write("2026 시즌 타자 기록실 (가상 OPS 계산 탑재)")
            st.dataframe(df_h, use_container_width=True)

    except Exception as e:
        st.error(f"데이터 오류 발생: {e}")


MLB_PARK_FACTORS = {'Colorado Rockies': 1.12, 'Cincinnati Reds': 1.08, 'Boston Red Sox': 1.07, 'Texas Rangers': 1.05, 'Chicago White Sox': 1.04, 'Atlanta Braves': 1.03, 'Los Angeles Dodgers': 1.03, 'Philadelphia Phillies': 1.02, 'Houston Astros': 1.01, 'Baltimore Orioles': 1.00, 'Toronto Blue Jays': 1.00, 'Minnesota Twins': 1.00, 'Chicago Cubs': 1.00, 'New York Yankees': 1.00, 'Kansas City Royals': 0.99, 'Arizona Diamondbacks': 0.99, 'Milwaukee Brewers': 0.98, 'Los Angeles Angels': 0.98, 'Washington Nationals': 0.98, 'San Francisco Giants': 0.97, 'Miami Marlins': 0.97, 'Pittsburgh Pirates': 0.96, 'Cleveland Guardians': 0.96, 'St. Louis Cardinals': 0.96, 'Detroit Tigers': 0.95, 'Tampa Bay Rays': 0.95, 'New York Mets': 0.95, 'Athletics': 0.94, 'San Diego Padres': 0.94, 'Seattle Mariners': 0.93}
POSITION_TRANSLATIONS = {'P': '투수', 'C': '포수', '1B': '1루수', '2B': '2루수', '3B': '3루수', 'SS': '유격수', 'LF': '좌익수', 'CF': '중견수', 'RF': '우익수', 'DH': '지명타자', 'TWP': '투타겸업', 'O': '외야수', 'IF': '내야수', 'B': '야수', 'PH': '대타', 'PR': '대주자'}

# (기존 load_mlb_all_data, load_mlb_team_momentum, calculate_mlb_ai_odds, load_mlb_schedule, load_mlb_live_lineup, calculate_platoon_ops, run_mlb_simulation, generate_ai_commentary 함수들을 여기에 차례대로 붙이세요)

# --- [사이드바 및 메인 UI] ---
st.sidebar.title("⚾ 통합 AI 스포츠 분석실")
league_choice = st.sidebar.radio("분석할 리그를 선택하세요:", ["메이저리그 (MLB)", "한국프로야구 (KBO)", "NBA (농구)"])

if league_choice == "메이저리그 (MLB)":
    # (기존 MLB 렌더링 코드들 붙이기)
elif league_choice == "한국프로야구 (KBO)":
    # (기존 KBO 렌더링 코드들 붙이기)
elif league_choice == "NBA (농구)":
    st.header("🏀 NBA AI 분석실")
    nba_date = st.date_input("🗓️ 날짜 선택", datetime.now().date())
    df_nba = load_nba_schedule(nba_date)
    if not df_nba.empty: st.dataframe(df_nba, use_container_width=True)
    else: st.info("선택하신 날짜에 진행된 NBA 경기가 없습니다.")
