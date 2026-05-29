import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("⚾ KBO AI 전용 분석실 (분석 엔진 탑재)")

csv_url = st.sidebar.text_input("🔗 웹에 게시된 CSV 주소:")

if csv_url:
    try:
        df = pd.read_csv(csv_url)
        st.success("✅ 시트 로드 성공!")
        
        df_p = df[df['분류'] == '투수']
        teams = df_p['팀'].unique()
        
        col1, col2 = st.columns(2)
        with col1:
            h_team = st.selectbox("홈 팀", teams)
            h_p = st.selectbox("홈 투수", df_p[df_p['팀'] == h_team]['이름'])
        with col2:
            a_team = st.selectbox("원정 팀", [t for t in teams if t != h_team])
            a_p = st.selectbox("원정 투수", df_p[df_p['팀'] == a_team]['이름'])
            
        if st.button("🚀 데이터 분석"):
            h_era = df_p[df_p['이름'] == h_p]['ERA'].iloc[0]
            a_era = df_p[df_p['이름'] == a_p]['ERA'].iloc[0]
            
            # 간단한 승률 로직: ERA가 낮을수록 승률이 높음
            h_win_prob = (a_era / (h_era + a_era)) * 100
            
            st.markdown("---")
            st.subheader("📊 분석 결과")
            st.write(f"### 🏠 {h_team} ({h_p}) 승리 확률: **{h_win_prob:.1f}%**")
            st.write(f"### ✈️ {a_team} ({a_p}) 승리 확률: **{100-h_win_prob:.1f}%**")
            
    except Exception as e:
        st.error(f"오류: {e}")
