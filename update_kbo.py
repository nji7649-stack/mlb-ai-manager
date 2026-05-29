import os
import json
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

def fetch_and_update_kbo():
    # 1. 한국 시간 기준 오늘 날짜 구하기
    kst_now = datetime.utcnow() + timedelta(hours=9)
    date_string = kst_now.strftime('%Y-%m-%d')
    
    # 2. 네이버 스포츠 KBO 일정 API 호출
    url = f"https://api-gw.sports.naver.com/schedule/games?upperCategoryId=kbaseball&date={date_string}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://sports.naver.com/"
    }
    
    rows = [["경기시간", "상태", "홈팀", "홈선발", "원정팀", "원정선발", "게임ID"]]
    
    try:
        res = requests.get(url, headers=headers, timeout=10).json()
        games_data = res.get('result', {}).get('games', [])
        
        for game in games_data:
            if str(game.get('categoryId', '')).lower() != 'kbo':
                continue
                
            h_score = game.get('homeTeamScore', 0)
            a_score = game.get('awayTeamScore', 0)
            status_code = game.get('statusCode', '')
            
            if status_code == 'RESULT': status_str = f"종료 ({h_score}:{a_score})"
            elif status_code == 'STARTED': status_str = f"진행중 ({h_score}:{a_score})"
            elif status_code == 'CANCELED': status_str = "취소"
            else: status_str = "예정"
            
            game_time = game.get('gameStartTime') or game.get('gameTime') or 'TBD'
            if game_time != 'TBD' and len(game_time) >= 5:
                game_time = game_time[:5]
                
            h_starter = game.get('homeStarterName') or game.get('homeStarter') or '미발표'
            a_starter = game.get('awayStarterName') or game.get('awayStarter') or '미발표'
            
            rows.append([
                game_time, status_str, 
                game.get('homeTeamName', '홈팀'), h_starter,
                game.get('awayTeamName', '원정팀'), a_starter,
                game.get('gameId', '')
            ])
    except Exception as e:
        print(f"네이버 데이터 수집 실패: {e}")
        return

    # 3. 구글 시트 연동 및 인증 (깃허브 비밀 키 활용)
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # 깃허브 서버 환경에서는 환경변수에서 키를 읽고, 로컬 테스트 시에는 json 파일을 읽음
    if "GCP_SA_KEY" in os.environ:
        service_account_info = json.loads(os.environ["GCP_SA_KEY"])
        creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    else:
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
        
    client = gspread.authorize(creds)
    
    # 💡 본인의 구글 스프레드시트 ID를 입력하세요 (주소창의 d/와 /edit 사이 문자열)
    SPREADSHEET_ID = "1NHbRs99IGLHE8lsiPDRmlgnHYol6dR4OgGX3HMCiYm0" 
    
    try:
        doc = client.open_by_key(SPREADSHEET_ID)
        sheet = doc.worksheet("일정표")
        
        # 기존 내용 초기화 후 데이터 덮어쓰기
        sheet.clear()
        sheet.update(rows)
        print(f"{date_string} KBO 일정 구글 시트 동기화 완료!")
    except Exception as e:
        print(f"구글 시트 업데이트 실패: {e}")

if __name__ == "__main__":
    fetch_and_update_kbo()
