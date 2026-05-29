import streamlit as st
import pandas as pd

st.set_page_config(page_title="KBO AI 감독 모드", layout="wide")

# 고정 주소 설정 (여기에 실제 웹 게시 CSV 주소를 넣으세요)
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=0&single=true&output=csv"

st.title("⚾ KBO AI 감독 모드 V2.2")

@st.cache_data
def load_data(url):
    df = pd.read_csv(url)
    # 1. 빈 줄(None) 제거
    df = df.dropna(how='all')
    # 2. '순위' 열에 숫자가 아닌 것(홈페이지 헤더 중복 등) 제거
    df = df[pd.to_numeric(df['순위'], errors='coerce').notnull()]
    return df

try:
    df = load_data(CSV_URL)
    
    # 3. 투수/타자 자동 구분 (시트 내 데이터 값 기준)
    # 투수와 타자 시트의 주소를 따로 받거나, 
    # 데이터 내 '포지션' 혹은 '구분' 열이 없다면 
    # 투수/타자 탭을 나누어 데이터를 각각 로드하는 것이 가장 정확합니다.
    
    tab1, tab2, tab3 = st.tabs(["📊 투수 매치업", "⚾ 타자 리포트", "📋 전체 데이터"])
    
    with tab1:
        st.header("투수 분석")
        # 투수 데이터 필터링 (순위가 있는 행을 투수로 간주)
        teams = df['팀명'].unique()
        col1, col2 = st.columns(2)
        with col1:
            h_team = st.selectbox("홈 팀", teams, key="h_t")
            h_p = st.selectbox("홈 선발", df[df['팀명']==h_team]['선수명'], key="h_p")
        with col2:
            a_team = st.selectbox("원정 팀", teams, key="a_t")
            a_p = st.selectbox("원정 선발", df[df['팀명']==a_team]['선수명'], key="a_p")
            
        if st.button("🚀 승부 예측"):
            h_era = float(df[df['선수명']==h_p]['ERA'].iloc[0])
            a_era = float(df[df['선수명']==a_p]['ERA'].iloc[0])
            m1, m2 = st.columns(2)
            m1.metric("홈 승리 확률", f"{(a_era/(h_era+a_era))*100:.1f}%")
            m2.metric("원정 승리 확률", f"{(h_era/(h_era+a_era))*100:.1f}%")

    with tab2:
        st.header("타자 리포트")
        st.write("타자 데이터를 연결하면 이곳에 OPS 기반 분석이 나타납니다.")

    with tab3:
        st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"데이터 정제 중 오류: {e}. 구글 시트 주소를 확인하세요.")
