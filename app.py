# ... (앞부분 동일) ...
elif league_choice == "🇰🇷 한국프로야구 (KBO)":
    st.header("🇰🇷 KBO AI 감독 모드 (구글 시트 연동)")
    url = st.text_input("🔗 구글 시트 게시 URL (CSV):")
    
    if url:
        try:
            df = pd.read_csv(url)
            # 데이터 로드 후 팀과 선수 선택
            st.success("✅ 데이터 로드 성공!")
            
            # 필수 데이터 확인
            if all(col in df.columns for col in ['팀', '이름', 'ERA', 'OPS']):
                h_team = st.selectbox("🏠 홈 팀", df['팀'].unique(), key="h")
                a_team = st.selectbox("✈️ 원정 팀", df['팀'].unique(), key="a")
                h_pitcher = st.selectbox("홈 선발", df[df['팀']==h_team]['이름'].tolist(), key="hp")
                a_pitcher = st.selectbox("원정 선발", df[df['팀']==a_team]['이름'].tolist(), key="ap")
                
                if st.button("🚀 KBO 시뮬레이션 시작"):
                    # 데이터 추출
                    h_data = df[df['이름'] == h_pitcher].iloc[0]
                    a_data = df[df['이름'] == a_pitcher].iloc[0]
                    h_ops = df[df['팀'] == h_team]['OPS'].mean()
                    a_ops = df[df['팀'] == a_team]['OPS'].mean()
                    
                    # 시뮬레이션 (함수 사용)
                    h_win, a_win, top3 = run_kbo_simulation(h_data['ERA'], a_data['ERA'], 5.0, 5.0, h_ops, a_ops, 4.5, 4.5, KBO_PARK_FACTORS.get(h_team, 1.0))
                    
                    st.success(f"{h_team} 승률: {h_win:.1f}% | {a_team} 승률: {a_win:.1f}%")
                    st.warning(f"🎯 예상 스코어 TOP 3: {top3}")
            else:
                st.error("데이터에 '팀', '이름', 'ERA', 'OPS' 열이 포함되어 있는지 확인하세요!")
        except Exception as e:
            st.error(f"주소 오류: {e}")
