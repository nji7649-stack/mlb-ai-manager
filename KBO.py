import streamlit as st
import pandas as pd

# 1. 페이지 및 MLB 스타일 디자인 설정
st.set_page_config(page_title="KBO AI 감독 모드", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stMetric { background-color: #161616; padding: 20px; border-radius: 10px; border-left: 5px solid #deff9a; }
    h1 { color: #deff9a !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. 각 탭의 실제 CSV 주소 (방금 생성하신 주소들입니다)
PITCHER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=0&single=true&output=csv"
BATTER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=779417540&single=true&output=csv"

st.title("⚾ KBO AI 감독 모드 V2.3")

# 3. 데이터 로드 함수 (헤더 행을 자동으로 정리)
@st.cache_data
def load_data(url):
    df = pd.read_csv(url)
    # 1행이 헤더가 아니거나 중복될 경우, 첫 행을 헤더로 강제 지정
    df.columns = df.iloc[0]
    df = df[1:]
    return df

try:
    df_p = load_data(PITCHER_URL)
    df_h = load_data(BATTER_URL)
    
    # 탭 생성 (MLB와 동일한 구조)
    tab1, tab2 = st.tabs(["📊 투수 매치업", "⚾ 타자 리포트"])

    with tab1:
        st.header("투수 데이터 분석")
        # 투수 데이터 중 팀명과 선수명 추출
        teams = df_p['팀명'].unique()
        col1, col2 = st.columns(2)
        with col1:
            h_team = st.selectbox("홈 팀", teams)
            h_p = st.selectbox("홈 선발", df_p[df_p['팀명'] == h_team]['선수명'])
        with col2:
            a_team = st.selectbox("원정 팀", [t for t in teams if t != h_team])
            a_p = st.selectbox("원정 선발", df_p[df_p['팀명'] == a_team]['선수명'])
        
        if st.button("🚀 정밀 승부 예측"):
            # 수치 데이터 변환 및 예측 (ERA가 숫자인지 확인)
            h_era = pd.to_numeric(df_p[df_p['선수명'] == h_p]['ERA'], errors='coerce').iloc[0]
            a_era = pd.to_numeric(df_p[df_p['선수명'] == a_p]['ERA'], errors='coerce').iloc[0]
            
            m1, m2 = st.columns(2)
            m1.metric("홈 승리 확률", f"{(a_era/(h_era+a_era))*100:.1f}%")
            m2.metric("원정 승리 확률", f"{(h_era/(h_era+a_era))*100:.1f}%")

    with tab2:
        st.header("타자 스탯 리포트")
        st.dataframe(df_h, use_container_width=True)

except Exception as e:
    st.error(f"데이터 로드 에러: {e}")
