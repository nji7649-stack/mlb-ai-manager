import streamlit as st
import pandas as pd

st.set_page_config(page_title="KBO 데이터 센터", layout="wide")
st.title("⚾ KBO AI 전용 분석실 (Clean Version)")

csv_url = st.sidebar.text_input("🔗 구글 시트 CSV 주소 입력:")

if csv_url:
    try:
        # 데이터 로드
        df = pd.read_csv(csv_url)
        
        # 투수/타자 자동 분리
        df_pitcher = df[df['분류'] == '투수']
        df_batter = df[df['분류'] == '타자']
        
        st.success("✅ 시트 로드 성공!")
        
        # 팀 리스트
        teams = df['팀'].unique()
        
        # 선발 대진 설정
        col1, col2 = st.columns(2)
        with col1:
            h_team = st.selectbox("🏠 홈 팀", teams)
            h_p = st.selectbox("홈 투수", df_pitcher[df_pitcher['팀'] == h_team]['이름'])
        with col2:
            a_team = st.selectbox("✈️ 원정 팀", [t for t in teams if t != h_team])
            a_p = st.selectbox("원정 투수", df_pitcher[df_pitcher['팀'] == a_team]['이름'])

        if st.button("🚀 데이터 분석"):
            h_era = df_pitcher[df_pitcher['이름'] == h_p]['ERA'].iloc[0]
            a_era = df_pitcher[df_pitcher['이름'] == a_p]['ERA'].iloc[0]
            
            st.write(f"홈 투수 ERA: {h_era} | 원정 투수 ERA: {a_era}")
            st.info("데이터 기반 분석 완료!")

    except Exception as e:
        st.error(f"데이터를 읽는 중 오류 발생. 시트의 헤더('분류', '팀', '이름', 'ERA', 'OPS')를 확인하세요.")
        st.write(f"에러 메시지: {e}")
