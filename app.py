import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date, timedelta
import random
from collections import Counter
import time

st.set_page_config(page_title="MLB AI 감독 모드", layout="wide")
st.title("⚾ MLB AI 감독 모드 V13.0 (세부 스탯 리더보드 확장판)")

PARK_FACTORS = {
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
    'TWP': '투타겸업', 'O': '외야수', 'IF': '내야수', 'B': '야수', 
    'PH': '대타', 'PR': '대주자'
}

@st.cache_data(ttl=3600)
def load_mlb_all_data():
    # 💡 타자 세부 스탯 대거 추가 추출
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
    
    # 💡 투수 세부 스탯 대거 추가 추출
    pitcher_url = "https://statsapi.mlb.com/api/v1/stats?stats=season&group=pitching&gameType=R&season=2026&playerPool=ALL&limit=1500"
    p_splits = requests.get(pitcher_url).json()['stats'][0]['splits']
    pitcher_list = [{
        '이름': r['player']['fullName'], '팀': r['team']['name'], 
        '승': r['stat'].get('wins', 0), '패': r['stat'].get('losses', 0),
        '세이브': r['stat'].get('saves', 0), '출장': r['stat'].get('gamesPlayed', 0), 
        '선발': r['stat'].get('gamesStarted', 0), '이닝': r['stat'].get('inningsPitched', '0.0'),
        '피안타율': r['stat'].get('avg', '.000'), 'WHIP': r['stat'].get('whip', '0.00'),
        '탈삼진': r['stat'].get('strikeOuts', 0), '볼넷': r['stat'].get('baseOnBalls', 0),
        'ERA': r['stat'].get('era', '99.99')
    } for r in p_splits]
    df_p = pd.DataFrame(pitcher_list)
    df_p['ERA_num'] = pd.to_numeric(df_p['ERA'], errors='coerce').fillna(4.50)
    df_p['이닝_num'] = pd.to_numeric(df_p['이닝'], errors='coerce').fillna(0.0)
    
    df_bullpen = df_p[(df_p['출장'] > df_p['선발']) & (df_p['이닝_num'] >= 5.0)]
    team_bullpen_era = df_bullpen.groupby('팀')['ERA_num'].mean().to_dict()
    
    return df_h, df_p, team_bullpen_era

@st.cache_data(ttl=3600)
def load_team_momentum():
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

@st.cache_data(ttl=300)
def load_schedule(target_date):
    date_str = target_date.strftime("%Y-%m-%d")
    schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}&hydrate=probablePitcher"
    res = requests.get(schedule_url).json()
    games = []
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
            else:
                time_str = "TBD"
                
            status = game['status']['abstractGameState']
            h_score = game['teams']['home'].get('score', 0)
            a_score = game['teams']['away'].get('score', 0)
            
            if status == 'Final': status_str = f"✅ 종료 ({h_score}:{a_score})"
            elif status == 'Live': status_str = f"🔥 진행중 ({h_score}:{a_score})"
            else: status_str = "⏳ 예정"

            home_display = f"<img src='https://www.mlbstatic.com/team-logos/{home_id}.svg' width='22' style='vertical-align:middle; margin-right:8px;'> <b>{home_team}</b>"
            away_display = f"<img src='https://www.mlbstatic.com/team-logos/{away_id}.svg' width='22' style='vertical-align:middle; margin-right:8px;'> <b>{away_team}</b>"

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
def load_live_lineup(game_pk):
    try:
        url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
        res = requests.get(url).json()
        home_order = res['teams']['home'].get('battingOrder', [])
        away_order = res['teams']['away'].get('battingOrder', [])
        if len(home_order) == 0 or len(away_order) == 0: return None, None
        h_players = res['teams']['home']['players']
        a_players = res['teams']['away']['players']
        
        h_lookup = {}
        for k, p in h_players.items():
            if 'person' in p and 'id' in p['person']:
                pos_code = p.get('position', {}).get('abbreviation', 'B')
                h_lookup[p['person']['id']] = {
                    'name': p['person']['fullName'],
                    'pos': POSITION_TRANSLATIONS.get(pos_code, pos_code)
                }
                
        a_lookup = {}
        for k, p in a_players.items():
            if 'person' in p and 'id' in p['person']:
                pos_code = p.get('position', {}).get('abbreviation', 'B')
                a_lookup[p['person']['id']] = {
                    'name': p['person']['fullName'],
                    'pos': POSITION_TRANSLATIONS.get(pos_code, pos_code)
                }
                
        home_lineup = [h_lookup.get(pid, {'name': 'Unknown', 'pos': '야수'}) for pid in home_order]
        away_lineup = [a_lookup.get(pid, {'name': 'Unknown', 'pos': '야수'}) for pid in away_order]
        return home_lineup, away_lineup
    except:
        return None, None

def run_simulation(h_s_era, a_s_era, h_ops, a_ops, h_bp_era, a_bp_era, h_l10_rate, a_l10_rate, park_factor, num_sims=10000):
    try: h_s_era = float(h_s_era) if float(h_s_era) < 50 else 4.50
    except: h_s_era = 4.50
    try: a_s_era = float(a_s_era) if float(a_s_era) < 50 else 4.50
    except: a_s_era = 4.50

    h_eff_era = (h_s_era * 0.6) + (h_bp_era * 0.4)
    a_eff_era = (a_s_era * 0.6) + (a_bp_era * 0.4)

    h_momentum = 1.0 + (h_l10_rate - 0.5) * 0.1
    a_momentum = 1.0 + (a_l10_rate - 0.5) * 0.1

    h_attack = (h_ops / 0.720) * h_momentum if h_ops > 0 else 1.0 * h_momentum
    a_attack = (a_ops / 0.720) * a_momentum if a_ops > 0 else 1.0 * a_momentum

    h_expected_runs = ((a_eff_era * h_attack) + 0.2) * park_factor
    a_expected_runs = (h_eff_era * a_attack) * park_factor

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

    return (h_wins / num_sims) * 100, (a_wins / num_sims) * 100, Counter(scores).most_common(1)[0][0], h_eff_era, a_eff_era, park_factor

st.write("🔄 메이저리그 30개 구단 데이터베이스 동기화 중...")

try:
    df_hitter, df_pitcher, team_bp_era_dict = load_mlb_all_data()
    momentum_dict = load_team_momentum()
    
    st.success("✅ V13.0 완료! (타자/투수 세부 스탯 리더보드 대규모 확장)")
    
    selected_date = st.date_input("🗓️ 분석 날짜를 선택하세요:", date.today())
    df_schedule = load_schedule(selected_date)
    
    tab1, tab2, tab3 = st.tabs(["📅 매치업 및 실시간 라인업", "投 전체 투수 스탯", "🏃‍♂️ 전체 타자 스탯"])
    
    with tab1:
        if not df_schedule.empty:
            html_table = "<table style='width:100%; border-collapse: collapse; margin-bottom: 20px; text-align: center; font-size: 15px;'>"
            html_table += "<tr style='background-color: #262730; color: white; border-bottom: 2px solid #555;'><th style='padding: 12px;'>경기시간(KST)</th><th style='padding: 12px;'>상태</th><th style='padding: 12px; text-align: left;'>홈 팀</th><th style='padding: 12px;'>홈 선발투수</th><th style='padding: 12px; text-align: left;'>어웨이 팀 (원정)</th><th style='padding: 12px;'>어웨이 선발투수</th></tr>"
            for _, row in df_schedule.iterrows():
                html_table += f"<tr style='border-bottom: 1px solid #333;'><td style='padding: 10px;'>{row['경기시간(KST)']}</td><td style='padding: 10px;'>{row['상태']}</td><td style='padding: 10px; text-align: left;'>{row['홈표시']}</td><td style='padding: 10px;'>{row['홈 선발투수']}</td><td style='padding: 10px; text-align: left;'>{row['원정표시']}</td><td style='padding: 10px;'>{row['어웨이 선발투수']}</td></tr>"
            html_table += "</table>"
            
            st.markdown(html_table, unsafe_allow_html=True)
            
            game_options = df_schedule['홈 팀'] + " (홈) vs " + df_schedule['어웨이 팀 (원정)'] + " (원정)"
            selected_game = st.selectbox("🔮 10,000회 정밀 시뮬레이션을 돌릴 경기를 선택하세요:", game_options)
            
            row = df_schedule[game_options == selected_game].iloc[0]
            h_team, a_team = row['홈 팀'], row['어웨이 팀 (원정)']
            h_id, a_id = row['홈 ID'], row['원정 ID']
            h_p, a_p = row['홈 선발투수'], row['어웨이 선발투수']
            game_pk = row['gamePk']
            
            c1, c2, c3 = st.columns([2, 1, 2])
            with c1:
                st.markdown(f"#### <img src='https://www.mlbstatic.com/team-logos/{h_id}.svg' width='24' style='vertical-align: middle; margin-right: 8px;'> **홈: {h_team}**", unsafe_allow_html=True)
            with c2:
                st.markdown("<h4 style='text-align: center;'>VS</h4>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"#### <img src='https://www.mlbstatic.com/team-logos/{a_id}.svg' width='24' style='vertical-align: middle; margin-right: 8px;'> **원정: {a_team}**", unsafe_allow_html=True)
            
            st.markdown("---")
            
            h_lineup, a_lineup = load_live_lineup(game_pk)
            if h_lineup and a_lineup:
                st.success("✨ 실시간 선발 라인업이 확정되었습니다. (크롬 '한국어로 번역' 기능을 켜시면 이름이 번역됩니다.)")
                col_l1, col_l2 = st.columns(2)
                with col_l1:
                    st.markdown(f"**🏠 {h_team} 선발 라인업**")
                    for i, p in enumerate(h_lineup): 
                        st.write(f"{i+1}. {p['name']} <span style='color:#ffcc00;'>({p['pos']})</span>", unsafe_allow_html=True)
                with col_l2:
                    st.markdown(f"**✈️ {a_team} 선발 라인업**")
                    for i, p in enumerate(a_lineup): 
                        st.write(f"{i+1}. {p['name']} <span style='color:#ffcc00;'>({p['pos']})</span>", unsafe_allow_html=True)
                
                h_names = [p['name'] for p in h_lineup]
                a_names = [p['name'] for p in a_lineup]
                h_ops = df_hitter[df_hitter['이름'].isin(h_names)]['OPS'].mean() or 0.720
                a_ops = df_hitter[df_hitter['이름'].isin(a_names)]['OPS'].mean() or 0.720
            else:
                st.markdown(
                    """
                    <div style='text-align:center; padding: 40px; background-color:#2b2b2b; color:#ffcc00; border-radius:10px; margin: 20px 0; border: 2px dashed #ffcc00;'>
                        <h2 style='margin:0;'>🚨 라인업 준비중 🚨</h2>
                        <p style='margin-top:10px; color:#dddddd; font-size:16px;'>아직 선발 명단이 공식 발표되지 않았습니다.<br>(미국 현지 시간 기준, 경기 시작 2~3시간 전에 포지션과 함께 자동 표기됩니다)</p>
                    </div>
                    """, unsafe_allow_html=True
                )
                h_ops = df_hitter[(df_hitter['팀'] == h_team) & (df_hitter['타수'] > 100)]['OPS'].mean() or 0.720
                a_ops = df_hitter[(df_hitter['팀'] == a_team) & (df_hitter['타수'] > 100)]['OPS'].mean() or 0.720
                
            if st.button("🚀 최종 시뮬레이션 돌리기"):
                my_bar = st.progress(0, text="선발+불펜+타선 화력+구장 가중치 연산 중...")
                for p in range(100):
                    time.sleep(0.01)
                    my_bar.progress(p + 1)
                my_bar.empty()
                
                h_bp = team_bp_era_dict.get(h_team, 4.00)
                a_bp = team_bp_era_dict.get(a_team, 4.00)
                
                h_l10 = momentum_dict.get(h_team, {'rate': 0.5, 'str': '5 W - 5 L'})
                a_l10 = momentum_dict.get(a_team, {'rate': 0.5, 'str': '5 W - 5 L'})
                
                pf = PARK_FACTORS.get(h_team, 1.00)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.error(f"🏠 **{h_team} 전력 분석**")
                    h_s_era = df_pitcher[df_pitcher['이름'] == h_p]['ERA_num'].values[0] if not df_pitcher[df_pitcher['이름'] == h_p].empty else 4.50
                    st.write(f"⚾ 선발투수({h_p}) 방어율: **{h_s_era:.2f}** | 🛡️ 불펜 평균 방어율: **{h_bp:.2f}**")
                    st.write(f"🔥 타선 OPS: **{h_ops:.3f}**")
                    st.write(f"📈 최근 기세(Last 10): **{h_l10['str']}**")
                    
                with col2:
                    st.info(f"✈️ **{a_team} 전력 분석**")
                    a_s_era = df_pitcher[df_pitcher['이름'] == a_p]['ERA_num'].values[0] if not df_pitcher[df_pitcher['이름'] == a_p].empty else 4.50
                    st.write(f"⚾ 선발투수({a_p}) 방어율: **{a_s_era:.2f}** | 🛡️ 불펜 평균 방어율: **{a_bp:.2f}**")
                    st.write(f"🔥 타선 OPS: **{a_ops:.3f}**")
                    st.write(f"📈 최근 기세(Last 10): **{a_l10['str']}**")
            
                st.markdown(f"**🏟️ 구장 환경 변수:** {h_team} 홈구장 (파크 팩터: **{pf}**)")
                
                h_win, a_win, b_score, h_eff, a_eff, _ = run_simulation(h_s_era, a_s_era, h_ops, a_ops, h_bp, a_bp, h_l10['rate'], a_l10['rate'], pf)
                
                st.markdown("---")
                st.subheader("🏆 최종 시뮬레이션 결과 리포트")
                st.success(f"**{h_team} (홈) 승리 확률:** {h_win:.1f}%")
                st.info(f"**{a_team} (원정) 승리 확률:** {a_win:.1f}%")
                st.warning(f"🎯 **가장 많이 나온 스코어 ({h_team} : {a_team}) -** {b_score}")
        else:
            st.info("예정된 경기가 없습니다.")
            
    with tab2:
        st.write("2026 시즌 전체 투수 세부 스탯 (가로 스크롤을 넘겨보세요)")
        st.dataframe(df_pitcher[['이름', '팀', 'ERA', '승', '패', '세이브', '출장', '선발', '이닝', '탈삼진', '볼넷', 'WHIP', '피안타율']], use_container_width=True)
        
    with tab3:
        st.write("2026 시즌 전체 타자 세부 스탯 (가로 스크롤을 넘겨보세요)")
        st.dataframe(df_hitter[['이름', '팀', '타수', '안타', '2루타', '3루타', '홈런', '타점', '득점', '볼넷', '삼진', '도루', '타율', '출루율', '장타율', 'OPS']], use_container_width=True)
        
except Exception as e:
    st.error(f"오류 발생: {e}")
