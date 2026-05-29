import streamlit as st
import pandas as pd

# ... (디자인 설정은 동일) ...

try:
    df_p = load_data(PITCHER_URL) # 투수 데이터 로드
    df_h = load_data(BATTER_URL)  # 타자 데이터 로드
    
    tab1, tab2 = st.tabs(["📊 투수 매치업", "⚾ 타자 리포트"])
    
    with tab1:
        # (기존 투수 로직 유지)
        if st.button("🚀 투수 승부 예측"):
            h_era = pd.to_numeric(df_p[df_p['선수명']==h_p]['ERA'], errors='coerce').iloc[0]
            a_era = pd.to_numeric(df_p[df_p['선수명']==a_p]['ERA'], errors='coerce').iloc[0]
            st.metric("홈 승리 확률", f"{(a_era/(h_era+a_era))*100:.1f}%")

    with tab2:
        st.header("타자 분석")
        # 타자는 ERA가 없으므로 OPS를 사용
        h_hitter = st.selectbox("홈 타자 선택", df_h['선수명'])
        h_ops = pd.to_numeric(df_h[df_h['선수명']==h_hitter]['OPS'], errors='coerce').iloc[0]
        st.info(f"선택한 타자 {h_hitter}의 OPS: {h_ops:.3f}")
        st.dataframe(df_h, use_container_width=True)

except Exception as e:
    st.error(f"데이터 로드 오류: {e}")
