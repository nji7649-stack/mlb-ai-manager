import streamlit as st
import pandas as pd

# 1. 페이지 설정 (MLB 스타일 다크 모드)
st.set_page_config(page_title="KBO AI 통합 분석실 V3.0", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #f5f5f5; }
    .stMetric { background-color: #1a1c23; padding: 20px; border-radius: 8px; border-left: 5px solid #ff4b4b; }
    </style>
""", unsafe_allow_html=True)

# 업데이트 확인용 제목
st.title("⚾ KBO AI 통합 분석실 V3.0")
st.success("✅ 이 화면(V3.0)이 보인다면 코드 업데이트가 성공한 것입니다!")

PITCHER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=0&single=true&output=csv"
BATTER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=779417540&single=true&output=csv"

# 2. 강력한 무적 데이터 로더 (에러 원천 차단)
@st.cache_data(ttl=10)
def load_kbo_data(url):
    # 열 이름(헤더)을 무시하고 그냥 0, 1, 2, 3번 열로 통째로 가져옵니다.
    df = pd.read_csv(url, header=None, dtype=str)
    
    # 1번 열(선수명 위치)이 비어있거나 '선수명'이라는 한글 찌꺼기면 삭제합니다.
    df = df.dropna(subset=[1])
    df = df[df[1] != '선수명']
    return df

try:
    with st.spinner("구글 시트 연동 중..."):
        df_p = load_kbo_data(PITCHER_URL)
        df_h = load_kbo_data(BATTER_URL)

    # 3. 필요한 데이터에만 이름 강제 부여
  # 3. KBO 공식 스탯 이름으로 전체 매핑 (숫자 -> 야구 용어)
    pitcher_cols = {
        0: '순위', 1: '선수명', 2: '팀명', 3: 'ERA', 4: 'G', 5: 'W', 6: 'L', 
        7: 'SV', 8: 'HLD', 9: '승률', 10: 'IP', 11: 'H', 12: 'HR', 13: 'BB', 
        14: 'HBP', 15: 'SO', 16: 'R', 17: 'ER', 18: 'WHIP'
    }
    batter_cols = {
        0: '순위', 1: '선수명', 2: '팀명', 3: 'AVG(타율)', 4: 'G', 5: '타석', 6: '타수', 
        7: '득점', 8: '안타', 9: '2루타', 10: '3루타', 11: '홈런', 12: '루타', 13: '타점', 
        14: '희생번트', 15: '희생플라이'
    }

    df_p = df_p.rename(columns=pitcher_cols)
    df_h = df_h.rename(columns=batter_cols)

    # 4. MLB 스타일 탭 구성
    tab1, tab2, tab3 = st.tabs(["🔥 매치업 분석", "⚾ 투수 스탯", "🏏 타자 스탯"])

    with tab1:
        st.subheader("오늘의 승부 예측")
        teams = df_p['팀명'].dropna().unique().tolist()
        col1, col2 = st.columns(2)
        
        with col1:
            h_team = st.selectbox("🏠 홈 팀", teams, key='ht')
            h_p_list = df_p[df_p['팀명'] == h_team]['선수명'].dropna().tolist()
            h_p = st.selectbox("홈 선발투수", h_p_list if h_p_list else ["선수없음"], key='hp')
            
        with col2:
            a_teams = [t for t in teams if t != h_team]
            a_team = st.selectbox("✈️ 어웨이 팀", a_teams if a_teams else teams, key='at')
            a_p_list = df_p[df_p['팀명'] == a_team]['선수명'].dropna().tolist()
            a_p = st.selectbox("어웨이 선발투수", a_p_list if a_p_list else ["선수없음"], key='ap')

        if st.button("🚀 AI 승률 분석 실행", use_container_width=True):
            # 문자로 된 ERA를 숫자로 안전하게 변환
            h_era_str = df_p[df_p['선수명'] == h_p]['ERA'].iloc[0] if not df_p[df_p['선수명'] == h_p].empty else "4.50"
            a_era_str = df_p[df_p['선수명'] == a_p]['ERA'].iloc[0] if not df_p[df_p['선수명'] == a_p].empty else "4.50"
            
            try:
                h_era = float(h_era_str)
            except:
                h_era = 4.50
            try:
                a_era = float(a_era_str)
            except:
                a_era = 4.50
            
            # 방어율 0 보정
            h_era = 0.01 if h_era <= 0 else h_era
            a_era = 0.01 if a_era <= 0 else a_era
            
            h_prob = (a_era / (h_era + a_era)) * 100
            a_prob = 100 - h_prob
            
            st.markdown("---")
            m1, m2 = st.columns(2)
            m1.metric(f"{h_team} 승리 확률", f"{h_prob:.1f}%", f"선발 ERA: {h_era:.2f}")
            m2.metric(f"{a_team} 승리 확률", f"{a_prob:.1f}%", f"선발 ERA: {a_era:.2f}")

    with tab2:
        st.dataframe(df_p, use_container_width=True)
        
    with tab3:
        st.dataframe(df_h, use_container_width=True)

except Exception as e:
    st.error(f"데이터 오류 발생: {e}")
