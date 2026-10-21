# Backup and restore

`ROOT_RECOVERY_LOCATOR.json`은 인증된 원격 checkpoint의 ID와 SHA-256이다. 원래 절대 경로·Manifest는 Private B2 객체 본문에만 있다. URL에 토큰을 붙이거나 다운로드 공유 링크를 생성하지 않는다.

다른 컴퓨터에서는 기존 PC의 DPAPI 비밀 파일을 복사해 사용할 수 없다. 승인된 제한 읽기 키를 보안 입력으로 입력한다. 두 reader Python 파일을 같은 폴더에 두고 다음을 실행한다. `<…>` 값은 locator와 Evidence ID로 대체한다.

```text
python tools/restore_evidence.py --root-file-id <ID> --root-sha256 <SHA256> --evidence-id sha256:<FILE_SHA256> --destination <NEW_DIRECTORY> --prompt-key
```

전체 위치 복원은 `--evidence-id …` 대신 `--all`을 사용한다. 중복 제거된 네트워크 데이터와 원래 모든 위치를 실물로 만드는 디스크 용량은 다르다. 전체 복원은 약 122GB 이상의 빈 공간과 여유 공간이 필요하며 도구가 사전 검사한다. 기존 폴더에 덮어쓰지 않는다. POSIX 고유 파일명·대소문자 충돌이 있으면 native POSIX 파일시스템을 사용한다.

정확한 원시 바이트 복원과 운영용 SQLite 복원은 구분한다. 운영 DB를 열기 전 `SQLITE_APPLICATION_RESTORE_MAP.json`에 지정된 일관된 스냅샷으로 복원하고 옛 WAL/SHM을 함께 적용하지 않는다. 여러 DB의 전역 동시점 일관성은 미입증이다. 절대 링크를 원래 PC로 연결하지 않는다.

과금은 B2 사용량 기준이다. 2026-10-21 공식 공개 요금은 $6.95/TB/30일, 첫 10GB 무료이다. 약 51.7GB를 유지하면 월 약 $0.29(세금·환율 제외) 예상이다. 월평균 저장량 3배 초과 다운로드는 $0.01/GB이다. $5는 승인 예산이며 정액제가 아니다. 계정 일일 cap은 월 cap을 자동 보장하지 않는다. 이 세션 종료 후 상주 백업·과금 감시·자동 Git 동기화가 계속된다고 가정하지 않는다.

새 연구 세대는 기존 논리 SHA256→원격 extent를 재사용하고 신규 콘텐츠만 append하는 방식으로 확장한다. 현재 frozen-run 도구는 동일 Manifest 중단 재개를 지원하며, 다른 세대의 전체 파일을 다시 pack해 중복 저장하는 방식으로 확장하면 안 된다. 새 실험의 실행 코드 pin과 Manifest를 함께 보존한다.

공식 요금: https://www.backblaze.com/cloud-storage/pricing
