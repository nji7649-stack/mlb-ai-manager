import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="KBO AI 분석실", layout="wide")

st.title("⚾ KBO AI 감독 모드 (통합 시트 연동)")
url = st.text_input("🔗 합쳐진 구글 시트 CSV 주소를 입력하세요:")

if url:
    try:
        df = pd.read_csv(url)
        # '분류' 열을 기준으로 투수와 타자 분리
        df_p = df[df['분류'] == '투수']
        df_h = df[df['분류'] == '타자']
        
        st.success("✅ 투수/타자 데이터 로드 완료!")
        
        h_team = st.selectbox("홈 팀", df_p['팀'].unique())
        a_team = st.selectbox("원정 팀", [t for t in df_p['팀'].unique() if t != h_team])
        h_p = st.selectbox("홈 선발", df_p[df_p['팀']==h_team]['이름'])
        a_p = st.selectbox("원정 선발", df_p[df_p['팀']==a_team]['이름'])
        
        if st.button("🚀 시뮬레이션 시작"):
            h_fip = df_p[df_p['이름']==h_p]['ERA'].iloc[0]
            a_fip = df_p[df_p['이름']==a_p]['ERA'].iloc[0]
            h_ops = df_h[df_h['팀']==h_team]['OPS'].mean()
            a_ops = df_h[df_h['팀']==a_team]['OPS'].mean()
            
            # 승률 계산 (기본 엔진)
            h_win = (1 - (h_fip / (h_fip + a_fip))) * 100
            st.success(f"{h_team} 승률: {h_win:.1f}% | {a_team} 승률: {100-h_win:.1f}%")
            
    except Exception as e:
        st.error(f"오류: 시트에 '분류', '팀', '이름', 'ERA', 'OPS' 열이 있는지 확인하세요. ({e})")
