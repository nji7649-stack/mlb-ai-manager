import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="KBO AI 감독 모드", layout="wide")

# 2. 가장 먼저 실행되어야 할 데이터 로드 함수 정의
@st.cache_data
def load_data(url):
    df = pd.read_csv(url)
    # 첫 줄을 헤더로 강제 지정하고 데이터 정제
    df.columns = df.iloc[0]
    df = df[1:]
    return df

# 3. CSV 주소 설정
PITCHER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=0&single=true&output=csv"
BATTER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=779417540&single=true&output=csv"

# 4. 분석실 시작
st.title("⚾ KBO AI 감독 모드 V2.4")

try:
    # 5. 데이터 불러오기 (함수 호출)
    df_p = load_data(PITCHER_URL)
    df_h = load_data(BATTER_URL)
    
    # 탭 구성
    tab1, tab2 = st.tabs(["📊 투수 매치업", "⚾ 타자 리포트"])
    
    with tab1:
        st.header("투수 데이터 분석")
        teams = df_p['팀명'].unique()
        col1, col2 = st.columns(2)
        with col1:
            h_team = st.selectbox("홈 팀", teams)
            h_p = st.selectbox("홈 선발", df_p[df_p['팀명']==h_team]['선수명'])
        with col2:
            a_team = st.selectbox("원정 팀", [t for t in teams if t != h_team])
            a_p = st.selectbox("원정 선발", df_p[df_p['팀명']==a_team]['선수명'])
        
        if st.button("🚀 승부 예측 분석"):
            h_era = pd.to_numeric(df_p[df_p['선수명']==h_p]['ERA'], errors='coerce').iloc[0]
            a_era = pd.to_numeric(df_p[df_p['선수명']==a_p]['ERA'], errors='coerce').iloc[0]
            
            m1, m2 = st.columns(2)
            m1.metric("홈 승리 확률", f"{(a_era/(h_era+a_era))*100:.1f}%")
            m2.metric("원정 승리 확률", f"{(h_era/(h_era+a_era))*100:.1f}%")

    with tab2:
        st.header("타자 데이터")
        st.dataframe(df_h, use_container_width=True)

except Exception as e:
    st.error(f"데이터 로드 도중 오류 발생: {e}")
