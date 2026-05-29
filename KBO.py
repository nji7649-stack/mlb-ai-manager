import streamlit as st
import pandas as pd

# UI 설정
st.set_page_config(page_title="KBO AI 통합 분석실 V2.0", layout="wide")

# 스타일 적용 (다크 모드 스타일링)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stMetric { background-color: #1e1e1e; padding: 20px; border-radius: 10px; border-left: 5px solid #deff9a; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚾ KBO AI 통합 분석실 V2.0")

# 데이터 입력
csv_url = st.sidebar.text_input("🔗 구글 시트 웹 게시 주소:")

if csv_url:
    try:
        df = pd.read_csv(csv_url)
        df_p = df[pd.to_numeric(df['순위'], errors='coerce').notnull()] # 투수 데이터
        df_h = df[pd.to_numeric(df['순위'], errors='coerce').isna()]    # 타자 데이터
        
        teams = df_p['팀명'].unique()
        
        col1, col2 = st.columns(2)
        with col1:
            h_team = st.selectbox("🏠 홈 팀", teams)
            h_p = st.selectbox("홈 선발", df_p[df_p['팀명'] == h_team]['선수명'])
            # 팀 타선 평균 OPS 계산 (간이 모델)
            h_ops = df_h[df_h['팀명'] == h_team]['OPS'].mean() if 'OPS' in df_h.columns else 0.750
        with col2:
            a_team = st.selectbox("✈️ 원정 팀", [t for t in teams if t != h_team])
            a_p = st.selectbox("원정 선발", df_p[df_p['팀명'] == a_team]['선수명'])
            a_ops = df_h[df_h['팀명'] == a_team]['OPS'].mean() if 'OPS' in df_h.columns else 0.750

        if st.button("🚀 정밀 분석 실행"):
            h_era = float(df_p[df_p['선수명'] == h_p]['ERA'].iloc[0])
            a_era = float(df_p[df_p['선수명'] == a_p]['ERA'].iloc[0])
            
            # 투타 통합 승률 모델 (ERA와 OPS를 가중치 결합)
            # 수식: (공격력 - 상대 투수력) / 합계 보정
            score_h = (h_ops * 10) - h_era
            score_a = (a_ops * 10) - a_era
            win_prob = (score_h / (score_h + score_a)) * 100
            
            st.markdown("---")
            m1, m2 = st.columns(2)
            m1.metric("홈 팀 승리 확률", f"{win_prob:.1f}%")
            m2.metric("원정 팀 승리 확률", f"{100-win_prob:.1f}%")
            
            st.write(f"📊 상세: 홈 OPS {h_ops:.3f} | 원정 선발 ERA {a_era:.2f}")

    except Exception as e:
        st.error(f"데이터 로드 실패: 시트 구조를 확인하세요. ({e})")
