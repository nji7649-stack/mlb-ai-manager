import streamlit as st
import pandas as pd
import random
from collections import Counter

st.set_page_config(page_title="통합 AI 스포츠 분석실", layout="wide")

# 시뮬레이션 엔진
def run_kbo_simulation(h_fip, a_fip, h_ops, a_ops, park_factor):
    h_expected_runs = ((a_fip * (h_ops / 0.740)) + 0.2) * park_factor
    a_expected_runs = (h_fip * (a_ops / 0.740)) * park_factor
    h_wins = sum(1 for _ in range(10000) if random.gauss(h_expected_runs, 2.5) > random.gauss(a_expected_runs, 2.5))
    return (h_wins/10000)*100, 100 - (h_wins/10000)*100

st.title("⚾ KBO AI 감독 모드 (구글 시트 연동)")
url = st.text_input("🔗 구글 시트 게시 URL (CSV 주소):")

if url:
    try:
        # 데이터 로드
        df = pd.read_csv(url)
        st.write("로드된 데이터 컬럼:", df.columns.tolist()) # 어떤 이름으로 인식되는지 확인용
        
        # 데이터가 정상인지 확인
        if len(df) > 0:
            # 팀 리스트 추출
            teams = df['팀'].unique()
            h_team = st.selectbox("홈 팀", teams, key="h")
            a_team = st.selectbox("원정 팀", [t for t in teams if t != h_team], key="a")
            
            h_p = st.selectbox("홈 선발", df[df['팀']==h_team]['이름'], key="hp")
            a_p = st.selectbox("원정 선발", df[df['팀']==a_team]['이름'], key="ap")
            
            if st.button("🚀 시뮬레이션 시작"):
                h_fip = df[df['이름']==h_p]['ERA'].iloc[0]
                a_fip = df[df['이름']==a_p]['ERA'].iloc[0]
                h_ops = df[df['팀']==h_team]['OPS'].mean()
                a_ops = df[df['팀']==a_team]['OPS'].mean()
                
                h_win, a_win = run_kbo_simulation(h_fip, a_fip, h_ops, a_ops, 1.0)
                st.success(f"{h_team} 승률: {h_win:.1f}% | {a_team} 승률: {a_win:.1f}%")
        else:
            st.error("데이터가 비어있습니다. 구글 시트를 확인하세요.")
    except Exception as e:
        st.error(f"오류: {e}")
