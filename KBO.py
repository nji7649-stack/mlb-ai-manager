import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="통합 AI 스포츠 분석실", layout="wide")

# 데이터 로드 함수 (공통)
@st.cache_data
def load_data(url):
    df = pd.read_csv(url)
    # 헤더가 섞이는 문제를 방지하기 위해 1행을 강제로 헤더로 지정
    df.columns = df.iloc[0]
    return df[1:]

# 1. 사이드바 통합
st.sidebar.title("통합 AI 스포츠 분석실")
league = st.sidebar.radio("분석할 리그를 선택하세요:", ["MLB", "KBO"])

# 2. MLB 모드
if league == "MLB":
    st.title("US MLB AI 감독 모드")
    # 기존 MLB 분석실 코드 영역
    st.write("MLB 분석 대시보드가 여기에 표시됩니다.")

# 3. KBO 모드 (오류 해결 완료)
elif league == "KBO":
    st.title("⚾ KBO AI 감독 모드 V2.5")
    
    # 여기서 주소를 직접 관리
    PITCHER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=0&single=true&output=csv"
    
    try:
        df = load_data(PITCHER_URL)
        
        # '팀명'이라는 열 이름이 없으면 첫 번째 열을 강제로 팀명으로 지정
        # (감독님 시트 헤더가 바뀌어도 코드가 유연하게 작동하게 함)
        if '팀명' not in df.columns:
            df.rename(columns={df.columns[2]: '팀명', df.columns[1]: '선수명', df.columns[3]: 'ERA'}, inplace=True)
            
        tab1, tab2 = st.tabs(["📊 투수 매치업", "⚾ 타자 리포트"])
        
        with tab1:
            teams = df['팀명'].unique()
            col1, col2 = st.columns(2)
            with col1:
                h_team = st.selectbox("홈 팀", teams)
                h_p = st.selectbox("홈 선발", df[df['팀명']==h_team]['선수명'])
            with col2:
                a_team = st.selectbox("원정 팀", [t for t in teams if t != h_team])
                a_p = st.selectbox("원정 선발", df[df['팀명']==a_team]['선수명'])
            
            if st.button("🚀 승부 예측"):
                h_era = pd.to_numeric(df[df['선수명']==h_p]['ERA'], errors='coerce').iloc[0]
                a_era = pd.to_numeric(df[df['선수명']==a_p]['ERA'], errors='coerce').iloc[0]
                m1, m2 = st.columns(2)
                m1.metric("홈 승리 확률", f"{(a_era/(h_era+a_era))*100:.1f}%")
                m2.metric("원정 승리 확률", f"{(h_era/(h_era+a_era))*100:.1f}%")
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}. 시트의 열 이름을 확인하세요.")
