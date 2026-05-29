import streamlit as st
import pandas as pd

st.set_page_config(page_title="KBO AI 감독 모드", layout="wide")

# 1. 데이터 로드 시 헤더 자동 지정 안 함
@st.cache_data
def load_data(url):
    # header=None으로 해서 열 이름을 아예 무시하고 0,1,2... 번호로 읽습니다.
    df = pd.read_csv(url, header=None)
    # 데이터가 아닌 첫 행(기존 헤더)을 제거
    df = df.iloc[1:]
    return df

PITCHER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=0&single=true&output=csv"
BATTER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=779417540&single=true&output=csv"

st.title("⚾ KBO AI 감독 모드 V2.6 (안정화 버전)")

try:
    df_p = load_data(PITCHER_URL)
    df_h = load_data(BATTER_URL)
    
    # 2. 열 이름을 강제로 우리가 아는 순서로 부여 (위치 기반 매핑)
    # 1번째(인덱스 1)=선수명, 2번째(인덱스 2)=팀명, 3번째(인덱스 3)=ERA
    df_p.rename(columns={1: '선수명', 2: '팀명', 3: 'ERA'}, inplace=True)
    
    tab1, tab2 = st.tabs(["📊 투수 매치업", "⚾ 타자 리포트"])
    
    with tab1:
        teams = df_p['팀명'].unique()
        c1, c2 = st.columns(2)
        with c1:
            h_t = st.selectbox("홈 팀", teams)
            h_p = st.selectbox("홈 선발", df_p[df_p['팀명']==h_t]['선수명'])
        with c2:
            a_t = st.selectbox("원정 팀", [t for t in teams if t != h_t])
            a_p = st.selectbox("원정 선발", df_p[df_p['팀명']==a_t]['선수명'])
        
        if st.button("🚀 승부 예측"):
            h_era = pd.to_numeric(df_p[df_p['선수명']==h_p]['ERA'], errors='coerce').iloc[0]
            a_era = pd.to_numeric(df_p[df_p['선수명']==a_p]['ERA'], errors='coerce').iloc[0]
            st.metric("홈 팀 승리 확률", f"{(a_era/(h_era+a_era))*100:.1f}%")

    with tab2:
        st.dataframe(df_h, use_container_width=True)

except Exception as e:
    st.error(f"오류: {e}. 데이터 구조를 다시 확인해야 합니다.")
