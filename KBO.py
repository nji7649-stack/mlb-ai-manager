import streamlit as st
import pandas as pd

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="KBO AI 감독 모드", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #161616; padding: 20px; border-radius: 10px; border-left: 5px solid #deff9a; }
    h1 { color: #deff9a !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. 고정 데이터 주소 (아래에 실제 주소 넣으세요)
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=0&single=true&output=csv" 

st.title("⚾ KBO AI 감독 모드")

# 3. 탭 구성 (MLB처럼 탭으로 메뉴 분리)
tab1, tab2 = st.tabs(["📊 매치업 분석", "📋 선수 스탯"])

try:
    df = pd.read_csv(CSV_URL)
    df_p = df[pd.to_numeric(df['순위'], errors='coerce').notnull()]
    df_h = df[pd.to_numeric(df['순위'], errors='coerce').isna()]
    teams = df_p['팀명'].unique()

    with tab1:
        st.header("정밀 승부 예측")
        col1, col2 = st.columns(2)
        with col1:
            h_team = st.selectbox("홈 팀", teams)
            h_p = st.selectbox("홈 선발", df_p[df_p['팀명'] == h_team]['선수명'])
        with col2:
            a_team = st.selectbox("원정 팀", [t for t in teams if t != h_team])
            a_p = st.selectbox("원정 선발", df_p[df_p['팀명'] == a_team]['선수명'])

        if st.button("🚀 정밀 분석 실행"):
            h_era = float(df_p[df_p['선수명'] == h_p]['ERA'].iloc[0])
            a_era = float(df_p[df_p['선수명'] == a_p]['ERA'].iloc[0])
            h_ops = df_h[df_h['팀명'] == h_team]['OPS'].mean() if 'OPS' in df_h.columns else 0.700
            
            win_prob = ( (a_era + (1-h_ops*0.5)) / (h_era + a_era) ) * 100
            
            m1, m2 = st.columns(2)
            m1.metric("홈 팀 승리 확률", f"{win_prob:.1f}%")
            m2.metric("원정 팀 승리 확률", f"{100-win_prob:.1f}%")
            st.info(f"분석 상세: 홈 타선 OPS {h_ops:.3f} | 투수 ERA {h_era:.2f}")

    with tab2:
        st.header("선수단 상세 스탯")
        st.dataframe(df, use_container_width=True)

except:
    st.error("데이터 로드가 필요합니다. 코드 내 CSV_URL을 확인하세요.")
