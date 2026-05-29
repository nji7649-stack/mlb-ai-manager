import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("⚾ KBO AI 통합 데이터 센터")

# 주소 입력창 하나로 끝
csv_url = st.sidebar.text_input("🔗 웹에 게시된 통합 CSV 주소:")

if csv_url:
    try:
        # 데이터 로드
        df = pd.read_csv(csv_url)
        
        # '분류' 열을 기준으로 자동 분리
        df_p = df[df['분류'] == '투수']
        df_h = df[df['분류'] == '타자']
        
        st.success("✅ 데이터 로드 성공!")
        
        # 선택창 구성
        teams = df['팀명'].unique()
        col1, col2 = st.columns(2)
        with col1:
            h_team = st.selectbox("홈 팀", teams)
            h_p = st.selectbox("홈 투수", df_p[df_p['팀명'] == h_team]['선수명'])
        with col2:
            a_team = st.selectbox("원정 팀", [t for t in teams if t != h_team])
            a_p = st.selectbox("원정 투수", df_p[df_p['팀명'] == a_team]['선수명'])
            
        if st.button("🚀 승부 예측"):
            h_era = df_p[df_p['선수명'] == h_p]['ERA'].iloc[0]
            a_era = df_p[df_p['선수명'] == a_p]['ERA'].iloc[0]
            
            # 예측 로직
            win_prob = (a_era / (h_era + a_era)) * 100
            st.write(f"### 홈 팀 승리 확률: {win_prob:.1f}%")
            
    except Exception as e:
        st.error(f"오류: 시트 1행에 '분류', '팀명', '선수명', 'ERA'가 있는지 확인하세요. 에러: {e}")
