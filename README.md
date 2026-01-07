# FTP 자동 이메일 발송 시스템 (FTP Auto-Mailer)

FTP 서버에서 특정 패턴(`RPA-성공률-YYYY-MM-dd-hh-mm.pdf`)의 최신 PDF 파일을 자동으로 찾아 다운로드하고, 이메일로 발송하는 자동화 시스템입니다. 웹 대시보드를 통해 설정을 관리하고 상태를 모니터링할 수 있습니다.

## 1. 주요 기능
- **자동 파일 검색**: FTP 서버에서 날짜 포맷을 분석하여 가장 최신 파일을 자동으로 선별합니다.
- **이메일 발송**: 다운로드한 파일을 첨부하여 지정된 수신자에게 이메일을 발송합니다.
- **웹 대시보드**: FTP 및 이메일 설정, 스케줄 시간을 웹 브라우저에서 간편하게 수정할 수 있습니다.
- **스케줄링**: 설정된 시간에 매일 자동으로 작업을 수행합니다.
- **수동 실행**: 대시보드의 "Run Now" 버튼을 통해 즉시 실행 테스트가 가능합니다.
- **로그 모니터링**: 실행 기록(성공/실패 여부)을 대시보드에서 실시간으로 확인할 수 있습니다.

## 2. 설치 방법 (Installation)

1. **Python 설치**: Python 3.x 버전이 설치되어 있어야 합니다.
2. **의존성 라이브러리 설치**:
   터미널에서 프로젝트 폴더로 이동 후 아래 명령어를 실행하세요.
   ```bash
   pip install -r requirements.txt
   ```

## 3. 실행 방법 (Usage)

1. **서버 실행**:
   ```bash
   python app.py
   ```
2. **대시보드 접속**:
   웹 브라우저를 열고 `http://localhost:5001` 주소로 접속합니다.

## 4. 설정 가이드 (Configuration)

대시보드 화면에서 아래 항목들을 설정하고 "Save Configuration"을 클릭하여 저장합니다.

### 4.1 FTP 설정
- **Host**: FTP 서버 주소 (예: 192.168.x.x)
- **Port**: FTP 포트 (기본: 21)
- **User**: FTP 접속 계정
- **Password**: FTP 접속 비밀번호
- **Target Dir**: 파일을 검색할 경로 (예: `/RPA_SUCCESS/`)

### 4.2 Email 설정
- **SMTP Server**: 이메일 서버 주소 (예: `smtp.office365.com` 또는 `smtp.gmail.com`)
- **SMTP Port**: 포트 번호 (일반적으로 587)
- **Sender Email**: 발송자 이메일 주소
- **Sender Password**: 발송자 이메일 비밀번호 (앱 비밀번호 사용 권장)
- **Recipients**: 수신자 이메일 주소 (콤마 `,`로 구분하여 여러 명 지정 가능)

### 4.3 Schedule 설정
- **Daily Run Time**: 매일 자동으로 실행될 시간 (24시간 형식, 예: `09:00`)

## 5. 문제 해결 (Troubleshooting)

- **로그 확인**: 대시보드 하단의 "Execution Logs"에서 에러 메시지를 확인하세요.
- **FTP 연결 실패**: 호스트 주소, 포트, 방화벽 설정을 확인하세요.
- **이메일 발송 실패**: 
  - SMTP 서버 및 포트가 정확한지 확인하세요.
  - Gmail 사용 시 "보안 수준이 낮은 앱 액세스" 허용 또는 앱 비밀번호 설정이 필요할 수 있습니다.
  - Office365 사용 시 TLS 설정이 필요할 수 있습니다 (현재 코드는 `starttls()` 지원).
- **파일 못 찾음**: 대상 폴더에 `RPA-성공률-YYYY-MM-dd-hh-mm.pdf` 형식의 파일이 존재하는지 확인하세요.

## 6. 파일 구조
- `app.py`: 웹 서버 및 스케줄러 메인 프로그램
- `ftp_manager.py`: FTP 연결 및 파일 다운로드 로직
- `email_manager.py`: 이메일 전송 로직
- `config.json`: 사용자 설정값 저장 파일
- `execution_log.txt`: 실행 로그 파일
- `templates/index.html`: 대시보드 화면
- `static/`: 스타일시트 및 스크립트

---
© 2026 Automail Project
