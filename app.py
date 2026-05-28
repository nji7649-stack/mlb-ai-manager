import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date
import random
from collections import Counter
import time

st.set_page_config(page_title="MLB AI 감독 모드", layout="wide")
st.title("⚾ MLB AI 감독 모드 V6.0 (타임머신 분석기)")

@st.cache_data(ttl=3600)
def load_mlb_all_data():
    hitter_url = "https://statsapi.mlb.com/api/v1/stats?stats=season&group=hitting&gameType=R&season=2026&playerPool=ALL&limit=1500"
    h_splits = requests.get(hitter_url).json()['stats'][0]['splits']
    hitter_list = [{'이름': r['player']['fullName'], '팀': r['team']['name'], 'OPS': r['stat'].get('ops', '.000'), '타율': r['stat'].get('avg', '.000')} for r in h_splits]
    
    pitcher_url = "https://statsapi.mlb.com/api/v1/stats?stats=season&group=pitching&gameType=R&season=2026&playerPool=ALL&limit=1500"
    p_splits = requests.get(pitcher_url).json()['stats'][0]['splits']
    pitcher_list = [{'이름': r['player']['fullName'], '팀': r['team']['name'], 'ERA': r['stat'].get('era', '99.99'), '이닝': r['stat'].get('inningsPitched', '0.0')} for r in p_splits]
    
    return pd.DataFrame(hitter_list), pd.DataFrame(pitcher_list)

# 💡 수정된 부분: 이제 '오늘'이 아니라 '선택한 날짜(target_date)'를 서버에 요청합니다.
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
            
            games.append({'홈 팀': home_team, '홈 선발투수': home_pitcher, '어웨이 팀 (원정)': away_team, '어웨이 선발투수': away_pitcher})
    return pd.DataFrame(games)

def run_simulation(home_era, away_era, num_sims=10000):
    try: h_era = float(home_era) if float(home_era) < 50 else 4.50
    except: h_era = 4.50
    try: a_era = float(away_era) if float(away_era) < 50 else 4.50
    except: a_era = 4.50

    home_wins, away_wins, draws = 0, 0, 0
    scores = []
    home_expected_runs = a_era + 0.2
    away_expected_runs = h_era

    for _ in range(num_sims):
        home_score = max(0, int(random.gauss(home_expected_runs, 2.5)))
        away_score = max(0, int(random.gauss(away_expected_runs, 2.5)))
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

st.write("🔄 시스템 부팅 중... 선수 스탯을 불러옵니다.")

try:
    df_hitter, df_pitcher = load_mlb_all_data()
    
    st.success("✅ V6.0 시스템 준비 완료! (캘린더 연동)")
    
    # 💡 새로 추가된 부분: 화면 최상단에 날짜를 고를 수 있는 달력을 띄웁니다.
    st.markdown("### 🗓️ 분석 날짜 선택")
    selected_date = st.date_input("미리 분석하고 싶은 경기 날짜를 선택하세요:", date.today())
    
    # 선택한 날짜를 바탕으로 스케줄을 불러옵니다.
    df_schedule = load_schedule(selected_date)
    
    tab1, tab2 = st.tabs(["📅 경기 매치업 및 예측", "📊 전체 선수 스탯 확인"])
    
    with tab1:
        st.subheader(f"[{selected_date.strftime('%Y년 %m월 %d일')}] 메이저리그 매치업")
        if not df_schedule.empty:
            st.dataframe(df_schedule[['홈 팀', '홈 선발투수', '어웨이 팀 (원정)', '어웨이 선발투수']], use_container_width=True)
            
            st.markdown("---")
            st.subheader("🔮 10,000회 AI 시뮬레이션")
            
            game_options = df_schedule['홈 팀'] + " (홈) vs " + df_schedule['어웨이 팀 (원정)'] + " (원정)"
            selected_game = st.selectbox("분석할 경기를 선택하세요:", game_options)
            
            if st.button("🚀 10,000회 시뮬레이션 돌리기"):
                game_idx = game_options[game_options == selected_game].index[0]
                home_team = df_schedule.iloc[game_idx]['홈 팀']
                away_team = df_schedule.iloc[game_idx]['어웨이 팀 (원정)']
                home_p = df_schedule.iloc[game_idx]['홈 선발투수']
                away_p = df_schedule.iloc[game_idx]['어웨이 선발투수']
                
                progress_text = "AI가 10,000번의 가상 경기를 치르고 있습니다..."
                my_bar = st.progress(0, text=progress_text)
                for percent_complete in range(100):
                    time.sleep(0.01)
                    my_bar.progress(percent_complete + 1, text=progress_text)
                time.sleep(0.3)
                my_bar.empty()
                
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
                
                # 아직 선발 투수 발표가 안 난 경기(미정)에 대한 경고문
                if home_p == '미정(TBD)' or away_p == '미정(TBD)':
                    st.warning("⚠️ 아직 선발 투수가 공식 발표되지 않은 팀이 포함되어 있습니다! (기본 방어율 4.50으로 임시 계산됩니다)")
                
                home_win, away_win, best_score = run_simulation(home_era, away_era)
                
                st.markdown("---")
                st.subheader("🏆 최종 시뮬레이션 결과 리포트")
                st.success(f"**{home_team} (홈) 승리 확률:** {home_win:.1f}%")
                st.info(f"**{away_team} (원정) 승리 확률:** {away_win:.1f}%")
                st.warning(f"🎯 **가장 많이 나온 스코어 (홈 : 원정) -** {best_score}")
                
        else:
            st.info(f"{selected_date.strftime('%Y년 %m월 %d일')}에는 예정된 메이저리그 경기가 없습니다.")
            
    with tab2:
        st.write("프로그램이 백그라운드에 저장해둔 전체 투수 스탯입니다.")
        st.dataframe(df_pitcher)

except Exception as e:
    st.error(f"오류 발생: {e}")
