import streamlit as st
import pandas as pd
import random
from collections import Counter

st.set_page_config(page_title="통합 AI 스포츠 분석실", layout="wide")

# MLB 및 KBO 기본 설정
MLB_PARK_FACTORS = {'Colorado Rockies': 1.12, 'Cincinnati Reds': 1.08, 'Boston Red Sox': 1.07} # 등 생략 가능
KBO_PARK_FACTORS = {'삼성 라이온즈': 1.06, 'SSG 랜더스': 1.05, '롯데 자이언츠': 1.02, 'NC 다이노스': 1.01, 'KT 위즈': 1.0, '한화 이글스': 1.0, 'KIA 타이거즈': 0.99, '키움 히어로즈': 0.97, 'LG 트윈스': 0.95, '두산 베어스': 0.95}

# 시뮬레이션 엔진
def run_simulation(h_fip, a_fip, h_ops, a_ops, park_factor):
    h_expected_runs = ((a_fip * (h_ops / 0.740)) + 0.2) * park_factor
    a_expected_runs = (h_fip * (a_ops / 0.740)) * park_factor
    h_wins = sum(1 for _ in range(10000) if random.gauss(h_expected_runs, 2.5) > random.gauss(a_expected_runs, 2.5))
    return (h_wins/10000)*100, 100 - (h_wins/10000)*100

# 사이드바 메뉴
menu = st.sidebar.radio("분석 모드 선택", ["🇺🇸 MLB 분석실", "🇰🇷 KBO 분석실"])

if menu == "🇺🇸 MLB 분석실":
    st.header("🇺🇸 MLB AI 감독 모드")
    st.write("MLB 데이터 분석 기능이 활성화되었습니다.")
    # (이전 MLB 코드 자리)

elif menu == "🇰🇷 KBO 분석실":
    st.header("🇰🇷 KBO AI 감독 모드 (구글 시트 연동)")
    h_url = st.text_input("🔗 타자 CSV 주소:")
    p_url = st.text_input("🔗 투수 CSV 주소:")
    
    if h_url and p_url:
        try:
            df_h = pd.read_csv(h_url)
            df_p = pd.read_csv(p_url)
            st.success("데이터 로드 성공!")
            
            h_team = st.selectbox("홈 팀", df_p['팀'].unique())
            a_team = st.selectbox("원정 팀", [t for t in df_p['팀'].unique() if t != h_team])
            h_p = st.selectbox("홈 선발", df_p[df_p['팀']==h_team]['이름'])
            a_p = st.selectbox("원정 선발", df_p[df_p['팀']==a_team]['이름'])
            
            if st.button("🚀 KBO 시뮬레이션 시작"):
                h_win, a_win = run_simulation(df_p[df_p['이름']==h_p]['ERA'].iloc[0], df_p[df_p['이름']==a_p]['ERA'].iloc[0], df_h[df_h['팀']==h_team]['OPS'].mean(), df_h[df_h['팀']==a_team]['OPS'].mean(), KBO_PARK_FACTORS.get(h_team, 1.0))
                st.success(f"{h_team} 승률: {h_win:.1f}% | {a_team} 승률: {a_win:.1f}%")
        except Exception as e:
            st.error(f"데이터를 불러올 수 없습니다. CSV 주소를 확인하세요: {e}")
