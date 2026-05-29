import streamlit as st
import pandas as pd

# 1. 페이지 설정 (MLB 스타일)
st.set_page_config(page_title="KBO AI 스포츠 분석실", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stMetric { background-color: #161616; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

PITCHER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=0&single=true&output=csv"
BATTER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=779417540&single=true&output=csv"

# 2. 강력한 데이터 정제 함수 (에러 원천 차단)
@st.cache_data
def load_clean_data(url, data_type):
    # 헤더를 아예 읽지 않음 (중복 이름 에러 방지)
    df = pd.read_csv(url, header=None, dtype=str)
    
    # 데이터가 없는 빈 줄 제거
    df = df.dropna(subset=[1])
    # KBO 홈피에서 긁어오며 섞인 '선수명' 글자가 있는 행 강제 삭제
    df = df[df[1] != '선수명']
    
    # 무조건 위치(숫자)로 데이터 매핑
    if data_type == 'pitcher':
        df = df.rename(columns={1: '선수명', 2: '팀명', 3: 'ERA'})
        df['ERA'] = pd.to_numeric(df['ERA'], errors='coerce')
    elif data_type == 'batter':
        df = df.rename(columns={1: '선수명', 2: '팀명'})
        
    return df

st.title("⚾ KR KBO AI 감독 모드")
st.caption("구글 시트 데이터베이스 동기화 완료")

try:
    with st.spinner("데이터를 정제하고 불러오는 중..."):
        df_p = load_clean_data(PITCHER_URL, 'pitcher')
        df_h = load_clean_data(BATTER_URL, 'batter')

    # 3. MLB 분석실과 동일한 탭 구조
    tab1, tab2, tab3 = st.tabs(["🔥 매치업 분석", "⚾ 투수 스탯", "🏏 타자 스탯"])

    with tab1:
        st.subheader("오늘의 KBO 승부 예측")
        teams = df_p['팀명'].dropna().unique()
        
        col1, col2 = st.columns(2)
        with col1:
            h_team = st.selectbox("🏠 홈 팀", teams, key='h_t')
            h_pitchers = df_p[df_p['팀명'] == h_team]['선수명'].dropna().unique()
            h_p = st.selectbox("홈 선발투수", h_pitchers, key='h_p')

        with col2:
            a_team = st.selectbox("✈️ 어웨이 팀", [t for t in teams if t != h_team], key='a_t')
            a_pitchers = df_p[df_p['팀명'] == a_team]['선수명'].dropna().unique()
            a_p = st.selectbox("어웨이 선발투수", a_pitchers, key='a_p')

        if st.button("🚀 AI 승률 계산"):
            h_era = df_p[df_p['선수명'] == h_p]['ERA'].iloc[0]
            a_era = df_p[df_p['선수명'] == a_p]['ERA'].iloc[0]

            # 0이거나 에러난 데이터 보정 로직
            h_era = 0.01 if pd.isna(h_era) or h_era == 0 else h_era
            a_era = 0.01 if pd.isna(a_era) or a_era == 0 else a_era

            h_prob = (a_era / (h_era + a_era)) * 100
            a_prob = 100 - h_prob

            st.markdown("---")
            m1, m2 = st.columns(2)
            m1.metric(f"🏠 {h_team} 승리 확률", f"{h_prob:.1f}%", f"선발 ERA: {h_era:.2f}", delta_color="inverse")
            m2.metric(f"✈️ {a_team} 승리 확률", f"{a_prob:.1f}%", f"선발 ERA: {a_era:.2f}", delta_color="inverse")

    with tab2:
        st.subheader("전체 투수 스탯")
        st.dataframe(df_p, use_container_width=True)

    with tab3:
        st.subheader("전체 타자 스탯")
        st.dataframe(df_h, use_container_width=True)

except Exception as e:
    st.error(f"데이터 정제 중 치명적 오류 발생: {e}. 구글 시트에 데이터가 올바르게 있는지 확인하세요.")
