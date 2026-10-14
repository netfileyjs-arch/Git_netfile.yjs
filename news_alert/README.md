# 뉴스 키워드 알림 (PC 알림)

대한민국 뉴스 중 지정한 키워드가 **모두** 들어간 기사(제목+본문)가 있으면 매일 아침 9시에 PC 알림으로 제목을 보여줍니다.
뉴스 출처는 Google 뉴스 한국판 RSS로, 언론사 기사만 검색됩니다 (블로그·카페·커뮤니티 글 제외). API 키는 필요 없습니다.

## 설치 (Windows)

1. [Python](https://www.python.org/downloads/) 설치 (설치 화면에서 **Add python.exe to PATH** 체크)
2. 이 `news_alert` 폴더를 PC에 복사 (예: `C:\news_alert`)
3. 그 폴더에서 PowerShell을 열고:
   ```powershell
   pip install -r requirements.txt
   python news_alert.py --test        # 알림이 뜨는지 확인
   powershell -ExecutionPolicy Bypass -File .\install_windows_task.ps1   # 매일 9시 등록
   ```

## 설정 (`config.json`)

| 항목 | 설명 |
|---|---|
| `keywords` | 찾을 키워드 목록 |
| `match` | `"all"`(기본): 모든 키워드가 **함께** 들어간 기사만 / `"any"`: 키워드 중 하나라도 들어간 기사 (키워드별로 따로 검색) |
| `search_in` | `"content"`(기본): 제목+본문에서 검색 (Google 뉴스 검색 결과 기준) / `"title"`: 제목에 키워드가 있는 기사만 |
| `lookback` | 검색 기간 (`1d` = 최근 24시간, `12h` 등) |
| `max_titles_in_popup` | 알림창에 보여줄 제목 수 (나머지는 "…외 N건") |
| `max_items_per_keyword` | 키워드당 최대 기사 수 |
| `open_report_in_browser` | 기사가 있으면 전체 목록(`report.html`, 링크 포함)을 브라우저로 열기 |
| `skip_already_notified` | 이미 알림 받은 기사는 다시 알리지 않기 |

기사가 없으면 알림을 띄우지 않습니다. 실행 기록은 `news_alert.log`에 남습니다.

## 참고

- PC가 9시에 꺼져 있었다면 켜진 뒤 바로 한 번 실행됩니다.
- 시간을 바꾸려면 `install_windows_task.ps1`의 `$Time`을 고치고 다시 실행하세요.
- 등록 해제: `Unregister-ScheduledTask -TaskName "NewsKeywordAlert" -Confirm:$false`
