import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date, timedelta
import random
from collections import Counter
import time

st.set_page_config(page_title="MLB AI 감독 모드", layout="wide")
st.title("⚾ MLB AI 감독 모드 V12.8 (수제 한글 사전 업데이트)")

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

TEAM_TRANSLATIONS = {
    'Arizona Diamondbacks': '애리조나 다이아몬드백스', 'Atlanta Braves': '애틀랜타 브레이브스',
    'Baltimore Orioles': '볼티모어 오리올스', 'Boston Red Sox': '보스턴 레드삭스',
    'Chicago Cubs': '시카고 컵스', 'Chicago White Sox': '시카고 화이트삭스',
    'Cincinnati Reds': '신시내티 레즈', 'Cleveland Guardians': '클리블랜드 가디언스',
    'Colorado Rockies': '콜로라도 로키스', 'Detroit Tigers': '디트로이트 타이거스',
    'Houston Astros': '휴스턴 애스트로스', 'Kansas City Royals': '캔자스시티 로열스',
    'Los Angeles Angels': '로스앤젤레스 에인절스', 'Los Angeles Dodgers': '로스앤젤레스 다저스',
    'Miami Marlins': '마이애미 말린스', 'Milwaukee Brewers': '밀워키 브루어스',
    'Minnesota Twins': '미네소타 트윈스', 'New York Mets': '뉴욕 메츠',
    'New York Yankees': '뉴욕 양키스', 'Athletics': '오클랜드 애슬레틱스',
    'Oakland Athletics': '오클랜드 애슬레틱스', 'Philadelphia Phillies': '필라델피아 필리스',
    'Pittsburgh Pirates': '피츠버그 파이어리츠', 'San Diego Padres': '샌디에이고 파드리스',
    'San Francisco Giants': '샌프란시스코 자이언츠', 'Seattle Mariners': '시애틀 매리너스',
    'St. Louis Cardinals': '세인트루이스 카디널스', 'Tampa Bay Rays': '탬파베이 레이스',
    'Texas Rangers': '텍사스 레인저스', 'Toronto Blue Jays': '토론토 블루제이스',
    'Washington Nationals': '워싱턴 내셔널스'
}

# 💡 대타(PH), 대주자(PR) 포지션을 추가했습니다.
POSITION_TRANSLATIONS = {
    'P': '투수', 'C': '포수', '1B': '1루수', '2B': '2루수', '3B': '3루수',
    'SS': '유격수', 'LF': '좌익수', 'CF': '중견수', 'RF': '우익수', 'DH': '지명타자',
    'TWP': '투타겸업', 'O': '외야수', 'IF': '내야수', 'B': '야수', 
    'PH': '대타', 'PR': '대주자'
}

# 💡 감독님이 보내주신 스크린샷의 누락 선수들을 사전에 꽉꽉 채워 넣었습니다!
PLAYER_TRANSLATIONS = {
    'Shohei Ohtani': '오타니 쇼헤이', 'Aaron Judge': '애런 저지', 'Mike Trout': '마이크 트라웃',
    'Nathan Eovaldi': '네이선 이오발디', 'Spencer Arrighetti': '스펜서 아리게티',
    'Jack Flaherty': '잭 플래허티', 'Grayson Rodriguez': '그레이슨 로드리게스',
    'Davis Martin': '데이비스 마틴', 'Simeon Woods Richardson': '시메온 우즈 리처드슨',
    'Payton Tolle': '페이튼 톨리', 'Chris Sale': '크리스 세일',
    'Chris Bassitt': '크리스 배싯', 'Patrick Corbin': '패트릭 코빈',
    'Paul Skenes': '폴 스킨스', 'Colin Rea': '콜린 레이', 'Tomoyuki Sugano': '스가노 토모유키',
    'Kyle Schwarber': '카일 슈와버', 'Munetaka Murakami': '무네타카 무라카미',
    'Yordan Alvarez': '요르단 알바레즈', 'Byron Buxton': '바이런 벅스턴',
    'Ben Rice': '벤 라이스', 'Jordan Walker': '조던 워커', 'Matt Olson': '맷 올슨',
    'James Wood': '제임스 우드', 'Christian Walker': '크리스찬 워커',
    'Colt Keith': '콜트 키스', 'Kevin McGonigle': '케빈 맥고니글', 'Dillon Dingler': '딜런 딩러',
    'Riley Greene': '라일리 그린', 'Spencer Torkelson': '스펜서 토켈슨', 'Zach McKinstry': '잭 맥킨스트리',
    'Matt Vierling': '맷 비어링', 'Wenceel Pérez': '웬실 페레즈', 'Jahmai Jones': '자마이 존스',
    'Zach Neto': '잭 네토', 'Vaughn Grissom': '본 그리섬', 'Jorge Soler': '호르헤 솔레어',
    'Jose Siri': '호세 시리', 'Jo Adell': '조 아델', 'Oswald Peraza': '오스왈드 페라자', 
    'Sebastián Rivero': '세바스찬 리베로', 'Donovan Walton': '도노반 월튼',
    'Jake Burger': '제이크 버거', 'Ezequiel Duran': '에세키엘 두란', 'Kyle Higashioka': '카일 히가시오카', 
    'Nicky Lopez': '니키 로페즈', 'Braden Shewmake': '브레이든 슈메이크', 'Zach Dezenzo': '잭 디젠조', 
    'Brice Matthews': '브라이스 매튜스', 'Christian Vázquez': '크리스티안 바스케스', 'Trey Gibson': '트레이 깁슨', 
    'Steven Matz': '스티븐 매츠', 'Casey Mize': '케이시 마이즈', 'José Soriano': '호세 소리아노', 
    'Bubba Chandler': '부바 챈들러', 'Jameson Taillon': '제임슨 타이욘', 'Connelly Early': '코넬리 얼리', 
    'Bryce Elder': '브라이스 엘더', 'Huascar Brazobán': '와스카 브라조반', 'Andrew Abbott': '앤드류 애보트', 
    'David Sandlin': '데이비드 샌들린', 'Connor Prielipp': '코너 프리립', 'Noah Cameron': '노아 카메론', 
    'Gerrit Cole': '게릿 콜', 'Jacob deGrom': '제이콥 디그롬', 'Mike Burrows': '마이크 버로우즈'
}

@st.cache_data(ttl=3600)
def load_mlb_all_data():
    hitter_url = "https://statsapi.mlb.com/api/v1/stats?stats=season&group=hitting&gameType=R&season=2026&playerPool=ALL&limit=1500"
    h_splits = requests.get(hitter_url).json()['stats'][0]['splits']
    hitter_list = [{'이름': r['player']['fullName'], '팀': r['team']['name'], '타수': r['stat'].get('atBats', 0), '홈런': r['stat'].get('homeRuns', 0), '타율': r['stat'].get('avg', '.000'), 'OPS': r['stat'].get('ops', '.000')} for r in h_splits]
    df_h = pd.DataFrame(hitter_list)
    df_h['OPS'] = pd.to_numeric(df_h['OPS'], errors='coerce').fillna(0.0)
    df_h['타수'] = pd.to_numeric(df_h['타수'], errors='coerce').fillna(0)
    
    pitcher_url = "https://statsapi.mlb.com/api/v1/stats?stats=season&group=pitching&gameType=R&season=2026&playerPool=ALL&limit=1500"
    p_splits = requests.get(pitcher_url).json()['stats'][0]['splits']
    pitcher_list = [{'이름': r['player']['fullName'], '팀': r['team']['name'], 'ERA': r['stat'].get('era', '99.99'), '이닝': r['stat'].get('inningsPitched', '0.0'), '출장': r['stat'].get('gamesPlayed', 0), '선발': r['stat'].get('gamesStarted', 0)} for r in p_splits]
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
                    l10_str = f"{split['wins']}승 {split['losses']}패"
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
            away_pitcher = game['teams']['away'].get('probablePitcher', {}).get('fullName', '미정(TBD)')
            home_pitcher = game['teams']['home'].get('probablePitcher', {}).get('fullName', '미정(TBD)')
            
            game_time_utc = game.get('gameDate')
            if game_time_utc:
                utc_time = datetime.strptime(game_time_utc, "%Y-%m-%dT%H:%M:%SZ")
                kst_time = utc_time + timedelta(hours=9)
                time_str = kst_time.strftime("%H:%M")
            else:
                time_str = "시간 미정"
                
            status = game['status']['abstractGameState']
            h_score = game['teams']['home'].get('score', 0)
            a_score = game['teams']['away'].get('score', 0)
            
            if status == 'Final': status_str = f"✅ 종료 ({h_score}:{a_score})"
            elif status == 'Live': status_str = f"🔥 진행중 ({h_score}:{a_score})"
            else: status_str = "⏳ 예정"

            home_ko = TEAM_TRANSLATIONS.get(home_team, home_team)
            away_ko = TEAM_TRANSLATIONS.get(away_team, away_team)
            
            home_p_ko = PLAYER_TRANSLATIONS.get(home_pitcher, home_pitcher)
            away_p_ko = PLAYER_TRANSLATIONS.get(away_pitcher, away_pitcher)

            home_display = f"<img src='https://www.mlbstatic.com/team-logos/{home_id}.svg' width='22' style='vertical-align:middle; margin-right:8px;'> <b>{home_ko}</b>"
            away_display = f"<img src='https://www.mlbstatic.com/team-logos/{away_id}.svg' width='22' style='vertical-align:middle; margin-right:8px;'> <b>{away_ko}</b>"

            games.append({
                '경기시간(KST)': time_str, '상태': status_str,
                '홈 팀': home_team, '홈 ID': home_id, '홈 선발투수': home_pitcher, '홈 선발 한글': home_p_ko, '홈표시': home_display, '홈 한글': home_ko,
                '어웨이 팀 (원정)': away_team, '원정 ID': away_id, '어웨이 선발투수': away_pitcher, '원정 선발 한글': away_p_ko, '원정표시': away_display, '원정 한글': away_ko,
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
                
        home_lineup = [h_lookup.get(pid, {'name': '알수없음', 'pos': '야수'}) for pid in home_order]
        away_lineup = [a_lookup.get(pid, {'name': '알수없음', 'pos': '야수'}) for pid in away_order]
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
    
    st.success("✅ V12.8 완료! (사전 업데이트 - 디트로이트, 에인절스 추가 완료)")
    
    selected_date = st.date_input("🗓️ 분석 날짜를 선택하세요:", date.today())
    df_schedule = load_schedule(selected_date)
    
    tab1, tab2, tab3 = st.tabs(["📅 매치업 및 실시간 라인업", "投 전체 투수 스탯", "🏃‍♂️ 전체 타자 스탯"])
    
    with tab1:
        if not df_schedule.empty:
            html_table = "<table style='width:100%; border-collapse: collapse; margin-bottom: 20px; text-align: center; font-size: 15px;'>"
            html_table += "<tr style='background-color: #262730; color: white; border-bottom: 2px solid #555;'><th style='padding: 12px;'>경기시간(KST)</th><th style='padding: 12px;'>상태</th><th style='padding: 12px; text-align: left;'>홈 팀</th><th style='padding: 12px;'>홈 선발투수</th><th style='padding: 12px; text-align: left;'>어웨이 팀 (원정)</th><th style='padding: 12px;'>어웨이 선발투수</th></tr>"
            for _, row in df_schedule.iterrows():
                html_table += f"<tr style='border-bottom: 1px solid #333;'><td style='padding: 10px;'>{row['경기시간(KST)']}</td><td style='padding: 10px;'>{row['상태']}</td><td style='padding: 10px; text-align: left;'>{row['홈표시']}</td><td style='padding: 10px;'>{row['홈 선발 한글']}</td><td style='padding: 10px; text-align: left;'>{row['원정표시']}</td><td style='padding: 10px;'>{row['원정 선발 한글']}</td></tr>"
            html_table += "</table>"
            
            st.markdown(html_table, unsafe_allow_html=True)
            
            game_options = df_schedule['홈 한글'] + " (홈) vs " + df_schedule['원정 한글'] + " (원정)"
            selected_game = st.selectbox("🔮 10,000회 정밀 시뮬레이션을 돌릴 경기를 선택하세요:", game_options)
            
            row = df_schedule[game_options == selected_game].iloc[0]
            h_team, a_team = row['홈 팀'], row['어웨이 팀 (원정)']
            h_ko, a_ko = row['홈 한글'], row['원정 한글']
            h_id, a_id = row['홈 ID'], row['원정 ID']
            h_p, a_p = row['홈 선발투수'], row['어웨이 선발투수']
            game_pk = row['gamePk']
            
            c1, c2, c3 = st.columns([2, 1, 2])
            with c1:
                st.markdown(f"#### <img src='https://www.mlbstatic.com/team-logos/{h_id}.svg' width='24' style='vertical-align: middle; margin-right: 8px;'> **홈: {h_ko}**", unsafe_allow_html=True)
            with c2:
                st.markdown("<h4 style='text-align: center;'>VS</h4>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"#### <img src='https://www.mlbstatic.com/team-logos/{a_id}.svg' width='24' style='vertical-align: middle; margin-right: 8px;'> **원정: {a_ko}**", unsafe_allow_html=True)
            
            st.markdown("---")
            
            h_lineup, a_lineup = load_live_lineup(game_pk)
            if h_lineup and a_lineup:
                st.success("✨ 실시간 선발 라인업이 확정되었습니다. 포지션별 데이터를 매칭합니다.")
                col_l1, col_l2 = st.columns(2)
                with col_l1:
                    st.markdown(f"**🏠 {h_ko} 선발 라인업**")
                    for i, p in enumerate(h_lineup): 
                        p_ko = PLAYER_TRANSLATIONS.get(p['name'], p['name'])
                        st.write(f"{i+1}. {p_ko} <span style='color:#ffcc00;'>({p['pos']})</span>", unsafe_allow_html=True)
                with col_l2:
                    st.markdown(f"**✈️ {a_ko} 선발 라인업**")
                    for i, p in enumerate(a_lineup): 
                        p_ko = PLAYER_TRANSLATIONS.get(p['name'], p['name'])
                        st.write(f"{i+1}. {p_ko} <span style='color:#ffcc00;'>({p['pos']})</span>", unsafe_allow_html=True)
                
                h_names = [p['name'] for p in h_lineup]
                a_names = [p['name'] for p in a_lineup]
                h_ops = df_hitter[df_hitter['이름'].isin(h_names)]['OPS'].mean() or 0.720
                a_ops = df_hitter[df_hitter['이름'].isin(a_names)]['OPS'].mean() or 0.720
            else:
                st.markdown(
                    """
                    <div style='text-align:center; padding: 40px; background-color:#2b2b2b; color:#ffcc00; border-radius:10px; margin: 20px 0; border: 2px dashed #ffcc00;'>
                        <h2 style='margin:0;'>🚨 라인업 준비중 🚨</h2>
                        <p style='margin-top:10px; color:#dddddd; font-size:16px;'>아직 선발 명단이 공식 발표되지 않았습니다.<br>(미국 현지 시간 기준, 경기 시작 2~3시간 전에 포지션과 함께 한글로 자동 변환됩니다)</p>
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
                
                h_l10 = momentum_dict.get(h_team, {'rate': 0.5, 'str': '5승 5패'})
                a_l10 = momentum_dict.get(a_team, {'rate': 0.5, 'str': '5승 5패'})
                
                pf = PARK_FACTORS.get(h_team, 1.00)
                
                h_p_ko = PLAYER_TRANSLATIONS.get(h_p, h_p)
                a_p_ko = PLAYER_TRANSLATIONS.get(a_p, a_p)

                col1, col2 = st.columns(2)
                with col1:
                    st.error(f"🏠 **{h_ko} 전력 분석**")
                    h_s_era = df_pitcher[df_pitcher['이름'] == h_p]['ERA_num'].values[0] if not df_pitcher[df_pitcher['이름'] == h_p].empty else 4.50
                    st.write(f"⚾ 선발투수({h_p_ko}) 방어율: **{h_s_era:.2f}** | 🛡️ 불펜 평균 방어율: **{h_bp:.2f}**")
                    st.write(f"🔥 타선 OPS: **{h_ops:.3f}**")
                    st.write(f"📈 최근 기세(Last 10): **{h_l10['str']}**")
                    
                with col2:
                    st.info(f"✈️ **{a_ko} 전력 분석**")
                    a_s_era = df_pitcher[df_pitcher['이름'] == a_p]['ERA_num'].values[0] if not df_pitcher[df_pitcher['이름'] == a_p].empty else 4.50
                    st.write(f"⚾ 선발투수({a_p_ko}) 방어율: **{a_s_era:.2f}** | 🛡️ 불펜 평균 방어율: **{a_bp:.2f}**")
                    st.write(f"🔥 타선 OPS: **{a_ops:.3f}**")
                    st.write(f"📈 최근 기세(Last 10): **{a_l10['str']}**")
            
                st.markdown(f"**🏟️ 구장 환경 변수:** {h_ko} 홈구장 (파크 팩터: **{pf}**)")
                
                h_win, a_win, b_score, h_eff, a_eff, _ = run_simulation(h_s_era, a_s_era, h_ops, a_ops, h_bp, a_bp, h_l10['rate'], a_l10['rate'], pf)
                
                st.markdown("---")
                st.subheader("🏆 최종 시뮬레이션 결과 리포트")
                st.success(f"**{h_ko} (홈) 승리 확률:** {h_win:.1f}%")
                st.info(f"**{a_ko} (원정) 승리 확률:** {a_win:.1f}%")
                st.warning(f"🎯 **가장 많이 나온 스코어 ({h_ko} : {a_ko}) -** {b_score}")
        else:
            st.info("예정된 경기가 없습니다.")
            
    with tab2:
        st.write("2026 시즌 전체 투수 데이터 리더보드")
        display_pitcher = df_pitcher.copy()
        display_pitcher['팀'] = display_pitcher['팀'].map(TEAM_TRANSLATIONS).fillna(display_pitcher['팀'])
        display_pitcher['이름'] = display_pitcher['이름'].map(PLAYER_TRANSLATIONS).fillna(display_pitcher['이름'])
        st.dataframe(display_pitcher[['이름', '팀', 'ERA', '이닝', '출장', '선발']], use_container_width=True)
        
    with tab3:
        st.write("2026 시즌 전체 타자 데이터 리더보드")
        display_hitter = df_hitter.copy()
        display_hitter['팀'] = display_hitter['팀'].map(TEAM_TRANSLATIONS).fillna(display_hitter['팀'])
        display_hitter['이름'] = display_hitter['이름'].map(PLAYER_TRANSLATIONS).fillna(display_hitter['이름'])
        st.dataframe(display_hitter[['이름', '팀', '타수', '홈런', '타율', 'OPS']], use_container_width=True)
        
except Exception as e:
    st.error(f"오류 발생: {e}")
