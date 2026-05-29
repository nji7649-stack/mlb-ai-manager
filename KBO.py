import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="KBO AI 전력 분석실", layout="wide")

st.title("⚾ KBO AI 전력 분석실")

# 1. 데이터 입력부 (투수/타자 각각 입력)
st.sidebar.header("데이터 세팅")
h_url = st.sidebar.text_input("🔗 타자 CSV 주소 (웹 게시):")
p_url = st.sidebar.text_input("🔗 투수 CSV 주소 (웹 게시):")

if h_url and p_url:
    try:
        # 데이터 로드
        df_h = pd.read_csv(h_url)
        df_p = pd.read_csv(p_url)
        
        # 데이터 확인 (감독님 시트가 '팀', '이름', 'ERA', 'OPS'를 포함한다고 가정)
        teams = df_p['팀'].unique()
        
        # 2. 팀 및 선발 투수 선택
        col1, col2 = st.columns(2)
        with col1:
            h_team = st.selectbox("홈 팀", teams)
            h_p = st.selectbox("홈 선발", df_p[df_p['팀'] == h_team]['이름'])
        with col2:
            a_team = st.selectbox("원정 팀", [t for t in teams if t != h_team])
            a_p = st.selectbox("원정 선발", df_p[df_p['팀'] == a_team]['이름'])
            
        # 3. 분석 실행
        if st.button("🚀 승부 예측 시뮬레이션"):
            h_fip = df_p[df_p['이름'] == h_p]['ERA'].iloc[0]
            a_fip = df_p[df_p['이름'] == a_p]['ERA'].iloc[0]
            h_ops = df_h[df_h['팀'] == h_team]['OPS'].mean()
            a_ops = df_h[df_h['팀'] == a_team]['OPS'].mean()
            
            # 승률 계산 로직 (간단한 공방 예측)
            win_prob = (1 - (h_fip / (h_fip + a_fip))) * 100
            
            st.markdown("---")
            st.subheader("📊 분석 결과")
            st.success(f"**{h_team} 승리 확률: {win_prob:.1f}%**")
            st.info(f"**{a_team} 승리 확률: {100-win_prob:.1f}%**")
            
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다. 시트의 헤더('팀', '이름', 'ERA', 'OPS')를 확인하세요.")
        st.write(f"상세 에러: {e}")
else:
    st.info("왼쪽 사이드바에 타자/투수 CSV 주소를 입력하면 분석이 시작됩니다.")
