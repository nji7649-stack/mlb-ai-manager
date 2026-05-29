elif league == "KR 한국프로야구 (KBO)":
    st.title("⚾ KBO AI 감독 모드")
    
    # KBO 전용 데이터 로드
    try:
        df_p = load_data(PITCHER_URL) # 투수 데이터
        df_h = load_data(BATTER_URL)  # 타자 데이터
        
        tab1, tab2 = st.tabs(["📊 투수 매치업", "⚾ 타자 리포트"])
        
        with tab1:
            teams = df_p['팀명'].unique()
            c1, c2 = st.columns(2)
            with c1:
                h_t = st.selectbox("홈 팀", teams)
                h_p = st.selectbox("홈 선발", df_p[df_p['팀명']==h_t]['선수명'])
            with c2:
                a_t = st.selectbox("원정 팀", [t for t in teams if t != h_t])
                a_p = st.selectbox("원정 선발", df_p[df_p['팀명']==a_t]['선수명'])
            
            if st.button("🚀 승부 예측"):
                h_era = pd.to_numeric(df_p[df_p['선수명']==h_p]['ERA'], errors='coerce').iloc[0]
                a_era = pd.to_numeric(df_p[df_p['선수명']==a_p]['ERA'], errors='coerce').iloc[0]
                
                # ERA 기반 승률 예측 (데이터에 OPS가 없을 때를 대비)
                h_win = (a_era / (h_era + a_era)) * 100
                st.metric(f"홈 팀({h_t}) 승리 확률", f"{h_win:.1f}%")
        
        with tab2:
            st.header("타자 리포트")
            # OPS가 없어도 타율(AVG)과 장타율(SLG)이 있다면 활용 가능
            if 'OPS' not in df_h.columns and 'AVG' in df_h.columns:
                st.write("OPS 데이터가 없어 타율 기반 분석을 진행합니다.")
                st.dataframe(df_h[['선수명', '팀명', 'AVG', 'HR']], use_container_width=True)
            else:
                st.dataframe(df_h, use_container_width=True)

    except Exception as e:
        st.error(f"KBO 데이터 연결 오류: {e}")
