import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="MLB AI 감독 모드", layout="wide")
st.title("⚾ MLB AI 감독 모드 V4.0 (매치업 분석기)")

@st.cache_data(ttl=3600)
def load_mlb_all_data():
    # 타자 데이터 수집
    hitter_url = "https://statsapi.mlb.com/api/v1/stats?stats=season&group=hitting&gameType=R&season=2026&playerPool=ALL&limit=1500"
    h_splits = requests.get(hitter_url).json()['stats'][0]['splits']
    hitter_list = [{'이름': r['player']['fullName'], '팀': r['team']['name'], 'OPS': r['stat'].get('ops', '.000'), '타율': r['stat'].get('avg', '.000')} for r in h_splits]
    
    # 투수 데이터 수집
    pitcher_url = "https://statsapi.mlb.com/api/v1/stats?stats=season&group=pitching&gameType=R&season=2026&playerPool=ALL&limit=1500"
    p_splits = requests.get(pitcher_url).json()['stats'][0]['splits']
    pitcher_list = [{'이름': r['player']['fullName'], '팀': r['team']['name'], 'ERA': r['stat'].get('era', '99.99'), '이닝': r['stat'].get('inningsPitched', '0.0')} for r in p_splits]
    
    return pd.DataFrame(hitter_list), pd.DataFrame(pitcher_list)

@st.cache_data(ttl=600)
def load_todays_schedule():
    # 미국 시간 기준 날짜 설정
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
            games.append({'어웨이 팀 (원정)': away_team, '어웨이 선발투수': away_pitcher, '홈 팀': home_team, '홈 선발투수': home_pitcher})
    return pd.DataFrame(games)

st.write("🔄 시스템 부팅 중... 선수 스탯 및 오늘의 매치업을 불러옵니다.")

try:
    df_hitter, df_pitcher = load_mlb_all_data()
    df_schedule = load_todays_schedule()
    
    st.success("✅ V4.0 시스템 준비 완료!")
    
    # 탭을 나눠서 일정표와 데이터베이스를 모두 볼 수 있게 수정
    tab1, tab2 = st.tabs(["📅 경기 매치업 분석", "📊 전체 선수 스탯 확인"])
    
    with tab1:
        st.subheader("오늘의 메이저리그 경기 일정")
        if not df_schedule.empty:
            st.dataframe(df_schedule, use_container_width=True)
            
            st.markdown("---")
            st.subheader("🔮 매치업 전력 비교")
            
            # 드롭다운으로 분석할 경기 선택
            game_options = df_schedule['어웨이 팀 (원정)'] + " vs " + df_schedule['홈 팀']
            selected_game = st.selectbox("분석할 경기를 선택하세요:", game_options)
            
            if st.button("해당 경기 선발투수 전력 비교하기"):
                game_idx = game_options[game_options == selected_game].index[0]
                away_p = df_schedule.iloc[game_idx]['어웨이 선발투수']
                home_p = df_schedule.iloc[game_idx]['홈 선발투수']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"✈️ **원정:** {away_p}")
                    st.dataframe(df_pitcher[df_pitcher['이름'] == away_p])
                with col2:
                    st.error(f"🏠 **홈:** {home_p}")
                    st.dataframe(df_pitcher[df_pitcher['이름'] == home_p])
        else:
            st.info("오늘 예정된 경기가 없습니다.")
            
    with tab2:
        st.write("프로그램이 백그라운드에 저장해둔 전체 투수 스탯입니다.")
        st.dataframe(df_pitcher)

except Exception as e:
    st.error(f"오류 발생: {e}")
