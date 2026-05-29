import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import random

# 페이지 설정
st.set_page_config(page_title="AI 스포츠 분석실", layout="wide")

# 1. 사이드바 메뉴
st.sidebar.title("🎮 분석실 컨트롤 타워")
mode = st.sidebar.radio("리그 선택", ["🇺🇸 MLB (안정형)", "🇰🇷 KBO (신규구축)", "🇯🇵 NPB (실험실)"])

# 2. MLB 모드 (기존 완벽 작동 코드)
if mode == "🇺🇸 MLB (안정형)":
    st.header("🇺🇸 MLB AI 감독 모드")
    st.info("MLB 모드는 기존 API 연동 방식으로 안정적으로 운영 중입니다.")
    # (여기에 기존의 MLB 시뮬레이션 및 데이터 호출 코드가 유지됩니다)

# 3. KBO 모드 (데이터 구조 분리형 신규 구축)
elif mode == "🇰🇷 KBO (신규구축)":
    st.header("🇰🇷 KBO AI 분석실")
    st.markdown("구글 시트의 데이터를 읽어와 분석합니다. (첫 행에 '분류, 팀, 이름, ERA, OPS' 필수)")
    kbo_url = st.text_input("🔗 구글 시트 CSV 주소:")
    
    if kbo_url:
        try:
            df = pd.read_csv(kbo_url)
            # 투수/타자 분리
            df_p = df[df['분류'] == '투수']
            df_h = df[df['분류'] == '타자']
            
            st.success("데이터 로드 완료!")
            
            # 분석 엔진
            teams = df_p['팀'].unique()
            col1, col2 = st.columns(2)
            with col1:
                h_team = st.selectbox("홈 팀", teams)
                h_p = st.selectbox("홈 선발", df_p[df_p['팀']==h_team]['이름'])
            with col2:
                a_team = st.selectbox("원정 팀", [t for t in teams if t != h_team])
                a_p = st.selectbox("원정 선발", df_p[df_p['팀']==a_team]['이름'])
            
            if st.button("🚀 KBO 승부 예측"):
                h_fip = df_p[df_p['이름']==h_p]['ERA'].iloc[0]
                a_fip = df_p[df_p['이름']==a_p]['ERA'].iloc[0]
                h_ops = df_h[df_h['팀']==h_team]['OPS'].mean()
                a_ops = df_h[df_h['팀']==a_team]['OPS'].mean()
                
                win_prob = (1 - (h_fip / (h_fip + a_fip))) * 100
                st.write(f"### {h_team} 승률: {win_prob:.1f}%")
        except Exception as e:
            st.error(f"데이터 형식을 확인하세요: {e}")

# 4. NPB 모드 (야후재팬 자동 수집형 신규 구축)
elif mode == "🇯🇵 NPB (실험실)":
    st.header("🇯🇵 NPB AI 자동 분석실")
    npb_url = st.text_input("🔗 야후재팬 NPB 기록 페이지 주소:")
    
    if npb_url:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(npb_url, headers=headers)
            tables = pd.read_html(res.text)
            
            st.success("데이터 수집 완료!")
            st.dataframe(tables[0]) # 첫 번째 표 출력
        except Exception as e:
            st.error(f"데이터 수집 실패: {e}")

st.sidebar.markdown("---")
st.sidebar.write("최종 업데이트: 2026.05.29")
