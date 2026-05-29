import streamlit as st
import pandas as pd

# 페이지 기본 설정
st.set_page_config(page_title="KBO AI 전용 분석실", layout="wide")
st.title("⚾ KBO AI 전용 분석실 (독립형)")

# 1. 데이터 입력부
st.sidebar.header("데이터 세팅")
h_url = st.sidebar.text_input("🔗 타자 CSV 주소 (웹 게시):")
p_url = st.sidebar.text_input("🔗 투수 CSV 주소 (웹 게시):")

# 2. 메인 분석 엔진
if h_url and p_url:
    try:
        # 데이터 로드
        df_h = pd.read_csv(h_url)
        df_p = pd.read_csv(p_url)
        
        # 데이터 확인 (데이터프레임 출력으로 로드 확인)
        st.success("✅ 데이터가 성공적으로 로드되었습니다.")
        
        # 팀 목록 추출
        teams = df_p['팀'].unique()
        
        # 선발 대진 선택
        col1, col2 = st.columns(2)
        with col1:
            h_team = st.selectbox("🏠 홈 팀", teams)
            h_p = st.selectbox("홈 선발 투수", df_p[df_p['팀'] == h_team]['이름'])
        with col2:
            a_team = st.selectbox("✈️ 원정 팀", [t for t in teams if t != h_team])
            a_p = st.selectbox("원정 선발 투수", df_p[df_p['팀'] == a_team]['이름'])
            
        # 시뮬레이션 버튼
        if st.button("🚀 승부 예측 시뮬레이션"):
            # 수치 추출
            h_era = df_p[df_p['이름'] == h_p]['ERA'].iloc[0]
            a_era = df_p[df_p['이름'] == a_p]['ERA'].iloc[0]
            h_ops = df_h[df_h['팀'] == h_team]['OPS'].mean()
            a_ops = df_h[df_h['팀'] == a_team]['OPS'].mean()
            
            # 승률 계산 엔진 (기본 모델)
            win_prob = (1 - (h_era / (h_era + a_era))) * 100
            
            st.markdown("---")
            st.subheader("📊 분석 결과 리포트")
            st.write(f"### 🏠 {h_team} 승리 확률: **{win_prob:.1f}%**")
            st.write(f"### ✈️ {a_team} 승리 확률: **{100-win_prob:.1f}%**")
            
    except Exception as e:
        st.error("데이터 로드 오류: 시트의 헤더(첫 줄)를 확인하세요.")
        st.write("요구되는 헤더: '팀', '이름', 'ERA', 'OPS'")
        st.write(f"오류 내용: {e}")
else:
    st.info("사이드바에 각각 CSV 주소를 입력하면 데이터 로드가 시작됩니다.")
