# Jarvis 통합 현황 — 연구 분리 checkpoint

## 판정

연구 환경은 MAIN GPU HW–SW와 독립 RCC SW 트랙으로 분리했다. 기존 REDESIGN_PROBLEM 및 강한 기준선 검증 필요성을 변경하지 않는다. 새로운 알고리즘이나 성능 실험을 수행하지 않았다.

## 원본·Git 보존

기존 task 폴더는 Git 저장소가 아니었다. 등록돼 있던 ‘논문’과 ‘논문 소스’는 master라는 unborn branch만 있고 커밋·remote·tracked file이 없었다. 이들 이름과 상태를 변경하지 않았고 .git 메타데이터도 별도 복사했다.

연구 파일10,270개를 별도 ZIP으로 보존하고 CRC·SHA를 확인했다. 대형 trace 포함1.35GB 보존본은 로컬 checkpoint에 남긴다. 새 전용 Git 저장소는 사용자가 만든 빈 private remote의 기본 이름 main으로 시작했다. 기존 Git 이력을 덮어쓰거나 force push하지 않았다.

## 원시 증거 대조

이전 CPU correctness JSON: 비교240,415 / assertion988,173, Python배열1,836. 이전 GPU의 12 stdout 로그는 receipt와 동일하고 종료 동기화 표식도 있다. SHA pin 전부 일치. BFS36/취소12/kernel232,14.907초,최고44°C,최저여유6878MiB. 이번에 다시 GPU를 실행한 수치가 아니다.

LJ q32 Push+RCC TABLE 약0.79991 대 Push+EARLY_N. Direction+RIE 뒤 추가 검사 생략0. 원본 OLD_P2의 같은 전체 service 계약 측정 누락 때문에 최종 strongest 승자 UNKNOWN. 이 누락을 RCC 우선 과제로 인계했다.

## 공통 API와 실제 교체

API1.0.0은 lifecycle, identity/version, 실패/fallback, 소유 결과 수명을 정의한다. MAIN client는 RCC 구현을 include하지 않는다. 같은 실행 파일에 baseline/TABLE/LAST 라이브러리를 바꿔 넣었다. 각 모듈512 exhaustive 그래프·중복 간선·lifecycle·실제4입력에 대해2111전체 배열 비교 PASS, 세 모듈총6333배열. assertion 수에는 입력 edge parsing도 포함되므로 독립 BFS 개수로 인용하지 않는다.

캐시 없음/비활성화/할당 실패 fallback, 잘못된 graph instance/identity/version 거부, invalidation, row-budget/pre-cancel, 실패 시 인증 유지, 반복 수명, immutable 독자, version mismatch 거부를 검사했다. 필수 출력 할당 실패는 오류를 반환하고 부분 결과를 공개하지 않는다. fault injection은 OS OOM 실측이 아니다.

이번 새 API는 CPU 기능 호환성만 통과했다. 어댑터의 추가 CSR 복사·출력 복사·진단 계수 비용을 포함한 성능은 UNKNOWN이다. CPU 자료를 GPU 성능 예측으로 사용하지 않는다. CUDA API backend는 미구현/미검증이며 UNSUPPORTED를 반환한다. **사용자의 GPU별 실제 교체 호환성 조건은 아직 충족하지 못했다.** 과거 GPU pilot와 현재 정적 빌드를 대신 제시하지 않는다.

## 연구 트랙

MAIN: 구조적 GPU instruction/SM/cache/DRAM/launch 비용과 knowledge/control/timing gap. RCC 자체의 새 알고리즘은 여기서 개발하지 않는다.

RCC: 먼저 OLD_P2 전체 service baseline gap을 해소한다. 기존 RCC replaceability를 유지하고 신규성을 별도 판단한다. 이전 도달 범위로 검사 영역 제한은 DISCOVERY이며 기본 구현에 병합하지 않았다. PAPER_CANDIDATE/PAPER_READY 조건은 충족되지 않았다.

## 안전 및 후속

다른 연구 작업·GPU 프로세스를 종료하지 않았다. 새로운 GPU query/kernel/Nsight/sanitizer/설치/유료 실행은0. 기존 승인 플래그를 재활성화하지 않았다. CUDA 공통 API 실제 검증은 backend 구현과 별도 고정 계획·fresh 안전 검사가 필요하다. `GPU_COMPATIBILITY_GATE.md`에 미완료 항목을 명시했다.

GitHub 인증은 Git Credential Manager의 브라우저 절차를 사용했다. API로 cudabinary/비공개/Push권한을 확인했고 초기 ls-remote는 성공하며 refs가 없었다. 토큰은 파일/채팅에 저장하지 않았다. 최종 브랜치별 SHA·원격 일치는 외부 DELIVERY_STATUS.json 영수증에 보존한다.
