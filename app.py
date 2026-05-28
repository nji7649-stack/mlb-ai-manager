import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date, timedelta
import random
from collections import Counter
import time

st.set_page_config(page_title="MLB AI 감독 모드", layout="wide")
st.title("⚾ MLB AI 감독 모드 V10.1 (라인업 버그 수정판)")

@st.cache_data(ttl=3600)
def load_mlb_all_data():
    hitter_url = "https://statsapi.mlb.com/api/v1/stats?stats=season&group=hitting&gameType=R&season=2026&playerPool=ALL&limit=1500"
    h_splits = requests.get(hitter_url).json()['stats'][0]['splits']
    hitter_list = []
    for r in h_splits:
        stat = r['stat']
        hitter_list.append({
            '이름': r['player']['fullName'], '팀': r['team']['name'],
            '타수': stat.get('atBats', 0), '홈런': stat.get('homeRuns', 0),
            '타율': stat.get('avg', '.000'), 'OPS': stat.get('ops', '.000')
        })
    df_h = pd.DataFrame(hitter_list)
    df_h['OPS'] = pd.to_numeric(df_h['OPS'], errors='coerce').fillna(0.0)
    df_h['타수'] = pd.to_numeric(df_h['타수'], errors='coerce').fillna(0)
    
    pitcher_url = "https://statsapi.mlb.com/api/v1/stats?stats=season&group=pitching&gameType=R&season=2026&playerPool=ALL&limit=1500"
    p_splits = requests.get(pitcher_url).json()['stats'][0]['splits']
    pitcher_list = [{'이름': r['player']['fullName'], '팀': r['team']['name'], 'ERA': r['stat'].get('era', '99.99'), '이닝': r['stat'].get('inningsPitched', '0.0')} for r in p_splits]
    df_p = pd.DataFrame(pitcher_list)
    
    return df_h, df_p

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
            home_score = game['teams']['home'].get('score', 0)
            away_score = game['teams']['away'].get('score', 0)
            
            if status == 'Final': status_str = f"✅ 종료 ({home_score}:{away_score})"
            elif status == 'Live': status_str = f"🔥 진행중 ({home_score}:{away_score})"
            else: status_str = "⏳ 경기 예정"

            games.append({
                '경기시간(KST)': time_str,
                '상태/결과': status_str,
                '홈 팀': home_team, '홈 선발투수': home_pitcher, 
                '어웨이 팀 (원정)': away_team, '어웨이 선발투수': away_pitcher,
                'gamePk': game.get('gamePk')
            })
            
    df = pd.DataFrame(games)
    if not df.empty:
        df = df.sort_values('경기시간(KST)').reset_index(drop=True)
    return df

# 💡 '알 수 없음' 에러를 막기 위한 무적의 이름 찾기 로직 적용
@st.cache_data(ttl=60)
def load_live_lineup(game_pk):
    try:
        url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
        res = requests.get(url).json()
        
        home_order = res['teams']['home'].get('battingOrder', [])
        away_order = res['teams']['away'].get('battingOrder', [])
        
        if len(home_order) == 0 or len(away_order) == 0:
            return None, None
            
        home_players = res['teams']['home']['players']
        away_players = res['teams']['away']['players']
        
        # 키(Key) 이름이 어떻게 들어오든 상관없이, 실제 선수 ID로 딕셔너리를 재조립합니다.
        home_lookup = {p['person']['id']: p['person']['fullName'] for k, p in home_players.items() if 'person' in p and 'id' in p['person']}
        away_lookup = {p['person']['id']: p['person']['fullName'] for k, p in away_players.items() if 'person' in p and 'id' in p['person']}
        
        # 재조립된 딕셔너리에서 1~9번 타자의 이름을 정확히 매칭해옵니다.
        home_lineup = [home_lookup.get(pid, '이름 로딩 에러') for pid in home_order]
        away_lineup = [away_lookup.get(pid, '이름 로딩 에러') for pid in away_order]
        
        return home_lineup, away_lineup
    except Exception as e:
        return None, None

def run_simulation(home_era, away_era, home_ops, away_ops, num_sims=10000):
    try: h_era = float(home_era) if float(home_era) < 50 else 4.50
    except: h_era = 4.50
    try: a_era = float(away_era) if float(away_era) < 50 else 4.50
    except: a_era = 4.50

    home_attack_power = home_ops / 0.720 if home_ops > 0 else 1.0
    away_attack_power = away_ops / 0.720 if away_ops > 0 else 1.0

    home_expected_runs = (a_era * home_attack_power) + 0.2
    away_expected_runs = (h_era * away_attack_power)

    home_wins, away_wins = 0, 0
    scores = []

    for _ in range(num_sims):
        home_score = max(0, int(random.gauss(home_expected_runs, 2.5)))
        away_score = max(0, int(random.gauss(away_expected_runs, 2.5)))
        if home_score == away_score:
            if random.random() > 0.5: home_score += 1
            else: away_score += 1
        if home_score > away_score: home_wins += 1
        elif away_score > home_score: away_wins += 1
        scores.append(f"{home_score} : {away_score}")

    return (home_wins / num_sims) * 100, (away_wins / num_sims) * 100, Counter(scores).most_common(1)[0][0]

st.write("🔄 메이저리그 공식 서버와 연결 중...")

try:
    df_hitter, df_pitcher = load_mlb_all_data()
    
    st.success("✅ V10.1 시스템 준비 완료! (라인업 버그 수정 패치 적용)")
    
    st.markdown("### 🗓️ 분석 날짜 선택")
    selected_date = st.date_input("미리 분석하고 싶은 경기 날짜를 선택하세요:", date.today())
    df_schedule = load_schedule(selected_date)
    
    tab1, tab2, tab3 = st.tabs(["📅 매치업 및 실시간 라인업", "投 투수 스탯", "🏃‍♂️ 타자 스탯"])
    
    with tab1:
        st.subheader(f"[{selected_date.strftime('%Y년 %m월 %d일')}] 경기 일정")
        if not df_schedule.empty:
            
            display_df = df_schedule.set_index('경기시간(KST)')
            st.dataframe(display_df[['상태/결과', '홈 팀', '홈 선발투수', '어웨이 팀 (원정)', '어웨이 선발투수']], use_container_width=True)
            
            st.markdown("---")
            st.subheader("📋 실시간 선발 라인업 및 승률 시뮬레이션")
            
            game_options = df_schedule['홈 팀'] + " (홈) vs " + df_schedule['어웨이 팀 (원정)'] + " (원정)"
            selected_game = st.selectbox("분석할 경기를 선택하세요:", game_options)
            
            selected_row = df_schedule[game_options == selected_game].iloc[0]
            home_team, away_team = selected_row['홈 팀'], selected_row['어웨이 팀 (원정)']
            home_p, away_p = selected_row['홈 선발투수'], selected_row['어웨이 선발투수']
            game_time, game_status = selected_row['경기시간(KST)'], selected_row['상태/결과']
            game_pk = selected_row['gamePk']
            
            home_lineup, away_lineup = load_live_lineup(game_pk)
            
            if home_lineup and away_lineup:
                st.success("✨ 선발 라인업이 공식 발표되었습니다! 이 명단을 바탕으로 정밀 시뮬레이션을 진행합니다.")
                col_l1, col_l2 = st.columns(2)
                with col_l1:
                    st.markdown(f"**🏠 {home_team} 선발 타순**")
                    for i, player in enumerate(home_lineup):
                        st.write(f"{i+1}. {player}")
                with col_l2:
                    st.markdown(f"**✈️ {away_team} 선발 타순**")
                    for i, player in enumerate(away_lineup):
                        st.write(f"{i+1}. {player}")
                
                home_hitters = df_hitter[df_hitter['이름'].isin(home_lineup)]
                away_hitters = df_hitter[df_hitter['이름'].isin(away_lineup)]
                home_team_ops = home_hitters['OPS'].mean() if not home_hitters.empty else 0.720
                away_team_ops = away_hitters['OPS'].mean() if not away_hitters.empty else 0.720
                
            else:
                st.markdown(
                    """
                    <div style='text-align:center; padding: 40px; background-color:#2b2b2b; color:#ffcc00; border-radius:10px; margin: 20px 0; border: 2px dashed #ffcc00;'>
                        <h2 style='margin:0;'>🚨 라인업 준비중 🚨</h2>
                        <p style='margin-top:10px; color:#dddddd; font-size:16px;'>아직 선발 명단이 공식 발표되지 않았습니다.<br>(미국 현지 시간 기준, 경기 시작 2~3시간 전에 발표됩니다)</p>
                    </div>
                    """, unsafe_allow_html=True
                )
                
                home_hitters = df_hitter[(df_hitter['팀'] == home_team) & (df_hitter['타수'] > 100)]
                away_hitters = df_hitter[(df_hitter['팀'] == away_team) & (df_hitter['타수'] > 100)]
                home_team_ops = home_hitters['OPS'].mean() if not home_hitters.empty else 0.720
                away_team_ops = away_hitters['OPS'].mean() if not away_hitters.empty else 0.720
            
            st.markdown("---")
            if st.button("🚀 10,000회 시뮬레이션 돌리기"):
                
                progress_text = "전력 데이터를 기반으로 10,000경기를 가상으로 치르는 중입니다..."
                my_bar = st.progress(0, text=progress_text)
                for percent_complete in range(100):
                    time.sleep(0.01)
                    my_bar.progress(percent_complete + 1, text=progress_text)
                my_bar.empty()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.error(f"🏠 **홈:** {home_team} (투수: {home_p})")
                    st.write(f"🔥 타선 평균 OPS: **{home_team_ops:.3f}**")
                    home_p_data = df_pitcher[df_pitcher['이름'] == home_p]
                    home_era = home_p_data['ERA'].values[0] if not home_p_data.empty else 4.50
                    
                with col2:
                    st.info(f"✈️ **원정:** {away_team} (투수: {away_p})")
                    st.write(f"🔥 타선 평균 OPS: **{away_team_ops:.3f}**")
                    away_p_data = df_pitcher[df_pitcher['이름'] == away_p]
                    away_era = away_p_data['ERA'].values[0] if not away_p_data.empty else 4.50
                
                home_win, away_win, best_score = run_simulation(home_era, away_era, home_team_ops, away_team_ops)
                
                st.markdown("---")
                st.subheader("🏆 최종 시뮬레이션 결과 리포트")
                st.success(f"**{home_team} (홈) 승리 확률:** {home_win:.1f}%")
                st.info(f"**{away_team} (원정) 승리 확률:** {away_win:.1f}%")
                st.warning(f"🎯 **가장 많이 나온 스코어 (홈 : 원정) -** {best_score}")
                
        else:
            st.info(f"{selected_date.strftime('%Y년 %m월 %d일')}에는 예정된 메이저리그 경기가 없습니다.")
            
    with tab2:
        st.dataframe(df_pitcher)
        
    with tab3:
        st.dataframe(df_hitter)

except Exception as e:
    st.error(f"오류 발생: {e}")
