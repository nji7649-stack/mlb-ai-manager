import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="KBO AI 감독 모드", layout="wide")

# 2. 데이터 로드 함수
@st.cache_data
def load_data(url):
    df = pd.read_csv(url)
    df.columns = df.iloc[0] # 첫 행을 헤더로
    return df[1:]

# 3. KBO 전용 주소
PITCHER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=0&single=true&output=csv"
BATTER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=779417540&single=true&output=csv"

st.title("⚾ KBO AI 감독 모드 V2.5")

try:
    df_p = load_data(PITCHER_URL)
    df_h = load_data(BATTER_URL)
    
    # 투수/타자 탭 분리
    tab1, tab2 = st.tabs(["📊 투수 매치업", "⚾ 타자 리포트"])
    
    with tab1:
        st.header("투수 데이터 분석")
        # 컬럼명이 제대로 인식되지 않을 경우를 대비한 안전 장치
        if '팀명' in df_p.columns and '선수명' in df_p.columns:
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
                st.metric("홈 승리 확률", f"{(a_era/(h_era+a_era))*100:.1f}%")
        else:
            st.write("데이터 열 이름을 확인하세요:", df_p.columns.tolist())

    with tab2:
        st.header("타자 리포트")
        st.dataframe(df_h, use_container_width=True)

except Exception as e:
    st.error(f"데이터 로드 오류: {e}")
