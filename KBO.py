import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("⚾ KBO AI 분석실 (원본 데이터 연동)")

# 1. 시트 URL 입력 (투수/타자 각각 받거나, 하나만 넣으면 탭별로 구분하게 함)
st.sidebar.header("데이터 세팅")
url = st.sidebar.text_input("🔗 웹에 게시된 구글 시트 주소:")

if url:
    try:
        # 투수 데이터 읽기 (투수 탭 데이터)
        df_p = pd.read_csv(url, sheet_name='투수') # 구글 시트에서 탭별로 링크를 따야 함
        # 타자 데이터 읽기
        df_h = pd.read_csv(url, sheet_name='타자')
        
        st.success("데이터 로드 완료!")
        
        # 2. 팀 및 선수 선택
        teams = df_p['팀명'].unique()
        col1, col2 = st.columns(2)
        with col1:
            h_team = st.selectbox("🏠 홈 팀", teams)
            h_p = st.selectbox("홈 선발 투수", df_p[df_p['팀명'] == h_team]['선수명'])
        with col2:
            a_team = st.selectbox("✈️ 원정 팀", teams)
            a_p = st.selectbox("원정 선발 투수", df_p[df_p['팀명'] == a_team]['선수명'])
            
        if st.button("🚀 데이터 분석"):
            h_era = df_p[df_p['선수명'] == h_p]['ERA'].iloc[0]
            a_era = df_p[df_p['선수명'] == a_p]['ERA'].iloc[0]
            
            st.write(f"### 분석 결과")
            st.write(f"홈({h_p}) ERA: {h_era} vs 원정({a_p}) ERA: {a_era}")
            # 승률 로직 (ERA 기반)
            prob = (a_era / (h_era + a_era)) * 100
            st.write(f"**홈 팀 승리 예상 확률: {prob:.1f}%**")
            
    except Exception as e:
        st.error(f"데이터 로드 에러: {e}")
