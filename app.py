import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="MLB AI 감독 모드", layout="wide")
st.title("⚾ MLB AI 감독 모드 V1.0 (자동 업데이트)")

# 1시간마다 메이저리그 공식 서버(statsapi)에서 최신 데이터를 알아서 가져옵니다.
@st.cache_data(ttl=3600)
def load_mlb_live_data():
    # MLB 공식 API 주소 (2026시즌 전체 타자 기록)
    url = "https://statsapi.mlb.com/api/v1/stats?stats=season&group=hitting&gameType=R&season=2026&playerPool=ALL&limit=1000"
    
    response = requests.get(url)
    data = response.json()
    
    splits = data['stats'][0]['splits']
    
    player_list = []
    for row in splits:
        stat = row['stat']
        player_list.append({
            '이름': row['player']['fullName'],
            '팀': row['team']['name'],
            '경기': stat.get('gamesPlayed', 0),
            '타수': stat.get('atBats', 0),
            '안타': stat.get('hits', 0),
            '홈런': stat.get('homeRuns', 0),
            '타점': stat.get('rbi', 0),
            '타율': stat.get('avg', '.000'),
            '출루율': stat.get('obp', '.000'),
            '장타율': stat.get('slg', '.000'),
            'OPS': stat.get('ops', '.000')
        })
        
    return pd.DataFrame(player_list)

st.write("🔄 메이저리그 공식 서버에서 오늘자 최신 데이터를 실시간으로 가져오는 중...")

try:
    df_hitter = load_mlb_live_data()
    st.success("✅ 실시간 데이터 자동 업데이트 완료! (매일 알아서 갱신됩니다)")
    
    # 순위를 홈런 순으로 정렬해서 보여주기
    df_hitter['홈런'] = pd.to_numeric(df_hitter['홈런'])
    df_hitter = df_hitter.sort_values(by='홈런', ascending=False).reset_index(drop=True)
    
    st.dataframe(df_hitter)
    
except Exception as e:
    st.error(f"데이터를 가져오지 못했습니다: {e}")
