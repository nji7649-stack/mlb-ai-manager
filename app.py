import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date, timedelta
import random
from collections import Counter
import time
from nba_api.stats.endpoints import leaguegamefinder

st.set_page_config(page_title="통합 AI 스포츠 분석실", layout="wide")

# --- [MLB/KBO/NBA 공통 함수] ---
@st.cache_data(ttl=3600)
def load_nba_schedule(target_date):
    date_str = target_date.strftime('%m/%d/%Y')
    gamefinder = leaguegamefinder.LeagueGameFinder(date_from_nullable=date_str, date_to_nullable=date_str)
    games = gamefinder.get_data_frames()[0]
    if games.empty: return pd.DataFrame()
    games = games.drop_duplicates(subset=['GAME_ID'])
    games = games[['GAME_DATE', 'MATCHUP', 'WL', 'PTS']]
    games.columns = ['경기날짜', '대진', '결과', '득점']
    return games

@st.cache_data(ttl=60)
def load_kbo_schedule(target_date):
    date_str = target_date.strftime('%Y-%m-%d')
    url = f"https://api-gw.sports.naver.com/schedule/games?upperCategoryId=kbaseball&categoryId=kbo&fromDate={date_str}&toDate={date_str}"
    headers = {"User-Agent": "Mozilla/5.0"}
    games = []
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            games_data = res.json().get('result', {}).get('games', [])
            for game in games_data:
                if str(game.get('categoryId', '')).lower() != 'kbo': continue
                status_code = game.get('statusCode', '')
                h_score, a_score = game.get('homeTeamScore', 0), game.get('awayTeamScore', 0)
                
                # 과거 데이터 보정 로직
                if status_code == 'RESULT':
                    status_str = f"✅ 종료 ({h_score}:{a_score})"
                    time_val = "종료됨"
                    w, l = game.get('wPitcherName'), game.get('lPitcherName')
                    h_s, a_s = (f"승: {w}", f"패: {l}") if h_score > a_score else (f"패: {l}", f"승: {w}")
                else:
                    status_str = "⏳ 예정" if status_code != 'STARTED' else f"🔥 진행중"
                    time_val = (game.get('gameStartTime') or 'TBD')[:5]
                    h_s, a_s = game.get('homeStarterName', '미발표'), game.get('awayStarterName', '미발표')

                games.append({'경기시간': time_val, '상태': status_str, '홈 팀': game.get('homeTeamName'), '홈 선발투수': h_s, '원정 팀': game.get('awayTeamName'), '원정 선발투수': a_s})
    except: pass
    return pd.DataFrame(games)

# --- [사이드바 메뉴] ---
st.sidebar.title("⚾ 통합 AI 스포츠 분석실")
league_choice = st.sidebar.radio("분석할 리그를 선택하세요:", ["메이저리그 (MLB)", "한국프로야구 (KBO)", "NBA (농구)"])

# --- [리그별 렌더링] ---
if league_choice == "한국프로야구 (KBO)":
    st.header("🇰🇷 KBO AI 감독 모드")
    selected_date = st.date_input("분석 날짜:", datetime.now().date())
    df = load_kbo_schedule(selected_date)
    if not df.empty: st.dataframe(df, use_container_width=True)
    else: st.info("데이터가 없습니다.")

elif league_choice == "NBA (농구)":
    st.header("🏀 NBA AI 분석실")
    selected_date = st.date_input("분석 날짜:", datetime.now().date())
    df = load_nba_schedule(selected_date)
    if not df.empty: st.dataframe(df, use_container_width=True)
    else: st.info("진행된 경기가 없습니다.")

# (MLB 기존 코드 구간은 그대로 유지)
