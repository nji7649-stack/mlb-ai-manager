import streamlit as st
import pandas as pd

st.set_page_config(page_title="MLB AI 감독 모드", layout="wide")
st.title("⚾ MLB AI 감독 모드 V1.0")

# 엑셀 파일 읽기 (수동 업로드 방식)
@st.cache_data
def load_mlb_data():
    # 파일 이름은 감독님이 올리실 이름과 맞춰주세요!
    hitter_df = pd.read_excel('MLB_타자_데이터.xlsx')
    return hitter_df

try:
    df_hitter = load_mlb_data()
    st.success("✅ MLB 데이터 연동 완료!")
    st.dataframe(df_hitter.head(5))
except FileNotFoundError:
    st.error("🚨 'MLB_타자_데이터.xlsx' 파일이 GitHub에 없습니다. 파일을 업로드해주세요!")
except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
