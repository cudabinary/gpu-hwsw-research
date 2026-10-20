# OLD_P2 동일 owned-output 서비스 비교 — 2026-10-21

상태: **고정 CPU 보완 실험 완료 / 원본 OLD_P2 서비스 누락 해소 / 보편적 RCC 우위는 입증되지 않음**.

`evidence/previous/SERVICE_BASELINE_GAP_AND_MINIMAL_RETEST.md`의 후속 검증이다. 과거 파일과 결과를 수정하거나 새 측정에 합산하지 않았다. 고정된 원본 Executor/Builder/P2/A를 사용했으며 RCC 알고리즘, API 및 MAIN 코드를 변경하지 않았다. 새 API 어댑터 자체의 서비스 성능은 이 실험으로 측정하지 않았다.

## 사전 고정과 정확성

`OLD_P2_PROTOCOL.json`과 소스·입력·바이너리 SHA를 성능 실행 전에 고정했다. LJ4096 original 및 기존 relabel fixture의 original source 목록, q8/q32를 그대로 사용했다. q는 첫 A 요청 뒤의 후속 요청 수다. 각 trial은 새로운 workspace/cache와 서로 독립적인 owned immutable 거리 배열을 반환한다. A는 변경하지 않은 frozen queue BFS이며 RCC에 필요한 완료 개수 계산·인증 갱신·복사도 서비스 시간에 포함된다.

성능 프로세스는 순차적으로 정확히 3개, 각 7라운드였다. 라운드마다 4개 경로의 순서를 회전·반전하고 두 번째 sweep은 정확한 역순으로 실행했다. 총 **672 trials**, **14,112 전체 배열 / 57,802,752 원소**가 독립 C++ deque BFS와 일치했다. 별도 진단 실행의 **336 배열 / 1,376,256 원소**도 독립 Python deque BFS와 일치했다. 이 수는 고유 그래프/요청 또는 독립 표본 수가 아니다. 재시도·warmup·새 GPU 실행은 0이다.

동일 session/round/graph/q의 두 sweep 비율을 기하평균하여 21개 primary block을 만들었다. 두 sweep을 독립 표본으로 세지 않았다. 고정 gate는 중앙 비율 <0.95, 17/21 이상 승리, 3개 session 중앙값 모두 <0.95다. 이는 사전 판정 규칙이며 신뢰구간이나 모집단 보장이 아니다.

## 서비스 결과

아래는 `total_ns`의 **RCC TABLE / 기준선** 짝 중앙 비율이다. 1보다 작으면 RCC TABLE이 빠르다. 서로 다른 조건의 시간 중앙값을 나눈 값이 아니다.

| Fixture | q | / PUSH_N | / OLD_P2 deferred | / OLD_P2 ready |
|---|---:|---:|---:|---:|
| LJ original | 8 | 0.8808 | 0.7815 | 1.3045 |
| LJ original | 32 | 0.7948 | 0.9327 | 1.0667 |
| LJ relabel | 8 | 0.8700 | 0.5108 | 0.6824 |
| LJ relabel | 32 | 0.7979 | 0.5440 | 0.5845 |

RCC TABLE은 네 조건에서 PUSH_N 및 OLD_P2 deferred 대비 고정 gate를 통과했다. 원본 LJ에서 RCC는 이미 reverse가 준비된 OLD_P2보다 q8 약30.45%, q32 약6.67% 오래 걸렸다. q8의 역방향 P2/RCC=0.7666은 gate를 통과했다. **q32의 역방향 P2/RCC=0.9375는 20/21 승리했지만 session별 0.9519/0.9208/0.9399여서 gate를 통과하지 못했다.** q32에서는 P2의 관측상 선두와 안정적 5% 우위 판정을 구별한다. RCC의 우위도 성립하지 않는다.

Relabel에서는 RCC가 ready P2에 대해서도 gate를 통과했다. 동일 그래프의 정점 번호/행 내 순서 대조이므로 독립적인 두 실세계 데이터셋의 재현으로 해석하지 않는다. 결과를 본 뒤 source·threshold·경로를 재선택하지 않았다. 현재 네 경로의 조건별 비교를 넘어 모든 그래프·공개 구현 대비 최강 승자를 선언할 수 없다. Direction+RIE의 과거 결과도 이 새 짝비교에 섞지 않았다.

## 전체 비용과 측정 경계

주 지표 `total_ns`는 과거 service와 같은 경계다. workspace/Executor/cache 할당부터 frozen A, 완료 인증·출력 복사, 필요한 deferred reverse 구축, q 후속 요청의 owned output 반환까지 포함한다. 입력 파일 읽기·oracle·출력 포인터 vector의 reserve·검증·해제·scope teardown은 제외한다. 시간 범위를 더 넓힌 지표도 같은 trial에서 직접 측정했다.

- `historical_prepare_ns`: ready reverse를 서비스 창 전에 실제 구축한 시간. ready가 이미 존재하는 조건의 서비스 시간과 새로 구축해야 하는 비용을 구별한다.
- `history_inclusive_ns`: 같은 trial의 `total_ns + historical_prepare_ns`로 계산한 합이며 연속 wall interval로 표시하지 않는다.
- `cleanup_window_ns`: 서비스 시작부터 검증·출력 해제·workspace/Executor/reverse/Builder 등의 정리 완료까지 연속 측정.
- `lifecycle_ns`: ready reverse 준비와 reserve까지 포함하여 함수 진입부터 모든 정리 완료까지 연속 측정. 최초 CSR 입력 생성·파일 로딩은 포함하지 않는다.

| LJ original | PUSH_N service (us) | RCC TABLE service (us) | P2 deferred service (us) | P2 ready service (us) | ready reverse 준비 (us) |
|---|---:|---:|---:|---:|---:|
| q8 | 511.414 | 450.256 | 567.106 | 347.289 | 214.292 |
| q32 | 2069.968 | 1659.363 | 1772.812 | 1548.056 | 218.916 |

이 표의 시간은 각 경로 원시 시간의 중앙값이며 위 짝비율과 직접 나눠 일치한다고 가정하지 않는다. 모든 조건의 A 완료·준비·검증·해제·연속 전체 비용·payload 중앙값은 `results/old_p2_service_20261021/COSTS.json`에 보존했다.

준비부터 정리까지 포함한 보조 지표 `lifecycle_ns`에서 RCC/P2 ready 비율은 original q8=0.7942, q32=0.9278이고 각각 같은 수치 gate를 통과했다. 이 지표에는 실험용 oracle 대조·identity 검사도 포함되므로 운영 서비스의 검증 없는 전체 지연으로 대체하지 않는다. **실제로 reverse가 이미 있으면 이 과거 비용을 다시 청구해 ready P2의 승리를 없애면 안 된다.** 신규 reverse 구축이 필요한 서비스와 기존 reverse를 재사용하는 서비스에 동일한 보편 승자를 강요하지 않는다.

TABLE payload는 n=4096에서 16,384 bytes이며 초기화·완료 A의 도달 수 계산·인증 table scan/write 및 이후 유지 작업은 이미 서비스 창에 포함된다. 유지 작업만의 독립 타이밍은 수집하지 않았으므로 별도 비용을 합성하지 않는다. 같은 frozen builder의 reverse/scratch 및 모든 owned output을 포함한 보수적 payload 상한은 모든 trial에서 32 MiB 이하였다. 각 worker의 실제 peak RSS는 20,052 KiB이며 payload 계수와 동일한 개념이 아니다. API 어댑터의 추가 CSR/출력 복사와 Trace=true 비용은 여전히 별도 미측정이다.

## 잡음·보존·호환성

같은 경로의 sweep1/sweep0 대조 16조건에서 중앙값은 약0.955~1.015였으나, raw 극값 중 LJ original q8 PUSH_N은 10.43배였다. 원시 이상치를 제거하지 않았고, 중간 결과를 보고 재실행하지 않았다. 짝비교·반대 순서와 3개 짧은 CPU session은 장기/독립 날짜 재현이나 통계적 불확실성 추정을 대신하지 않는다. 특히 original q32 ready의 엄격 gate 미통과를 보존한다.

`tools/audit_old_p2_service.py`는 전체 trial 행렬, 중복/누락, mirror 순서, 시간 경계, source/binary/protocol pin을 읽기 전용으로 감사해 PASS했다. vendor 37개 파일과 원본 폴더의 대응 37개 파일, MAIN의 tracked 219개 파일 SHA 및 HEAD/status가 보존 전후 동일했다. 원본 전체 폴더에 새 SHA 감사를 했다고 확대하지 않는다. 다른 worktree의 기존 미추적 파일과 RCC 시작 시 존재하던 미추적 run은 그대로 두었다.

공통 API1.0.0은 수정하지 않았다. 새 `tools/verify.py` 실행에서 **동일 MAIN client SHA `d5238d6b796509e64cab143ac5c1d75cdf368c4aba2f7325c6e309ec7483862e`**로 baseline/TABLE/LAST를 실제 교체하여 각각 2,111 배열을 통과했다. 취소·잘못된 graph/version·할당 실패·owned reader 수명 등의 기존 회귀검사도 포함된다. 새 서비스 배열 수와 이 호환성 배열 수를 독립 발견 횟수로 합산하지 않는다. GPU API backend는 계속 NOT_IMPLEMENTED_NOT_VERIFIED다.

## 판정과 재현

원본 P2 누락은 이 고정 CPU 조건에서 해결됐다. RCC는 신규 reverse 준비가 필요한 서비스에서 실효성이 있으나, 원본 LJ의 준비된 P2를 항상 이기지 못한다. 일반적 최강 SW 우위, API 어댑터 성능 우위, GPU 효과, 신규성 또는 독립 논문 기여는 확정하지 않는다. 새 알고리즘을 기본 RCC에 통합하지 않았다.

소스와 원시 CSV/명령/정확성 dump/비용/잡음/보존 감사는 이 체크포인트에 함께 보존한다. WSL에서 새 깨끗한 복사본의 빈 build/results 경로를 사용한다.

```text
python3 tools/run_old_p2_service.py prepare
python3 tools/run_old_p2_service.py benchmark
python3 tools/run_old_p2_service.py analyze
python3 tools/audit_old_p2_service.py
```

이미 `BENCHMARK_STARTED.json`이 있는 결과 디렉터리에서는 benchmark를 재실행하지 않는다. `analyze`와 audit는 기존 원시 자료를 읽을 뿐 새 성능 프로세스를 시작하지 않는다.

RCC-Scope·DistanceGuard ZIP 경로는 전달받았다. 사용자가 요청한 순서에 따라 이 OLD_P2 결과를 먼저 확정·커밋·보고한다. ZIP은 이 체크포인트에서 열거나 실행하지 않았으며 두 모듈을 추측해 구현하지 않았다. 후속 독립 감사의 수신/무결성/정확성/동일 서비스 기준선/고유 이득/선행연구 판정 전에는 기본 RCC에 통합하지 않는다.
