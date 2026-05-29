import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("⚾ KBO AI 통합 데이터 센터")

csv_url = st.sidebar.text_input("🔗 웹에 게시된 CSV 주소:")

if csv_url:
    try:
        # 데이터 로드
        df = pd.read_csv(csv_url)
        st.success("✅ 데이터가 성공적으로 연결되었습니다!")
        
        # 1행에 '순위', '선수명', '팀명', 'ERA'가 있는 것을 그대로 활용
        # 데이터 중 '순위'가 숫자인 행만 투수로 간주
        df_p = df[pd.to_numeric(df['순위'], errors='coerce').notnull()]
        
        teams = df_p['팀명'].unique()
        
        col1, col2 = st.columns(2)
        with col1:
            h_team = st.selectbox("🏠 홈 팀", teams)
            h_p = st.selectbox("홈 선발 투수", df_p[df_p['팀명'] == h_team]['선수명'])
        with col2:
            a_team = st.selectbox("✈️ 원정 팀", [t for t in teams if t != h_team])
            a_p = st.selectbox("원정 선발 투수", df_p[df_p['팀명'] == a_team]['선수명'])
            
        if st.button("🚀 승부 예측 분석"):
            # 투수 이름으로 ERA 찾기
            h_era = float(df_p[df_p['선수명'] == h_p]['ERA'].iloc[0])
            a_era = float(df_p[df_p['선수명'] == a_p]['ERA'].iloc[0])
            
            # 예측 로직 (ERA가 낮을수록 승률 높음)
            # h_era가 0인 경우를 대비해 0.01로 보정
            h_val = 0.01 if h_era == 0 else h_era
            a_val = 0.01 if a_era == 0 else a_era
            
            win_prob = (a_val / (h_val + a_val)) * 100
            
            st.markdown("---")
            st.write(f"### 📊 분석 리포트")
            st.write(f"🏠 {h_team} 선발 {h_p} (ERA: {h_era})")
            st.write(f"✈️ {a_team} 선발 {a_p} (ERA: {a_era})")
            st.write(f"## 홈 팀 승리 예상 확률: **{win_prob:.1f}%**")
            
    except Exception as e:
        st.error(f"데이터 연동 중 오류 발생. 시트의 헤더를 확인하세요: {e}")
