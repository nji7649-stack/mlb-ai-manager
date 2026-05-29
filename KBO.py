import streamlit as st
import pandas as pd

st.set_page_config(page_title="KBO AI 감독 모드", layout="wide")

# 1. 시트 탭별 고정 URL 설정 (웹에 게시된 각 탭의 CSV 주소)
PITCHER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=0&single=true&output=csv"
BATTER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=779417540&single=true&output=csv"

st.title("⚾ KBO AI 감독 모드 V2.3")

@st.cache_data
def load_data(url):
    df = pd.read_csv(url)
    # 데이터가 아닌 불필요한 행(순위 헤더 중복 등) 제거
    df = df[df['선수명'] != '선수명'] 
    return df

try:
    df_p = load_data(PITCHER_URL)
    df_h = load_data(BATTER_URL)
    
    tab1, tab2 = st.tabs(["📊 투수 매치업", "⚾ 타자 리포트"])

    with tab1:
        st.header("투수 매치업 분석")
        teams = df_p['팀명'].unique()
        col1, col2 = st.columns(2)
        with col1:
            h_team = st.selectbox("홈 팀", teams, key="h_t")
            h_p = st.selectbox("홈 선발", df_p[df_p['팀명']==h_team]['선수명'], key="h_p")
        with col2:
            a_team = st.selectbox("원정 팀", teams, key="a_t")
            a_p = st.selectbox("원정 선발", df_p[df_p['팀명']==a_team]['선수명'], key="a_p")
        
        if st.button("🚀 승부 예측"):
            h_era = float(df_p[df_p['선수명']==h_p]['ERA'].iloc[0])
            a_era = float(df_p[df_p['선수명']==a_p]['ERA'].iloc[0])
            st.metric("홈 승리 확률", f"{(a_era/(h_era+a_era))*100:.1f}%")

    with tab2:
        st.header("타자 리포트")
        st.dataframe(df_h, use_container_width=True)

except Exception as e:
    st.error(f"데이터 로드 오류: 시트 주소를 확인하세요. ({e})")
