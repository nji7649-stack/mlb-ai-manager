import streamlit as st
import pandas as pd

# 1. 페이지 설정 (MLB 스타일 다크 테마)
st.set_page_config(page_title="통합 AI 스포츠 분석실", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #f5f5f5; }
    .stMetric { background-color: #1a1c23; padding: 20px; border-radius: 8px; border-left: 5px solid #ff4b4b; }
    </style>
""", unsafe_allow_html=True)

# 2. 사이드바 구성 (MLB 분석실 완벽 재현)
st.sidebar.title("⚽ 통합 AI 스포츠 분석실")
st.sidebar.caption("클릭 한 번으로 리그를 전환하세요.")
st.sidebar.markdown("---")
league = st.sidebar.radio("분석할 리그를 선택하세요:", ["us 메이저리그 (MLB)", "KR 한국프로야구 (KBO)"], index=1)
st.sidebar.markdown("---")
st.sidebar.info("해외 야구는 크롬의 '한국어로 번역' 기능을 켜시면 더욱 쾌적하게 이용할 수 있습니다.")

# 3. 데이터 로드 함수 (캐시 초기화 및 중복 에러 원천 차단)
# 함수 이름을 fetch_kbo_data로 바꿔서 기존의 고장난 캐시를 완전히 피합니다.
@st.cache_data(ttl=600)
def fetch_kbo_data(url, tab_type):
    # header=None: 첫 줄을 제목으로 쓰지 않음 (중복 에러 방지)
    df = pd.read_csv(url, header=None, dtype=str)
    
    # 위치(숫자 인덱스)를 기반으로 우리가 필요한 3개만 이름표를 붙임
    if tab_type == 'pitcher':
        df = df.rename(columns={1: '선수명', 2: '팀명', 3: 'ERA'})
    else:
        df = df.rename(columns={1: '선수명', 2: '팀명'})
        
    # KBO 홈페이지 텍스트 찌꺼기(빈칸, '선수명'이라는 글자 자체) 완벽 제거
    df = df.dropna(subset=['선수명'])
    df = df[df['선수명'] != '선수명']
    df = df[df['선수명'] != 'None']
    df = df[df['팀명'].notna()]
    
    return df

# 4. KBO 모드 메인 화면
if league == "KR 한국프로야구 (KBO)":
    st.title("KR KBO AI 감독 모드 (배당 및 분석 탑재)")
    st.caption("🔄 한국프로야구 구단 데이터베이스 동기화 중...")

    PITCHER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=0&single=true&output=csv"
    BATTER_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS0Xtkb0DAS2LR3cl5kw5hwk8LgazAmdkDHeQPryXCliim7P1Cnzde-0hqfdti3SQvIzGpbqG-hJdHJ/pub?gid=779417540&single=true&output=csv"

    try:
        df_p = fetch_kbo_data(PITCHER_URL, 'pitcher')
        df_h = fetch_kbo_data(BATTER_URL, 'batter')

        # MLB 분석실과 완벽히 동일한 탭
        tab1, tab2, tab3 = st.tabs(["📅 매치업 및 실시간 라인업", "⚾ 전체 투수 스탯", "🏏 전체 타자 스탯"])

        with tab1:
            st.write("※ 팀 이름 옆 숫자는 'AI 자체 예상 배당(Implied Odds)'입니다.")
            
            teams = df_p['팀명'].unique().tolist()
            
            col1, col2 = st.columns(2)
            with col1:
                h_team = st.selectbox("홈 팀", teams, key='h_t')
                h_pitchers = df_p[df_p['팀명'] == h_team]['선수명'].tolist()
                h_p = st.selectbox("홈 선발투수", h_pitchers if h_pitchers else ["선수 없음"], key='h_p')

            with col2:
                a_teams = [t for t in teams if t != h_team]
                a_team = st.selectbox("어웨이 팀 (원정)", a_teams if a_teams else teams, key='a_t')
                a_pitchers = df_p[df_p['팀명'] == a_team]['선수명'].tolist()
                a_p = st.selectbox("어웨이 선발투수", a_pitchers if a_pitchers else ["선수 없음"], key='a_p')

            if st.button("🚀 AI 매치업 분석 및 배당 산출", use_container_width=True):
                # 안전한 ERA 변환 (문제가 있으면 4.50 기본값 처리)
                try:
                    h_era = float(df_p[df_p['선수명'] == h_p]['ERA'].iloc[0])
                except:
                    h_era = 4.50
                try:
                    a_era = float(df_p[df_p['선수명'] == a_p]['ERA'].iloc[0])
                except:
                    a_era = 4.50

                # 0점대 방어율 에러 방지
                h_era = 0.01 if h_era <= 0 else h_era
                a_era = 0.01 if a_era <= 0 else a_era

                # 확률 계산 및 배당(Odds) 산출
                h_prob = (a_era / (h_era + a_era))
                a_prob = 1.0 - h_prob
                
                h_odds = 1 / h_prob if h_prob > 0 else 0
                a_odds = 1 / a_prob if a_prob > 0 else 0

                st.markdown("---")
                m1, m2 = st.columns(2)
                m1.metric(f"🏠 {h_team} 승리 확률", f"{h_prob*100:.1f}%", f"AI 예상 배당: {h_odds:.2f}")
                m2.metric(f"✈️ {a_team} 승리 확률", f"{a_prob*100:.1f}%", f"AI 예상 배당: {a_odds:.2f}")

        with tab2:
            st.dataframe(df_p, use_container_width=True)

        with tab3:
            st.dataframe(df_h, use_container_width=True)

    except Exception as e:
        st.error(f"구글 시트 연동 오류: {e}")

# 5. MLB 모드 (기존 MLB 코드를 여기에 합치시면 됩니다)
elif league == "us 메이저리그 (MLB)":
    st.title("US MLB AI 감독 모드")
    st.info("MLB 분석 시스템이 여기에 표시됩니다.")
