import streamlit as st
import pandas as pd
import random
from collections import Counter

st.set_page_config(page_title="KBO 데이터 분석실", layout="wide")

# 파크팩터 설정
KBO_PARK_FACTORS = {'삼성 라이온즈': 1.06, 'SSG 랜더스': 1.05, '롯데 자이언츠': 1.02, 'NC 다이노스': 1.01, 'KT 위즈': 1.0, '한화 이글스': 1.0, 'KIA 타이거즈': 0.99, '키움 히어로즈': 0.97, 'LG 트윈스': 0.95, '두산 베어스': 0.95}

def run_kbo_simulation(h_fip, a_fip, h_avg_ip, a_avg_ip, h_ops, a_ops, h_bp_fip, a_bp_fip, park_factor):
    h_starter_weight = h_avg_ip / 9.0
    a_starter_weight = a_avg_ip / 9.0
    h_eff_fip = (h_fip * h_starter_weight) + (h_bp_fip * (1 - h_starter_weight))
    a_eff_fip = (a_fip * a_starter_weight) + (a_bp_fip * (1 - a_starter_weight))
    h_expected_runs = ((a_eff_fip * (h_ops / 0.740)) + 0.2) * park_factor
    a_expected_runs = (h_eff_fip * (a_ops / 0.740)) * park_factor
    h_wins, a_wins = 0, 0
    for _ in range(10000):
        h_score = max(0, int(random.gauss(h_expected_runs, 2.5)))
        a_score = max(0, int(random.gauss(a_expected_runs, 2.5)))
        if h_score > a_score: h_wins += 1
        elif a_score > h_score: a_wins += 1
    return (h_wins/10000)*100, (a_wins/10000)*100

st.title("⚾ KBO AI 감독 모드")
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
        
        if st.button("🚀 시뮬레이션 시작"):
            h_win, a_win = run_kbo_simulation(df_p[df_p['이름']==h_p]['ERA'].iloc[0], df_p[df_p['이름']==a_p]['ERA'].iloc[0], 6.0, 6.0, df_h[df_h['팀']==h_team]['OPS'].mean(), df_h[df_h['팀']==a_team]['OPS'].mean(), 4.5, 4.5, KBO_PARK_FACTORS.get(h_team, 1.0))
            st.success(f"{h_team} 승률: {h_win:.1f}% | {a_team} 승률: {a_win:.1f}%")
    except Exception as e:
        st.error(f"오류: {e}")
