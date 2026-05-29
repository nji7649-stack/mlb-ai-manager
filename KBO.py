import streamlit as st
import pandas as pd

st.set_page_config(page_title="KBO AI 분석실", layout="wide")
st.title("⚾ KBO AI 전용 분석실")

# 사이드바에서 데이터 세팅
st.sidebar.header("데이터 세팅")
h_url = st.sidebar.text_input("🔗 타자 CSV 주소:")
p_url = st.sidebar.text_input("🔗 투수 CSV 주소:")

if h_url and p_url:
    try:
        df_h = pd.read_csv(h_url)
        df_p = pd.read_csv(p_url)
        
        # 필수 열 확인
        required_p = ['팀', '이름', 'ERA']
        required_h = ['팀', '이름', 'OPS']
        
        if all(col in df_p.columns for col in required_p) and all(col in df_h.columns for col in required_h):
            st.success("✅ 데이터 로드 성공!")
            
            teams = df_p['팀'].unique()
            col1, col2 = st.columns(2)
            with col1:
                h_team = st.selectbox("홈 팀", teams)
                h_p = st.selectbox("홈 선발", df_p[df_p['팀']==h_team]['이름'])
            with col2:
                a_team = st.selectbox("원정 팀", [t for t in teams if t != h_team])
                a_p = st.selectbox("원정 선발", df_p[df_p['팀']==a_team]['이름'])
            
            if st.button("🚀 시뮬레이션"):
                # 계산 엔진
                h_era = df_p[df_p['이름']==h_p]['ERA'].iloc[0]
                a_era = df_p[df_p['이름']==a_p]['ERA'].iloc[0]
                h_ops = df_h[df_h['팀']==h_team]['OPS'].mean()
                a_ops = df_h[df_h['팀']==a_team]['OPS'].mean()
                
                win_prob = (1 - (h_era / (h_era + a_era))) * 100
                st.write(f"### 홈 승리 확률: {win_prob:.1f}%")
        else:
            st.error("데이터에 '팀', '이름', 'ERA', 'OPS' 열이 있는지 확인하세요.")
    except Exception as e:
        st.error(f"오류: {e}")
