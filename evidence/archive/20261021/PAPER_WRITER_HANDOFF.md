# PAPER SCOUT / PAPER WRITER handoff

1. `RESEARCH_EVIDENCE_INDEX.json`에서 인덱스 범위·해시·원격 checkpoint를 확인한다.
2. 연구명/role/claim ID로 shard를 찾고 Evidence ID를 결정한다. 기록된 실행 Commit이 없으면 UNKNOWN으로 둔다.
3. 승인된 B2 읽기 키를 사용자 또는 Secret 저장소를 통해 확보한다. GitHub 읽기 권한이 B2 읽기 권한을 의미하지 않는다. 비밀값을 채팅·Git·명령행 인자·로그로 전달하지 않는다.
4. `tools/restore_evidence.py`, `tools/independent_restore.py`, `tools/restore_git_history.py`를 같은 폴더에 저장한다. 기존 Python 표준 라이브러리만 필요하다.
5. 새 빈 폴더로 필요한 Evidence ID를 복원하고 전체 SHA-256을 검사한다. 코드를 자동 실행하지 않는다.
6. 원본의 환경·정확성 계약·비교군·반복 수·측정 경계를 확인한 뒤 주장에 인용한다. 원격 원본을 읽을 권한이 없으면 열람 검증 완료로 표시하지 않는다.

운영용 업로드 키를 서비스에 배포하지 않는다. 서비스는 해당 Bucket·prefix 범위의 별도 읽기 전용 키를 사용한다. Master Key는 서비스에 제공하지 않는다. 키 만료는 저장된 객체를 삭제하거나 보관료를 중단하지 않는다.
