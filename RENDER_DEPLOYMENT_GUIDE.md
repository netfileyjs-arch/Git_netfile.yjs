# Render 배포 가이드 (AV Web Platform)

## 단계 1: Render 계정 생성 및 연결

### 1.1 Render 가입
1. https://render.com 에서 **Sign up** 클릭
2. GitHub 계정으로 로그인 선택 (권장)
   - GitHub 계정: netfileyjs-arch
   - 이메일: netfile.yjs@gmail.com
3. Render의 GitHub 접근 권한 승인

### 1.2 GitHub 저장소 연결
- Render 대시보드에서 GitHub 계정 연결 완료
- 저장소: `netfileyjs-arch/Git_netfile.yjs`

---

## 단계 2: Web Service 생성

### 2.1 새 Web Service 만들기
1. Render 대시보드 → **New +** → **Web Service**
2. 저장소 선택: `Git_netfile.yjs`
3. **Connect** 클릭

### 2.2 서비스 설정

| 항목 | 값 |
|------|-----|
| **Name** | `av-web-platform` |
| **Region** | `Singapore` (또는 `Oregon`) |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app` |

### 2.3 Environment Variables (선택사항)
- **FLASK_ENV**: `production`
- **SECRET_KEY**: (자동 생성됨)

### 2.4 배포 설정
- **Free tier** 선택
- **Auto-Deploy** 활성화 (GitHub push 시 자동 배포)

---

## 단계 3: 배포 확인

### 3.1 배포 로그 확인
1. Render 대시보드에서 서비스 선택
2. **Logs** 탭에서 배포 진행 상황 확인
3. "All systems operational" 메시지 대기

### 3.2 라이브 URL 확인
- 형식: `https://av-web-platform.onrender.com`
- Render 대시보드 상단에 URL 표시됨

### 3.3 사이트 접속 테스트
```
https://av-web-platform.onrender.com
```
- 홈페이지가 정상 로드되는지 확인
- 배우 검색 기능 테스트
- 관리자 페이지 접속 (localhost 제한이므로 로컬에서만 가능)

---

## 단계 4: 주요 설정 및 제한사항

### 4.1 Free Tier 제약사항
- **자동 종료**: 15분 간 요청 없으면 자동 sleep
  - 다시 요청하면 재시작 (10-30초 소요)
- **메모리**: 512 MB 제한
- **저장소**: 휘발성 (재시작 시 초기화)
  - database 파일(av_database.db)이 초기화될 수 있음

### 4.2 database 문제 해결
- SQLite database는 Render 내부에서 유지되지 않음
- 해결 방법:
  1. **PostgreSQL** 사용 (Render 무료 tier 제공)
  2. 또는 Render에서 제공하는 **Disk** 마운트 사용

### 4.3 데이터 지속성 설정 (권장)
1. Render 서비스에서 **Disk** 추가
2. **Mount Path**: `/data`
3. 앱에서 DB를 `/data/av_database.db`로 지정

---

## 단계 5: 자동 배포 설정

### 5.1 GitHub와 Render 연동
- GitHub에 push하면 자동으로 Render에 배포됨
```bash
git push origin main
```

### 5.2 배포 모니터링
1. Render 대시보드 → Logs
2. 빌드 및 배포 상황 실시간 확인

---

## 단계 6: 도메인 설정 (선택사항)

### 6.1 Render 제공 도메인
- 기본: `av-web-platform.onrender.com`

### 6.2 커스텀 도메인
1. Render 서비스 설정 → **Settings**
2. **Custom Domains** → **Add Domain**
3. 도메인 입력 및 DNS 설정 (생략 가능)

---

## 배포 체크리스트

- [ ] Render 계정 생성 및 GitHub 연결
- [ ] `av-web-platform` Web Service 생성
- [ ] 빌드 및 시작 명령어 설정
- [ ] 배포 완료 확인
- [ ] 라이브 URL에서 사이트 접속 확인
- [ ] 배우 검색 기능 테스트
- [ ] 배너 표시 확인
- [ ] 자동 배포 활성화 확인

---

## 배포 후 주의사항

1. **Free Tier 유지**
   - 월 750 시간 무료 (충분함)
   - 15분 자동 sleep은 정상 동작

2. **데이터 초기화 방지**
   - Disk를 마운트하여 데이터 지속성 확보

3. **성능 최적화**
   - 필요시 Paid Tier로 업그레이드
   - Pro: $7/월 (항상 켜짐, 더 많은 리소스)

---

## 문제 해결

### 503 Service Unavailable
- 원인: 앱이 crashed 상태
- 해결: Render 대시보드 Logs에서 에러 확인

### Database Lock 에러
- 원인: SQLite 동시 접근
- 해결: PostgreSQL 사용

### 자동 배포 안 됨
- 확인: Render Settings에서 GitHub 연결 상태
- 재연결: Disconnect 후 다시 Connect

---

## 다음 단계 (Phase 3)

1. system_config.json 최종 업데이트
2. 배포 정보 기록
3. 파일 보호 설정
