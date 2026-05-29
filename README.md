# 🎬 AV 웹 플랫폼 - 품번기 스타일 검색 사이트

현재 블로그 자동 발행 프로젝트의 AV 데이터베이스를 기반으로 한 **웹 인터페이스**입니다.
품번기(poomki.net) 사이트처럼 배우와 작품을 검색하고 찜할 수 있습니다.

## 📁 프로젝트 구조

```
av_web_platform/
├── app.py                 # Flask 메인 서버
├── requirements.txt       # 패키지 의존성
├── README.md             # 이 파일
├── data/
│   └── av_database.db    # SQLite 데이터베이스 (자동 생성)
├── templates/
│   ├── base.html         # 기본 템플릿
│   └── index.html        # 메인 페이지
└── static/
    ├── style.css         # 스타일시트
    └── script.js         # JavaScript
```

## 🚀 시작하기

### 1️⃣ 패키지 설치

```bash
cd C:\Users\윤재순\Desktop\blog-master-automation\av_web_platform
pip install -r requirements.txt
```

### 2️⃣ 서버 실행

```bash
python app.py
```

출력:
```
🚀 AV 웹 플랫폼 시작...
📍 http://localhost:5000
```

### 3️⃣ 브라우저에서 접속

```
http://localhost:5000
```

## ✨ 주요 기능

### 1. **배우 검색**
- 한글, 영어, 일본어로 배우명 검색
- 20명의 배우 정보 데이터베이스

### 2. **작품 검색**
- 품번(코드) 또는 제목으로 검색
- 평점 및 조회수 표시

### 3. **찜 목록 관리**
- ❤️ 찜하기 버튼으로 작품 저장
- 로컬 스토리지에 자동 저장
- 찜한 작품 모아보기

### 4. **통계 대시보드**
- 전체 배우 수
- 등록된 작품 수
- 평가된 작품 수

### 5. **다크 모드**
- 🌙 버튼으로 다크 모드 토글
- 로컬 스토리지에 저장

## 🔗 API 엔드포인트

### 검색
```
GET /api/search?q=배우명&type=all&page=1
```

### 배우
```
GET /api/actresses/<id>/works
```

### 작품 상세
```
GET /api/works/<id>
```

### 찜 목록
```
GET /api/favorites
POST /api/favorites (body: {work_id: 1})
DELETE /api/favorites (body: {work_id: 1})
```

### 통계
```
GET /api/stats
```

## 📊 데이터 소스

1. **배우 정보**: `../av_actress_db.py` (20명)
2. **작품 정보**: `../av_ranking_history.json` (자동 임포트)
3. **코드-배우 매핑**: `../av_scraper.py` (실시간 데이터)

## 🎨 UI 특징

- **품번기 스타일**: 핑크색 그래디언트 헤더
- **반응형 디자인**: 모바일/태블릿/데스크톱 최적화
- **스무스한 애니메이션**: 카드 호버, 스크롤 효과
- **통계 박스**: 실시간 통계 표시
- **찜하기 UI**: 하트 아이콘으로 직관적 조작

## 🔧 커스터마이징

### 색상 변경 (static/style.css)
```css
:root {
    --primary: #ff1493;      /* 핑크색 */
    --secondary: #00ced1;    /* 턱색 */
    --success: #20b2aa;      /* 초록색 */
}
```

### 포트 변경 (app.py 마지막 줄)
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # 5001로 변경
```

### 그리드 크기 (static/style.css)
```css
.grid-container {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
}
```

## 🐛 문제 해결

### 포트 이미 사용 중
```bash
# 다른 프로세스 확인
netstat -ano | findstr :5000

# 강제 종료
taskkill /PID <PID> /F
```

### 데이터베이스 초기화
```bash
# data 폴더 삭제
rmdir /s data

# 서버 재실행하면 자동 재생성
python app.py
```

### 배우 데이터 갱신
```bash
# app.py 재실행
python app.py
```

## 📝 파일 설명

### app.py
- Flask 서버 메인 파일
- API 엔드포인트 정의
- 데이터베이스 관리

### templates/base.html
- 모든 페이지의 기본 틀
- 헤더, 네비게이션, 푸터

### templates/index.html
- 메인 페이지
- 히어로 섹션, 최신 작품, 검색 섹션

### static/style.css
- 전체 스타일
- 다크 모드, 반응형 레이아웃
- 애니메이션 정의

### static/script.js
- 클라이언트 사이드 로직
- 테마 토글, 모달 관리

## 🔐 보안 주의사항

- 공개 정보만 사용
- 저작권 침해 X
- 부정확한 데이터는 제외

## 📄 라이센스

이 프로젝트는 개인용/교육용입니다.

## 🤝 연동

### 기존 블로그 시스템과의 연동
```python
# app.py의 load_sample_works()에서 자동으로 임포트
# av_ranking_history.json 활용
# av_actress_db.py 활용
```

### 새로운 작품 추가
```python
# 데이터베이스에 INSERT
cursor.execute('''
    INSERT INTO works (code, title, rating, description)
    VALUES (?, ?, ?, ?)
''', (code, title, rating, description))
```

## 💡 향후 개선 방향

- [ ] 사용자 계정 시스템
- [ ] 배우별 통계 차트
- [ ] 댓글 기능
- [ ] 평점 투표
- [ ] 고급 필터링
- [ ] CSV 내보내기
- [ ] 관리자 패널

---

**제작일**: 2026-05-29  
**버전**: 1.0  
**상태**: 🟢 운영 중
