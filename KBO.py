import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="글로벌 AI 스포츠 분석실", layout="wide")

# 2. 데이터 로드 함수 (오류 방지를 위해 함수를 맨 위에 배치)
@st.cache_data
def load_data(url):
    df = pd.read_csv(url)
    df.columns = df.iloc[0] # 첫 줄을 헤더로
    return df[1:]

# 3. 데이터 주소
PITCHER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=0&single=true&output=csv"
BATTER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=779417540&single=true&output=csv"

# 4. 사이드바 구성 (MLB와 동일)
st.sidebar.title("통합 AI 스포츠 분석실")
league = st.sidebar.radio("분석할 리그를 선택하세요:", ["us 메이저리그 (MLB)", "KR 한국프로야구 (KBO)"])

if league == "KR 한국프로야구 (KBO)":
    st.title("⚾ KBO AI 감독 모드")
    try:
        df_p = load_data(PITCHER_URL)
        df_h = load_data(BATTER_URL)
        
        tab1, tab2 = st.tabs(["📊 투수 매치업", "⚾ 타자 리포트"])
        with tab1:
            teams = df_p['팀명'].unique()
            col1, col2 = st.columns(2)
            with col1:
                h_team = st.selectbox("홈 팀", teams)
                h_p = st.selectbox("홈 선발", df_p[df_p['팀명']==h_team]['선수명'])
            with col2:
                a_team = st.selectbox("원정 팀", [t for t in teams if t != h_team])
                a_p = st.selectbox("원정 선발", df_p[df_p['팀명']==a_team]['선수명'])
            
            if st.button("🚀 정밀 승부 예측"):
                h_era = pd.to_numeric(df_p[df_p['선수명']==h_p]['ERA'], errors='coerce').iloc[0]
                a_era = pd.to_numeric(df_p[df_p['선수명']==a_p]['ERA'], errors='coerce').iloc[0]
                m1, m2 = st.columns(2)
                m1.metric("홈 승리 확률", f"{(a_era/(h_era+a_era))*100:.1f}%")
                m2.metric("원정 승리 확률", f"{(h_era/(h_era+a_era))*100:.1f}%")
        with tab2:
            st.dataframe(df_h, use_container_width=True)
            
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
else:
    st.title("MLB 분석 모드")
    st.write("MLB 데이터가 로드되었습니다. (기존 MLB 기능을 여기에 연결하세요)")
