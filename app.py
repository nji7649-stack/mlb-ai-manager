import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date, timedelta
import random
from collections import Counter
import time

st.set_page_config(page_title="MLB AI 감독 모드", layout="wide")
st.title("⚾ MLB AI 감독 모드 V11.0 (투타+불펜 완전체 엔진)")

@st.cache_data(ttl=3600)
def load_mlb_all_data():
    # 1. 타자 데이터
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
    
    # 2. 투수 데이터 (출장, 선발 경기 수 추가)
    pitcher_url = "https://statsapi.mlb.com/api/v1/stats?stats=season&group=pitching&gameType=R&season=2026&playerPool=ALL&limit=1500"
    p_splits = requests.get(pitcher_url).json()['stats'][0]['splits']
    pitcher_list = [{'이름': r['player']['fullName'], '팀': r['team']['name'], 'ERA': r['stat'].get('era', '99.99'), '이닝': r['stat'].get('inningsPitched', '0.0'), '출장': r['stat'].get('gamesPlayed', 0), '선발': r['stat'].get('gamesStarted', 0)} for r in p_splits]
    df_p = pd.DataFrame(pitcher_list)
    
    df_p['ERA_num'] = pd.to_numeric(df_p['ERA'], errors='coerce').fillna(4.50)
    df_p['이닝_num'] = pd.to_numeric(df_p['이닝'], errors='coerce').fillna(0.0)
    
    # 💡 팀별 불펜 방어율 사전 계산: (출장이 선발보다 많고, 5이닝 이상 던진 전문 구원투수들)
    df_bullpen = df_p[(df_p['출장'] > df_p['선발']) & (df_p['이닝_num'] >= 5.0)]
    team_bullpen_era = df_bullpen.groupby('팀')['ERA_num'].mean().to_dict()
    
    return df_h, df_p, team_bullpen_era

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
        
        home_lookup = {p['person']['id']: p['person']['fullName'] for k, p in home_players.items() if 'person' in p and 'id' in p['person']}
        away_lookup = {p['person']['id']: p['person']['fullName'] for k, p in away_players.items() if 'person' in p and 'id' in p['person']}
        
        home_lineup = [home_lookup.get(pid, '이름 로딩 에러') for pid in home_order]
        away_lineup = [away_lookup.get(pid, '이름 로딩 에러') for pid in away_order]
        
        return home_lineup, away_lineup
    except Exception as e:
        return None, None

# 💡 선발투수 방어율과 불펜 방어율을 모두 받는 강력한 시뮬레이션 엔진
def run_simulation(home_starter_era, away_starter_era, home_ops, away_ops, home_bp_era, away_bp_era, num_sims=10000):
    try: h_s_era = float(home_starter_era) if float(home_starter_era) < 50 else 4.50
    except: h_s_era = 4.50
    try: a_s_era = float(away_starter_era) if float(away_starter_era) < 50 else 4.50
    except: a_s_era = 4.50

    # 💡 투수진 통합 방어율 (선발 60% + 불펜 40% 비중)
    home_effective_era = (h_s_era * 0.6) + (home_bp_era * 0.4)
    away_effective_era = (a_s_era * 0.6) + (away_bp_era * 0.4)

    home_attack_power = home_ops / 0.720 if home_ops > 0 else 1.0
    away_attack_power = away_ops / 0.720 if away_ops > 0 else 1.0

    # 득점 확률 계산에 '통합 방어율(Effective ERA)' 적용
    home_expected_runs = (away_effective_era * home_attack_power) + 0.2
    away_expected_runs = (home_effective_era * away_attack_power)

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

    return (home_wins / num_sims) * 100, (away_wins / num_sims) * 100, Counter(scores).most_common(1)[0][0], home_effective_era, away_effective_era

st.write("🔄 메이저리그 공식 서버와 연결 중...")

try:
    df_hitter, df_pitcher, team_bp_era_dict = load_mlb_all_data()
    
    st.success("✅ V11.0 시스템 준비 완료! (불펜 통합 전력 분석 엔진 탑재)")
    
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
                
                progress_text = "선발, 불펜, 타선의 화력을 종합하여 10,000경기를 시뮬레이션 중입니다..."
                my_bar = st.progress(0, text=progress_text)
                for percent_complete in range(100):
                    time.sleep(0.01)
                    my_bar.progress(percent_complete + 1, text=progress_text)
                my_bar.empty()
                
                # 팀 불펜 방어율 추출 (없으면 기본값 4.00)
                home_bp = team_bp_era_dict.get(home_team, 4.00)
                away_bp = team_bp_era_dict.get(away_team, 4.00)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.error(f"🏠 **홈:** {home_team}")
                    home_p_data = df_pitcher[df_pitcher['이름'] == home_p]
                    home_s_era = home_p_data['ERA_num'].values[0] if not home_p_data.empty else 4.50
                    st.write(f"⚾ 선발 투수({home_p}) 방어율: **{home_s_era:.2f}**")
                    st.write(f"🛡️ 팀 불펜 평균 방어율: **{home_bp:.2f}**")
                    st.write(f"🔥 타선 평균 OPS: **{home_team_ops:.3f}**")
                    
                with col2:
                    st.info(f"✈️ **원정:** {away_team}")
                    away_p_data = df_pitcher[df_pitcher['이름'] == away_p]
                    away_s_era = away_p_data['ERA_num'].values[0] if not away_p_data.empty else 4.50
                    st.write(f"⚾ 선발 투수({away_p}) 방어율: **{away_s_era:.2f}**")
                    st.write(f"🛡️ 팀 불펜 평균 방어율: **{away_bp:.2f}**")
                    st.write(f"🔥 타선 평균 OPS: **{away_team_ops:.3f}**")
                
                home_win, away_win, best_score, h_eff_era, a_eff_era = run_simulation(home_s_era, away_s_era, home_team_ops, away_team_ops, home_bp, away_bp)
                
                st.markdown("---")
                st.subheader("🏆 최종 시뮬레이션 결과 리포트")
                st.markdown(f"**[홈 투수진 통합 방어율: {h_eff_era:.2f}]** vs **[원정 투수진 통합 방어율: {a_eff_era:.2f}]**")
                st.success(f"**{home_team} (홈) 승리 확률:** {home_win:.1f}%")
                st.info(f"**{away_team} (원정) 승리 확률:** {away_win:.1f}%")
                st.warning(f"🎯 **가장 많이 나온 스코어 (홈 : 원정) -** {best_score}")
                
        else:
            st.info(f"{selected_date.strftime('%Y년 %m월 %d일')}에는 예정된 메이저리그 경기가 없습니다.")
            
    with tab2:
        st.dataframe(df_pitcher[['이름', '팀', 'ERA', '이닝', '출장', '선발']])
        
    with tab3:
        st.dataframe(df_hitter[['이름', '팀', '타수', '홈런', '타율', 'OPS']])

except Exception as e:
    st.error(f"오류 발생: {e}")
