import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("⚾ KBO AI 데이터 센터 (홈페이지 복사 전용)")

# 주소 입력창 2개로 복구 (투수/타자 각각)
st.sidebar.header("데이터 세팅")
p_url = st.sidebar.text_input("🔗 투수 시트 웹 게시 주소:")
h_url = st.sidebar.text_input("🔗 타자 시트 웹 게시 주소:")

if p_url and h_url:
    try:
        # 감독님의 원본 헤더를 그대로 사용 (코드 내에서 이름을 맞춤)
        df_p = pd.read_csv(p_url)
        df_h = pd.read_csv(h_url)
        
        st.success("✅ 시트 로드 성공!")
        
        # '팀명'이라는 열 이름이 그대로 있다면 사용
        teams = df_p['팀명'].unique()
        
        col1, col2 = st.columns(2)
        with col1:
            h_team = st.selectbox("🏠 홈 팀", teams)
            # '선수명'이라는 열 이름 그대로 사용
            h_p = st.selectbox("홈 투수", df_p[df_p['팀명'] == h_team]['선수명'])
        with col2:
            a_team = st.selectbox("✈️ 원정 팀", [t for t in teams if t != h_team])
            a_p = st.selectbox("원정 투수", df_p[df_p['팀명'] == a_team]['선수명'])
            
        if st.button("🚀 승부 예측"):
            h_era = df_p[df_p['선수명'] == h_p]['ERA'].iloc[0]
            a_era = df_p[df_p['선수명'] == a_p]['ERA'].iloc[0]
            
            prob = (a_era / (h_era + a_era)) * 100
            st.write(f"### 🏠 {h_team} 승리 확률: {prob:.1f}%")
            
    except Exception as e:
        st.error(f"데이터 오류 발생: 구글 시트의 1행(헤더)에 '팀명', '선수명', 'ERA'라는 글자가 있는지 확인하세요.")
        st.write(f"상세 에러: {e}")
