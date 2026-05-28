import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import random
from collections import Counter
import time

st.set_page_config(page_title="MLB AI 감독 모드", layout="wide")
st.title("⚾ MLB AI 감독 모드 V5.0 (10,000회 시뮬레이션 엔진)")

@st.cache_data(ttl=3600)
def load_mlb_all_data():
    # 타자 데이터
    hitter_url = "https://statsapi.mlb.com/api/v1/stats?stats=season&group=hitting&gameType=R&season=2026&playerPool=ALL&limit=1500"
    h_splits = requests.get(hitter_url).json()['stats'][0]['splits']
    hitter_list = [{'이름': r['player']['fullName'], '팀': r['team']['name'], 'OPS': r['stat'].get('ops', '.000'), '타율': r['stat'].get('avg', '.000')} for r in h_splits]
    
    # 투수 데이터
    pitcher_url = "https://statsapi.mlb.com/api/v1/stats?stats=season&group=pitching&gameType=R&season=2026&playerPool=ALL&limit=1500"
    p_splits = requests.get(pitcher_url).json()['stats'][0]['splits']
    pitcher_list = [{'이름': r['player']['fullName'], '팀': r['team']['name'], 'ERA': r['stat'].get('era', '99.99'), '이닝': r['stat'].get('inningsPitched', '0.0')} for r in p_splits]
    
    return pd.DataFrame(hitter_list), pd.DataFrame(pitcher_list)

@st.cache_data(ttl=600)
def load_todays_schedule():
    today_str = datetime.now().strftime("%Y-%m-%d")
    schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today_str}&hydrate=probablePitcher"
    res = requests.get(schedule_url).json()
    
    games = []
    if 'dates' in res and len(res['dates']) > 0:
        for game in res['dates'][0]['games']:
            away_team = game['teams']['away']['team']['name']
            home_team = game['teams']['home']['team']['name']
            away_pitcher = game['teams']['away'].get('probablePitcher', {}).get('fullName', '미정(TBD)')
            home_pitcher = game['teams']['home'].get('probablePitcher', {}).get('fullName', '미정(TBD)')
            
            # 딕셔너리 저장 시 홈팀이 먼저 오도록 순서 변경
            games.append({'홈 팀': home_team, '홈 선발투수': home_pitcher, '어웨이 팀 (원정)': away_team, '어웨이 선발투수': away_pitcher})
    return pd.DataFrame(games)

# 10,000회 승률 시뮬레이션 함수
def run_simulation(home_era, away_era, num_sims=10000):
    try: h_era = float(home_era) if float(home_era) < 50 else 4.50
    except: h_era = 4.50
        
    try: a_era = float(away_era) if float(away_era) < 50 else 4.50
    except: a_era = 4.50

    home_wins, away_wins, draws = 0, 0, 0
    scores = []

    # 홈팀 예상 득점 = 상대 투수 방어율 + 홈 어드밴티지(0.2)
    home_expected_runs = a_era + 0.2
    # 원정팀 예상 득점 = 상대 투수 방어율
    away_expected_runs = h_era

    for _ in range(num_sims):
        # 가우스 분포(정규분포)를 이용해 득점 확률 시뮬레이션
        home_score = max(0, int(random.gauss(home_expected_runs, 2.5)))
        away_score = max(0, int(random.gauss(away_expected_runs, 2.5)))

        # 무승부 시 연장전 가정하여 랜덤하게 1점 추가
        if home_score == away_score:
            if random.random() > 0.5: home_score += 1
            else: away_score += 1

        if home_score > away_score: home_wins += 1
        elif away_score > home_score: away_wins += 1

        scores.append(f"{home_score} : {away_score}")

    home_win_rate = (home_wins / num_sims) * 100
    away_win_rate = (away_wins / num_sims) * 100
    most_common_score = Counter(scores).most_common(1)[0][0]

    return home_win_rate, away_win_rate, most_common_score

st.write("🔄 시스템 부팅 중... 선수 스탯 및 오늘의 매치업을 불러옵니다.")

try:
    df_hitter, df_pitcher = load_mlb_all_data()
    df_schedule = load_todays_schedule()
    
    st.success("✅ V5.0 시스템 준비 완료! (시뮬레이션 엔진 장착)")
    
    tab1, tab2 = st.tabs(["📅 경기 매치업 및 예측", "📊 전체 선수 스탯 확인"])
    
    with tab1:
        st.subheader("오늘의 메이저리그 경기 일정")
        if not df_schedule.empty:
            # 표 컬럼 순서를 [홈 -> 원정]으로 명시적 고정
            st.dataframe(df_schedule[['홈 팀', '홈 선발투수', '어웨이 팀 (원정)', '어웨이 선발투수']], use_container_width=True)
            
            st.markdown("---")
            st.subheader("🔮 10,000회 AI 시뮬레이션")
            
            # 드롭다운 선택창도 홈팀이 먼저 나오게 수정
            game_options = df_schedule['홈 팀'] + " (홈) vs " + df_schedule['어웨이 팀 (원정)'] + " (원정)"
            selected_game = st.selectbox("분석할 경기를 선택하세요:", game_options)
            
            if st.button("🚀 10,000회 시뮬레이션 돌리기"):
                game_idx = game_options[game_options == selected_game].index[0]
                home_team = df_schedule.iloc[game_idx]['홈 팀']
                away_team = df_schedule.iloc[game_idx]['어웨이 팀 (원정)']
                home_p = df_schedule.iloc[game_idx]['홈 선발투수']
                away_p = df_schedule.iloc[game_idx]['어웨이 선발투수']
                
                # 멋진 로딩 바 효과
                progress_text = "AI가 10,000번의 가상 경기를 치르고 있습니다..."
                my_bar = st.progress(0, text=progress_text)
                for percent_complete in range(100):
                    time.sleep(0.01)
                    my_bar.progress(percent_complete + 1, text=progress_text)
                time.sleep(0.3)
                my_bar.empty()
                
                # 좌측 홈, 우측 원정으로 레이아웃 완벽 교체
                col1, col2 = st.columns(2)
                with col1:
                    st.error(f"🏠 **홈:** {home_team} ({home_p})")
                    home_p_data = df_pitcher[df_pitcher['이름'] == home_p]
                    st.dataframe(home_p_data)
                    home_era = home_p_data['ERA'].values[0] if not home_p_data.empty else 4.50
                    
                with col2:
                    st.info(f"✈️ **원정:** {away_team} ({away_p})")
                    away_p_data = df_pitcher[df_pitcher['이름'] == away_p]
                    st.dataframe(away_p_data)
                    away_era = away_p_data['ERA'].values[0] if not away_p_data.empty else 4.50
                
                # 시뮬레이션 결과 화면 출력
                home_win, away_win, best_score = run_simulation(home_era, away_era)
                
                st.markdown("---")
                st.subheader("🏆 최종 시뮬레이션 결과 리포트")
                st.success(f"**{home_team} (홈) 승리 확률:** {home_win:.1f}%")
                st.info(f"**{away_team} (원정) 승리 확률:** {away_win:.1f}%")
                st.warning(f"🎯 **가장 많이 나온 스코어 (홈 : 원정) -** {best_score}")
                
        else:
            st.info("오늘 예정된 경기가 없습니다.")
            
    with tab2:
        st.write("프로그램이 백그라운드에 저장해둔 전체 투수 스탯입니다.")
        st.dataframe(df_pitcher)

except Exception as e:
    st.error(f"오류 발생: {e}")
