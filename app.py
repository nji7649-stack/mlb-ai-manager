import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date, timedelta
import random
from collections import Counter
import time

st.set_page_config(page_title="MLB AI 감독 모드", layout="wide")
st.title("⚾ MLB AI 감독 모드 V8.0 (KST 타임라인 엔진)")

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

@st.cache_data(ttl=600)
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
            
            # 💡 추가된 부분: 미국 시간(UTC)을 가져와서 한국 시간(KST, +9시간)으로 변환
            game_time_utc = game.get('gameDate')
            if game_time_utc:
                utc_time = datetime.strptime(game_time_utc, "%Y-%m-%dT%H:%M:%SZ")
                kst_time = utc_time + timedelta(hours=9)
                time_str = kst_time.strftime("%H:%M") # "08:05" 형태로 포맷
            else:
                time_str = "시간 미정"

            games.append({
                '경기시간(KST)': time_str,
                '홈 팀': home_team, '홈 선발투수': home_pitcher, 
                '어웨이 팀 (원정)': away_team, '어웨이 선발투수': away_pitcher
            })
            
    df = pd.DataFrame(games)
    if not df.empty:
        # 💡 추가된 부분: 경기 시간을 기준으로 표를 먼저 정렬합니다.
        df = df.sort_values('경기시간(KST)').reset_index(drop=True)
    return df

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

st.write("🔄 시스템 부팅 중... 투수 및 타자 스탯을 불러옵니다.")

try:
    df_hitter, df_pitcher = load_mlb_all_data()
    
    st.success("✅ V8.0 시스템 준비 완료! (KST 타임라인 장착)")
    
    st.markdown("### 🗓️ 분석 날짜 선택")
    selected_date = st.date_input("미리 분석하고 싶은 경기 날짜를 선택하세요:", date.today())
    df_schedule = load_schedule(selected_date)
    
    tab1, tab2, tab3 = st.tabs(["📅 경기 매치업 및 예측", "投 전체 투수 스탯", "🏃‍♂️ 전체 타자 스탯"])
    
    with tab1:
        st.subheader(f"[{selected_date.strftime('%Y년 %m월 %d일')}] 메이저리그 매치업")
        if not df_schedule.empty:
            
            # 💡 수정된 부분: '경기시간(KST)'을 DataFrame의 인덱스(가장 왼쪽 첫 번째 열)로 설정하여 출력합니다.
            display_df = df_schedule.set_index('경기시간(KST)')
            st.dataframe(display_df[['홈 팀', '홈 선발투수', '어웨이 팀 (원정)', '어웨이 선발투수']], use_container_width=True)
            
            st.markdown("---")
            st.subheader("🔮 10,000회 투타 밸런스 시뮬레이션")
            
            game_options = df_schedule['홈 팀'] + " (홈) vs " + df_schedule['어웨이 팀 (원정)'] + " (원정)"
            selected_game = st.selectbox("분석할 경기를 선택하세요:", game_options)
            
            if st.button("🚀 10,000회 시뮬레이션 돌리기"):
                selected_row = df_schedule[game_options == selected_game].iloc[0]
                home_team = selected_row['홈 팀']
                away_team = selected_row['어웨이 팀 (원정)']
                home_p = selected_row['홈 선발투수']
                away_p = selected_row['어웨이 선발투수']
                game_time = selected_row['경기시간(KST)']
                
                home_hitters = df_hitter[(df_hitter['팀'] == home_team) & (df_hitter['타수'] > 100)]
                away_hitters = df_hitter[(df_hitter['팀'] == away_team) & (df_hitter['타수'] > 100)]
                home_team_ops = home_hitters['OPS'].mean() if not home_hitters.empty else 0.720
                away_team_ops = away_hitters['OPS'].mean() if not away_hitters.empty else 0.720

                progress_text = "투수의 방어율과 타선의 화력을 계산하여 10,000경기를 시뮬레이션 중입니다..."
                my_bar = st.progress(0, text=progress_text)
                for percent_complete in range(100):
                    time.sleep(0.01)
                    my_bar.progress(percent_complete + 1, text=progress_text)
                my_bar.empty()
                
                # 시뮬레이션 돌렸을 때 해당 경기 시작 시간도 함께 안내합니다.
                st.write(f"⏰ **경기 시작 시간:** 한국 시간 {game_time}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.error(f"🏠 **홈:** {home_team} (선발: {home_p})")
                    st.write(f"🔥 팀 핵심 타선 평균 OPS: **{home_team_ops:.3f}**")
                    home_p_data = df_pitcher[df_pitcher['이름'] == home_p]
                    home_era = home_p_data['ERA'].values[0] if not home_p_data.empty else 4.50
                    
                with col2:
                    st.info(f"✈️ **원정:** {away_team} (선발: {away_p})")
                    st.write(f"🔥 팀 핵심 타선 평균 OPS: **{away_team_ops:.3f}**")
                    away_p_data = df_pitcher[df_pitcher['이름'] == away_p]
                    away_era = away_p_data['ERA'].values[0] if not away_p_data.empty else 4.50
                
                home_win, away_win, best_score = run_simulation(home_era, away_era, home_team_ops, away_team_ops)
                
                st.markdown("---")
                st.subheader("🏆 최종 시뮬레이션 결과 리포트 (투타 종합)")
                st.success(f"**{home_team} (홈) 승리 확률:** {home_win:.1f}%")
                st.info(f"**{away_team} (원정) 승리 확률:** {away_win:.1f}%")
                st.warning(f"🎯 **가장 많이 나온 스코어 (홈 : 원정) -** {best_score}")
                
        else:
            st.info(f"{selected_date.strftime('%Y년 %m월 %d일')}에는 예정된 메이저리그 경기가 없습니다.")
            
    with tab2:
        st.write("2026 시즌 전체 투수 스탯입니다.")
        st.dataframe(df_pitcher)
        
    with tab3:
        st.write("2026 시즌 전체 타자 스탯입니다. (홈런 순 정렬 가능)")
        st.dataframe(df_hitter)

except Exception as e:
    st.error(f"오류 발생: {e}")
