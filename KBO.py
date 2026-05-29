import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="KBO AI 분석실", layout="wide")

# 2. MLB 스타일 다크 모드 디자인
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161616; padding: 20px; border-radius: 10px; border-left: 5px solid #deff9a; }
    h1 { color: #deff9a !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. 고정 주소 설정 (매번 입력 안 해도 됩니다!)
FIXED_CSV_URL = "여기에_구글_시트_웹_게시_CSV_주소를_한번만_복사해_넣으세요"

st.sidebar.title("🎮 분석실 컨트롤 타워")
st.sidebar.info("데이터가 자동으로 로드됩니다.")

try:
    df = pd.read_csv(FIXED_CSV_URL)
    df_p = df[pd.to_numeric(df['순위'], errors='coerce').notnull()]
    df_h = df[pd.to_numeric(df['순위'], errors='coerce').isna()]
    
    teams = df_p['팀명'].unique()
    
    # MLB 스타일 대진 선택창
    st.header("⚾ KBO AI 감독 모드")
    col1, col2 = st.columns(2)
    with col1:
        h_team = st.selectbox("🏠 홈 팀", teams)
        h_p = st.selectbox("홈 선발", df_p[df_p['팀명'] == h_team]['선수명'])
    with col2:
        a_team = st.selectbox("✈️ 원정 팀", [t for t in teams if t != h_team])
        a_p = st.selectbox("원정 선발", df_p[df_p['팀명'] == a_team]['선수명'])
        
    if st.button("🚀 정밀 분석 실행"):
        h_era = float(df_p[df_p['선수명'] == h_p]['ERA'].iloc[0])
        a_era = float(df_p[df_p['선수명'] == a_p]['ERA'].iloc[0])
        h_ops = df_h[df_h['팀명'] == h_team]['OPS'].mean() if 'OPS' in df_h.columns else 0.700
        
        # 정교한 승률 모델
        win_prob = ( (a_era + (1-h_ops*0.5)) / (h_era + a_era) ) * 100
        
        # MLB 스타일 메트릭
        m1, m2 = st.columns(2)
        m1.metric("홈 팀 승리 확률", f"{win_prob:.1f}%")
        m2.metric("원정 팀 승리 확률", f"{100-win_prob:.1f}%")
        st.info(f"분석 상세: 홈 타선 OPS {h_ops:.3f} | 투수 ERA {h_era:.2f}")

except Exception as e:
    st.warning("⚠️ 데이터 로드 대기 중... 코드 내 FIXED_CSV_URL을 확인하세요.")
