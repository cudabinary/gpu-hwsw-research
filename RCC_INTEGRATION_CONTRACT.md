# RCC integration contract 1.0.0

정의: `api/rcc/v1.hpp`, 정수 ABI ID `0x00010000`. 현재 지원은 WSL Linux/g++ C++20 CPU 동적 모듈이다. CUDA 백엔드는 명시적으로 `UNSUPPORTED_BACKEND`를 반환한다. 이 계약을 CUDA 통합 가능으로 선언하지 않는다.

## 고정 의미

- `prepare(graph, options, seed_source=-1)`: 이전 바인딩을 해제하고 CSR 복사본·작업 공간·인증 저장소를 준비한다. seed 지정 시 완전한 BFS를 실행하여 인증을 생성한다. 비용은 prepare_ns에 포함한다.
- `can_apply(graph, source)`: 같은 immutable graph 객체·identity·version이고 source에 유효한 n보다 작은 도달 상한이 있는지 검사한다. 단순 n 상한은 유익한 RCC 인증으로 표시하지 않는다.
- `run(request)`: 완료 시 전체 거리 배열(-1=도달 불가)을 owned immutable Output으로 반환한다. 완성된 결과에 대해서만 인증을 갱신한다. 인증이 없거나 비활성화·캐시 할당 실패이면 정확한 Push+EARLY_N을 사용한다.
- `update(request)`: 해당 source의 완전한 BFS를 실행하여 상태를 갱신한다. 임의 외부 배열의 무료 인증 import가 아니다. run과 같은 계산·복사·publication 비용을 update_ns에 명시한다.
- `invalidate()`: 인증만 지운다. 기존 독자가 가진 출력은 계속 유효하다.
- `release()`: 모듈 소유 자원과 바인딩을 해제한다. 기존 출력의 graph 및 distance 수명은 독립적으로 유지된다.

같은 identity/version 문자열을 갖더라도 다른 Graph 인스턴스는 거부한다. 변경 그래프는 새 immutable 객체와 증가한 version으로 재준비해야 한다. 그래프 교체를 잘못된 인증을 사용하는 fallback으로 숨기지 않고 `INVALID_GRAPH`로 반환한다. 사용자는 새 그래프를 prepare한 뒤 정확한 기본 BFS로 실행할 수 있다.

## 실패·취소·publication

모듈은 단일 owner가 순차 호출한다. 다른 스레드는 이미 공개된 immutable Output만 읽는다. 임의 동시 cache writer나 lock-free publication은 지원하지 않는다. pre-cancel은 즉시 취소한다. row_budget 취소는 행 경계에서 검사하며 부분 결과/인증을 공개하지 않는다. 중단한 탐색 자체를 resume하지 않고 새 run으로 시작한다.

공개용 출력 메모리는 legacy executor의 인증 갱신 전에 할당한다. 그 후 배열 복사에는 추가 할당이 없다. 기존 executor도 완성 출력 할당 후에만 인증을 갱신한다. 캐시 할당 실패는 정확한 baseline으로 fallback하며, 필수 graph/workspace/output 메모리를 확보할 수 없으면 명시적 실패를 반환한다. OOM에서 결과가 없는데 성공했다고 하지 않는다.

## 교체·버전·수명

MAIN은 API header와 Graph 계약만 사용한다. `rcc_create(version)`와 `rcc_destroy()`를 가진 라이브러리를 선택한다. MAIN 코드는 모듈 내부 TABLE/LAST를 참조하지 않는다. baseline-1, rcc-table-20261021-v1, rcc-last-20261021-v1은 같은 API 구현이다. 이들은 RCC 알고리즘 v2/v3의 신규 연구 성과가 아니다.

현재 ABI는 같은 OS/아키텍처/compiler/C++ runtime 빌드 조합을 요구한다. 플랫폼을 넘는 안정 C ABI라고 주장하지 않는다. 알 수 없는 version은 factory가 거부한다. 동적 라이브러리는 프로세스가 끝날 때까지 매핑을 유지한다. Output의 shared_ptr deleter가 있을 수 있으므로 독자가 남은 상태에서 dlclose하지 않는다. 모듈 객체 release/destroy 후 독자 수명은 테스트하지만 arbitrary library unload는 지원하지 않는다.

미래 구현은 같은 계약과 회귀검사를 통과해야 한다. breaking change는 새 major/API ID와 명시적 migration adapter를 제공한다. 현재 v2 구현이 없으므로 미래 버전 호환성을 이미 검증했다고 주장하지 않는다.

## 측정 경계와 지원 한계

prepare_ns/run_ns/update_ns, 검사 간선, 캐시 payload, 추가 CSR payload, 출력 복사 원소 수를 반환한다. 새 어댑터는 원본 CSR→legacy CSR 복사와 owned output 한 번의 추가 복사를 수행하며 Trace=true 진단 경로를 사용한다. 임시 edge pair·workspace·allocator metadata·RSS를 모두 대표하는 메모리 계수는 아니다. 기존 ~0.80 CPU 비율은 이 어댑터의 성능으로 이전할 수 없다. 추가 어댑터 비용을 포함한 service 성능은 UNKNOWN이다.

CPU 호환성 결과와 CUDA 정적 빌드/과거 GPU 실행 결과는 별도 증거다. CUDA API 백엔드의 실제 교체·그래프 수명·할당 실패·취소 검증은 아직 완료되지 않았다.
