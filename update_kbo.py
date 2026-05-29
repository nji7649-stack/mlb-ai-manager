import os
import json
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

def fetch_and_update_kbo():
    kst_now = datetime.utcnow() + timedelta(hours=9)
    current_year = kst_now.year
    current_month = kst_now.month
    
    # 엑셀 첫 번째 줄(헤더) 미리 세팅
    all_rows = [["경기시간", "상태", "홈팀", "홈선발", "원정팀", "원정선발", "게임ID"]]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://sports.naver.com/"
    }
    
    # 🚀 핵심: 3월(개막월)부터 현재 월(5월)까지 한 달씩 쪼개서 반복 수집!
    for month in range(3, current_month + 1):
        # 해당 월의 1일
        start_date = f"{current_year}-{month:02d}-01"
        
        # 해당 월의 마지막 날짜 구하기 로직
        if month == 12:
            end_date = f"{current_year}-12-31"
        else:
            next_month_first_day = datetime(current_year, month + 1, 1)
            last_day = next_month_first_day - timedelta(days=1)
            end_date = last_day.strftime('%Y-%m-%d')
        
        # 네이버에 한 달 치씩 요청
        url = f"https://api-gw.sports.naver.com/schedule/games?upperCategoryId=kbaseball&categoryId=kbo&fromDate={start_date}&toDate={end_date}"
        
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
                
                # 수집한 데이터를 all_rows 장바구니에 계속 담기
                all_rows.append([
                    game_time, status_str, 
                    game.get('homeTeamName', '홈팀'), h_starter,
                    game.get('awayTeamName', '원정팀'), a_starter,
                    game.get('gameId', '')
                ])
        except Exception as e:
            print(f"네이버 데이터 수집 실패 ({start_date}월): {e}")

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
        print(f"시즌 전체 데이터 동기화 완료! (총 {len(all_rows)}경기)")
    except Exception as e:
        print(f"구글 시트 업데이트 실패: {e}")

if __name__ == "__main__":
    fetch_and_update_kbo()
