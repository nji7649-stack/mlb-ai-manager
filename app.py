import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="MLB AI 감독 모드", layout="wide")
st.title("⚾ MLB AI 감독 모드 V2.0 (종합 데이터 엔진)")

# 타자/투수 전체 데이터를 메이저리그 서버에서 긁어오는 함수
@st.cache_data(ttl=3600)
def load_mlb_all_data():
    # 1. 타자 세부 데이터 수집
    hitter_url = "https://statsapi.mlb.com/api/v1/stats?stats=season&group=hitting&gameType=R&season=2026&playerPool=ALL&limit=1500"
    h_res = requests.get(hitter_url).json()
    h_splits = h_res['stats'][0]['splits']
    
    hitter_list = []
    for row in h_splits:
        s = row['stat']
        hitter_list.append({
            '이름': row['player']['fullName'], '팀': row['team']['name'],
            '경기': s.get('gamesPlayed', 0), '타수': s.get('atBats', 0),
            '득점': s.get('runs', 0), '안타': s.get('hits', 0),
            '2루타': s.get('doubles', 0), '3루타': s.get('triples', 0),
            '홈런': s.get('homeRuns', 0), '타점': s.get('rbi', 0),
            '볼넷': s.get('baseOnBalls', 0), '삼진': s.get('strikeOuts', 0),
            '도루': s.get('stolenBases', 0), '타율': s.get('avg', '.000'),
            '출루율': s.get('obp', '.000'), '장타율': s.get('slg', '.000'), 'OPS': s.get('ops', '.000')
        })
        
    # 2. 투수 세부 데이터 수집
    pitcher_url = "https://statsapi.mlb.com/api/v1/stats?stats=season&group=pitching&gameType=R&season=2026&playerPool=ALL&limit=1500"
    p_res = requests.get(pitcher_url).json()
    p_splits = p_res['stats'][0]['splits']
    
    pitcher_list = []
    for row in p_splits:
        s = row['stat']
        pitcher_list.append({
            '이름': row['player']['fullName'], '팀': row['team']['name'],
            '승': s.get('wins', 0), '패': s.get('losses', 0),
            '세이브': s.get('saves', 0), '평균자책점(ERA)': s.get('era', '0.00'),
            '경기': s.get('gamesPlayed', 0), '선발': s.get('gamesStarted', 0),
            '이닝': s.get('inningsPitched', '0.0'), '피안타': s.get('hits', 0),
            '실점': s.get('runs', 0), '자책점': s.get('earnedRuns', 0),
            '피홈런': s.get('homeRuns', 0), '볼넷': s.get('baseOnBalls', 0),
            '탈삼진': s.get('strikeOuts', 0), 'WHIP': s.get('whip', '0.00')
        })
        
    return pd.DataFrame(hitter_list), pd.DataFrame(pitcher_list)

st.write("🔄 MLB 공식 데이터베이스에서 전체 타자/투수 지표를 동시 구축 중...")

try:
    df_hitter, df_pitcher = load_mlb_all_data()
    st.success("✅ 메이저리그 전 선수 종합 데이터 베이스 구축 완료!")
    
    # 깔끔하게 탭으로 나누어 보여주기
    tab1, tab2 = st.tabs(["🏃‍♂️ 타자 전체 스탯", "投 투수 전체 스탯"])
    
    with tab1:
        st.subheader("📋 2026 시즌 타자 데이터 리더보드")
        st.dataframe(df_hitter)
        
    with tab2:
        st.subheader("📋 2026 시즌 투수 데이터 리더보드")
        # 방어율 순으로 정렬 (이닝을 어느 정도 던진 투수 기준)
        df_pitcher['평균자책점(ERA)'] = pd.to_numeric(df_pitcher['평균자책점(ERA)'])
        df_pitcher = df_pitcher.sort_values(by='평균자책점(ERA)').reset_index(drop=True)
        st.dataframe(df_pitcher)
        
except Exception as e:
    st.error(f"데이터 구축 실패: {e}")
