import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="KBO AI 감독 모드", layout="wide")

st.title("⚾ KBO AI 감독 모드 (구글 시트 연동)")
# 탭 정보를 포함한 URL을 받기 위해 시트 주소를 입력받습니다.
url = st.text_input("🔗 구글 시트 게시 URL (CSV):")

if url:
    try:
        # 투수/타자 탭을 각각 읽어옵니다 (URL 끝 gid를 수정하여 각 탭 호출)
        h_url = url.replace("gid=0", "gid=1756540608") # 타자 탭의 gid (감독님 시트 확인 필요)
        p_url = url.replace("gid=0", "gid=1334812365") # 투수 탭의 gid
        
        df_h = pd.read_csv(h_url)
        df_p = pd.read_csv(p_url)
        
        st.success("✅ 데이터 로드 완료!")
        
        # 데이터 분석
        teams = df_p['팀'].unique()
        h_team = st.selectbox("홈 팀", teams, key="h")
        a_team = st.selectbox("원정 팀", [t for t in teams if t != h_team], key="a")
        
        h_p = st.selectbox("홈 선발", df_p[df_p['팀']==h_team]['이름'], key="hp")
        a_p = st.selectbox("원정 선발", df_p[df_p['팀']==a_team]['이름'], key="ap")
        
        if st.button("🚀 시뮬레이션 시작"):
            # 감독님 시트의 'ERA'와 'OPS'를 직접 사용
            h_fip = df_p[df_p['이름']==h_p]['ERA'].iloc[0]
            a_fip = df_p[df_p['이름']==a_p]['ERA'].iloc[0]
            h_ops = df_h[df_h['팀']==h_team]['OPS'].mean()
            a_ops = df_h[df_h['팀']==a_team]['OPS'].mean()
            
            h_win = (1 - (h_fip / (h_fip + a_fip))) * 100
            st.success(f"결과: {h_team} 승률 {h_win:.1f}% vs {a_team} 승률 {100-h_win:.1f}%")
            
    except Exception as e:
        st.error(f"데이터 로드 실패. 시트의 첫 줄에 '팀', '이름', 'ERA', 'OPS' 헤더가 있는지 확인하세요. 에러: {e}")
