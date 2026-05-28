import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="MLB AI 감독 모드", layout="wide")
st.title("⚾ MLB AI 감독 모드 V3.0 (자동 매치업 엔진)")

# 1. 타자/투수 전체 스탯 불러오기 (V2.0과 동일)
@st.cache_data(ttl=3600)
def load_mlb_all_data():
    # 타자 데이터 수집
    hitter_url = "https://statsapi.mlb.com/api/v1/stats?stats=season&group=hitting&gameType=R&season=2026&playerPool=ALL&limit=1500"
    h_splits = requests.get(hitter_url).json()['stats'][0]['splits']
    
    hitter_list = []
    for row in h_splits:
        s = row['stat']
        hitter_list.append({
            '이름': row['player']['fullName'], '팀': row['team']['name'],
            'OPS': s.get('ops', '.000'), '타율': s.get('avg', '.000')
        })
        
    # 투수 데이터 수집
    pitcher_url = "https://statsapi.mlb.com/api/v1/stats?stats=season&group=pitching&gameType=R&season=2026&playerPool=ALL&limit=1500"
    p_splits = requests.get(pitcher_url).json()['stats'][0]['splits']
    
    pitcher_list = []
    for row in p_splits:
        s = row['stat']
        pitcher_list.append({
            '이름': row['player']['fullName'], '팀': row['team']['name'],
            'ERA': s.get('era', '99.99'), '이닝': s.get('inningsPitched', '0.0')
        })
        
    return pd.DataFrame(hitter_list), pd.DataFrame(pitcher_list)

# 2. 오늘의 MLB 경기 일정과 선발투수 불러오기 (새로 추가됨!)
@st.cache_data(ttl=600)
def load_todays_schedule():
    # 오늘 날짜 구하기
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # schedule API에 hydrate=probablePitcher를 넣어서 선발투수까지 한 번에 가져옴
    schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today_str}&hydrate=probablePitcher"
    res = requests.get(schedule_url).json()
    
    games = []
    if 'dates' in res and len(res['dates']) > 0:
        for game in res['dates'][0]['games']:
            away_team = game['teams']['away']['team']['name']
            home_team = game['teams']['home']['team']['name']
            
            # 선발 투수 정보가 있으면 가져오고, 아직 미정이면 '미정(TBD)'으로 표시
            away_pitcher = game['teams']['away'].get('probablePitcher', {}).get('fullName', '미정(TBD)')
            home_pitcher = game['teams']['home'].get('probablePitcher', {}).get('fullName', '미정(TBD)')
            
            games.append({
                '어웨이 팀 (원정)': away_team,
                '어웨이 선발투수': away_pitcher,
                '홈 팀': home_team,
                '홈 선발투수': home_pitcher
            })
            
    return pd.DataFrame(games)

st.write("🔄 시스템 부팅 중... 선수 스탯 및 오늘의 매치업을 불러옵니다.")

try:
    df_hitter, df_pitcher = load_mlb_all_data()
    df_schedule = load_todays_schedule()
    
    st.success("✅ V3.0 시스템 준비 완료!")
    
    # 오늘의 매치업 화면 표시
    st.subheader(f"📅 오늘({datetime.now().strftime('%m월 %d일')})의 MLB 매치업")
    if not df_schedule.empty:
        st.dataframe(df_schedule, use_container_width=True)
    else:
        st.info("오늘 예정된 메이저리그 경기가 없습니다.")
        
except Exception as e:
    st.error(f"오류 발생: {e}")
