import streamlit as st
import pandas as pd
from pybaseball import batting_stats, pitching_stats

st.set_page_config(page_title="MLB AI 감독 모드", layout="wide")
st.title("⚾ MLB AI 감독 모드 V1.0 (실시간 데이터 버전)")

# 1. 인터넷에서 실시간 MLB 데이터 긁어오기 (최초 1회만 실행되어 속도 유지)
@st.cache_data
def load_mlb_data():
    # 2026시즌 타자/투수 스탯 실시간 수집
    hitter_df = batting_stats(2026)
    pitcher_df = pitching_stats(2026)
    return hitter_df, pitcher_df

st.write("🔄 메이저리그 실시간 데이터를 불러오는 중입니다...")
try:
    df_hitter, df_pitcher = load_mlb_data()
    st.success("✅ MLB 실시간 데이터 연동 완료!")
    
    # 데이터 잘 나오는지 맛보기 화면
    st.subheader("📋 실시간 MLB 타자 기록 TOP 5 (WAR 기준)")
    st.dataframe(df_hitter[['Name', 'Team', 'G', 'HR', 'BA', 'WAR']].head(5))
    
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")