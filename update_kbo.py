import os
import json
import time
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

def fetch_and_update_kbo():
    kst_now = datetime.utcnow() + timedelta(hours=9)
    
    # 엑셀 첫 번째 줄(헤더) 미리 세팅
    all_rows = [["경기시간", "상태", "홈팀", "홈선발", "원정팀", "원정선발", "게임ID"]]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://sports.naver.com/"
    }
    
    # ✅ 시즌 개막일 세팅
    start_date = datetime(2026, 3, 1)
    
    print("데이터 수집을 시작합니다...")
    
    # 🚀 핵심: 3월 1일부터 오늘까지 '하루씩' 더해가며 빠짐없이 긁어오기!
    current_date = start_date
    while current_date <= kst_now:
        date_str = current_date.strftime('%Y-%m-%d')
        # 시작일과 종료일을 딱 하루(date_str)로 묶어서 네이버의 꼼수 원천 차단
        url = f"https://api-gw.sports.naver.com/schedule/games?upperCategoryId=kbaseball&categoryId=kbo&fromDate={date_str}&toDate={date_str}"
        
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
                
                all_rows.append([
                    game_time, status_str, 
                    game.get('homeTeamName', '홈팀'), h_starter,
                    game.get('awayTeamName', '원정팀'), a_starter,
                    game.get('gameId', '')
                ])
        except Exception as e:
            pass # 에러가 나더라도 로봇이 멈추지 않고 다음 날짜로 쿨하게 넘어감
            
        current_date += timedelta(days=1)
        time.sleep(0.1) # 💡 네이버가 공격(해킹)으로 오해하지 않게 0.1초씩 쉬어주기

    # 4. 모인 데이터를 구글 시트에 한 번에 쏘기
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    if "GCP_SA_KEY" in os.environ:
        service_account_info = json.loads(os.environ["GCP_SA_KEY"])
        creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    else:
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
        
    client = gspread.authorize(creds)
    SPREADSHEET_ID = "1NHbRs99lGLHE8IsiPDRmlgnHYol6dR4OgGX3HMCiYm0"
    
    try:
        doc = client.open_by_key(SPREADSHEET_ID)
        sheet = doc.worksheet("일정표")
        
        sheet.clear()
        sheet.append_rows(all_rows)
        print(f"시즌 전체 데이터 동기화 완료! (총 {len(all_rows)-1}경기)")
    except Exception as e:
        print(f"구글 시트 업데이트 실패: {e}")

if __name__ == "__main__":
    fetch_and_update_kbo()
