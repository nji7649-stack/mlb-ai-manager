import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date, timedelta
import random
from collections import Counter
import time

# ==========================================
# 🏠 앱 전체 기본 설정
# ==========================================
st.set_page_config(page_title="통합 AI 스포츠 분석실", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #f5f5f5; }
    .stMetric { background-color: #1a1c23; padding: 20px; border-radius: 8px; border-left: 5px solid #ff4b4b; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🏀 [새로운 기능] NBA 전용 함수
# ==========================================
@st.cache_data(ttl=600)
@st.cache_data(ttl=600)
def load_nba_schedule(target_date):
    date_str = target_date.strftime('%Y-%m-%d')
    # balldontlie v1 API는 이제 키가 필수입니다
    url = f"https://api.balldontlie.io/v1/games?dates[]={date_str}" 
    headers = {"Authorization": "470ab1a9-a550-4eba-9e06-dd55721c64a9"}
    try:
        res = requests.get(url, headers=headers, timeout=10).json()
        games = res.get('data', [])
        data = []
        for g in games:
            data.append({
                '경기시간': g.get('status', '종료'),
                '원정 팀': g.get('visitor_team', {}).get('abbreviation', ''),
                '원정 점수': g.get('visitor_score', 0),
                '홈 팀': g.get('home_team', {}).get('abbreviation', ''),
                '홈 점수': g.get('home_score', 0)
            })
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"데이터 로딩 오류: {e}")
        return pd.DataFrame()

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
    except: return None, None, 'R', 'R'

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
    else: comments.append("💡 **[종합 요약]** 전력이 팽팽한 **박빙 매치(Toss-up)**입니다. 선발 이닝 소화력과 벤치 개입이 승패를 가릅니다.")
    return comments

# ==========================================
# 🇰🇷 KBO 전용 함수
# ==========================================
@st.cache_data(ttl=60)
def load_kbo_schedule(target_date):
    date_str = target_date.strftime('%Y-%m-%d')
    url = f"https://api-gw.sports.naver.com/schedule/games?upperCategoryId=kbaseball&categoryId=kbo&fromDate={date_str}&toDate={date_str}"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://sports.naver.com/"}
    games = []
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            games_data = res.json().get('result', {}).get('games', [])
            for game in games_data:
                if str(game.get('categoryId', '')).lower() != 'kbo': continue
                h_score = game.get('homeTeamScore', 0)
                a_score = game.get('awayTeamScore', 0)
                status_code = game.get('statusCode', '')
                if status_code == 'RESULT': status_str = f"✅ 종료 ({h_score}:{a_score})"
                elif status_code == 'STARTED': status_str = f"🔥 진행중 ({h_score}:{a_score})"
                elif status_code == 'CANCELED': status_str = "☔ 취소"
                else: status_str = "⏳ 예정"
                game_time = game.get('gameStartTime') or game.get('gameTime') or 'TBD'
                h_starter = game.get('homeStarterName') or '미발표'
                a_starter = game.get('awayStarterName') or '미발표'
                games.append({'경기시간': game_time[:5], '상태': status_str, '홈 팀': game.get('homeTeamName'), '홈 선발투수': h_starter, '원정 팀': game.get('awayTeamName'), '원정 선발투수': a_starter})
    except: pass
    return pd.DataFrame(games)

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
        except: return 1.0
    if data_type == 'pitcher':
        cols = {0:'순위', 1:'선수명', 2:'소속팀', 3:'방어율', 4:'경기수', 5:'승리', 6:'패배', 7:'세이브', 8:'홀드', 9:'승률', 10:'소화이닝', 11:'피안타', 12:'피홈런', 13:'볼넷', 14:'데드볼', 15:'탈삼진', 16:'실점', 17:'자책점', 18:'이닝당출루허용'}
        df = df.rename(columns=cols)
        df['소화이닝_num'] = df['소화이닝'].apply(parse_innings)
        df['피홈런'] = pd.to_numeric(df['피홈런'], errors='coerce').fillna(0)
        df['볼넷'] = pd.to_numeric(df['볼넷'], errors='coerce').fillna(0)
        df['탈삼진'] = pd.to_numeric(df['탈삼진'], errors='coerce').fillna(0)
        df['방어율'] = pd.to_numeric(df['방어율'], errors='coerce').fillna(4.50)
        df['FIP'] = df.apply(lambda x: ((13*x['피홈런'] + 3*x['볼넷'] - 2*x['탈삼진']) / x['소화이닝_num']) + 3.10 if x['소화이닝_num'] > 0 else x['방어율'], axis=1)
    else:
        cols = {0:'순위', 1:'선수명', 2:'소속팀', 3:'타율', 4:'경기수', 5:'타석', 6:'타수', 7:'득점', 8:'안타', 9:'2루타', 10:'3루타', 11:'홈런', 12:'루타', 13:'타점', 14:'희생번트', 15:'희생플라이'}
        df = df.rename(columns=cols)
        df['타율'] = pd.to_numeric(df['타율'], errors='coerce').fillna(0.0)
        df['타수'] = pd.to_numeric(df['타수'], errors='coerce').fillna(1)
        df['루타'] = pd.to_numeric(df['루타'], errors='coerce').fillna(0)
        df['가상OPS'] = df['타율'] + (df['루타'] / df['타수'])
    return df

# ==========================================
# 📺 메인 UI 및 사이드바 구성
# ==========================================
st.sidebar.title("⚾ 통합 AI 스포츠 분석실")
league_choice = st.sidebar.radio("분석할 리그를 선택하세요:", ["메이저리그 (MLB)", "한국프로야구 (KBO)", "NBA (농구)"])
st.sidebar.markdown("---")

# 🇺🇸 MLB 모드
if league_choice == "메이저리그 (MLB)":
    st.header("🇺🇸 MLB AI 감독 모드")
    try:
        df_hitter, df_pitcher, team_bp_fip_dict = load_mlb_all_data()
        momentum_dict = load_mlb_team_momentum()
        selected_date = st.date_input("🗓️ 분석 날짜 선택(KST):", datetime.now().date())
        df_schedule = load_mlb_schedule(selected_date)
        tab1, tab2, tab3 = st.tabs(["매치업 분석", "투수 스탯", "타자 스탯"])
        with tab1:
            if not df_schedule.empty:
                st.dataframe(df_schedule[['경기시간(KST)', '상태', '홈 팀', '홈 선발투수', '어웨이 팀 (원정)', '어웨이 선발투수']], use_container_width=True)
                game_options = df_schedule['홈 팀'] + " vs " + df_schedule['어웨이 팀 (원정)']
                selected_game = st.selectbox("🔮 정밀 시뮬레이션 선택:", game_options)
                row = df_schedule[game_options == selected_game].iloc[0]
                if st.button("🚀 시뮬레이션 실행"):
                    h_team, a_team = row['홈 팀'], row['어웨이 팀 (원정)']
                    h_p, a_p = row['홈 선발투수'], row['어웨이 선발투수']
                    h_ops = df_hitter[df_hitter['팀'] == h_team]['OPS'].mean() or 0.720
                    a_ops = df_hitter[df_hitter['팀'] == a_team]['OPS'].mean() or 0.720
                    h_win, a_win, top3, h_eff, a_eff, _ = run_mlb_simulation(4.5, 4.5, 5.0, 5.0, h_ops, a_ops, 4.0, 4.0, 0.5, 0.5, 1.0)
                    st.success(f"🏠 {h_team} 승률: {h_win:.1f}% | ✈️ {a_team} 승률: {a_win:.1f}%")
                    for c in generate_ai_commentary(h_team, a_team, h_eff, a_eff, h_ops, a_ops, 0.5, 0.5, h_win): st.info(c)
            else: st.info("예정된 경기가 없습니다.")
        with tab2: st.dataframe(df_pitcher, use_container_width=True)
        with tab3: st.dataframe(df_hitter, use_container_width=True)
    except Exception as e: st.error(f"오류: {e}")

# 🇰🇷 KBO 모드
elif league_choice == "한국프로야구 (KBO)":
    st.header("🇰🇷 KBO AI 감독 모드")
    PITCHER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=0&single=true&output=csv"
    BATTER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=779417540&single=true&output=csv"
    try:
        df_p = load_kbo_data(PITCHER_URL, 'pitcher')
        df_h = load_kbo_data(BATTER_URL, 'batter')
        selected_kbo_date = st.date_input("🗓️ 날짜 선택:", datetime.now().date())
        df_kbo_schedule = load_kbo_schedule(selected_kbo_date)
        tab1, tab2, tab3 = st.tabs(["매치업 분석", "투수 기록", "타자 기록"])
        with tab1:
            if not df_kbo_schedule.empty: st.dataframe(df_kbo_schedule, use_container_width=True)
            else: st.info("경기가 없습니다.")
        with tab2: st.dataframe(df_p, use_container_width=True)
        with tab3: st.dataframe(df_h, use_container_width=True)
    except Exception as e: st.error(f"데이터 오류: {e}")

# 🏀 NBA 모드 (새로 추가됨)
elif league_choice == "NBA (농구)":
    st.header("🏀 NBA AI 분석실")
    nba_date = st.date_input("🗓️ NBA 경기 날짜 선택", datetime.now().date() - timedelta(days=1))
    with st.spinner("NBA 데이터를 불러오는 중..."):
        df_nba = load_nba_schedule(nba_date)
        if not df_nba.empty:
            st.write(f"### 📅 {nba_date.strftime('%Y-%m-%d')} 경기 결과 및 일정")
            st.dataframe(df_nba, use_container_width=True, hide_index=True)
        else:
            st.info("선택하신 날짜에 진행된 NBA 경기가 없거나 데이터를 불러올 수 없습니다. 날짜를 변경해 보세요.")
