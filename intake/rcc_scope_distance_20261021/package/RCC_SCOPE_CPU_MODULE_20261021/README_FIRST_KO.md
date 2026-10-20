# RCC-Scope / DistanceGuard CPU 독립 연구 모듈

Codex가 진행 중인 Consumer-first+RCC/RIE 통합과 별개로, ChatGPT가 이 세션의 CPU에서 구현·검증한 모듈이다. 원격 PC, GPU, Nsight, sanitizer, 설치, 외부 업로드를 실행하지 않았다.

## 먼저 볼 결과
- `docs/INDEPENDENT_RESULTS_KO.md`: 긍정/부정 결과, 정확한 측정 경계.
- `docs/DESIGN_PROOF_KO.md`: 종료 증거와 공간/시간적 검사 제외 증거의 차이.
- `docs/PRIOR_WORK_KO.md`: 관련 고전 원리와 신규성 미입증.
- `results/GUARD_LOGICAL_READ_LEDGER.csv`: 추가 old-distance 읽기와 생략한 neighbor 검사.
- `results/VALIDATION_SUMMARY.json`: 실제 테스트 결과.

## 구현
- `include/closure_scope.hpp`: 완료된 과거 도달 집합을 Pull 후보 범위로 사용. exact regional indegree, bounded certificate publication, compaction 대조, WCC 대조.
- `include/distance_guard.hpp`: 직전 완료 거리 배열을 보유하고, 이번 레벨에 도달 불가능한 후보의 reverse 목록 검사를 생략. COUNT/CLOSURE/RADIUS/FRONTIER_MAX 차분 비교.
- `src/scope_probe.cpp`, `src/distance_probe.cpp`: 정확성·진단·한정 비계측 벤치마크·전체 출력 저장.
- `include/stop_bridge.hpp`, `vendor/consumer/*`: 기존 인계 source의 변경 없는 복사본. 새 모듈로 포장하지 않는다.

## 핵심 판정
실제 파생 Google/LiveJournal에서 RIE 이후에도 논리적 간선 검사량을 추가로 줄였다. 그러나 비용까지 포함한 실세계 CPU 성능 우위는 확보하지 못했다. 큰 시간 이득은 일부 합성 입력/요청 지역성에 한정된다. GPU 성능, 전체 최강 baseline 우위, HW 필요성 및 학술적 최초성은 미입증이다.

## 실행
`REPRODUCE.md`를 따른다. C++17 compiler와 Python3는 기존 설치본을 사용한다. pandas는 원시 CSV 재집계에만 사용하며 검사 자체는 Python standard library만으로 가능하다. 도구 설치 명령, GPU 호출 및 네트워크 실행은 없다.

Codex 진행 중 작업에 자동 반영하는 파일이 아니다. 다음 결과가 도착한 뒤 같은 입력/같은 backend에서 추가 가치만 비교할 독립 후보이다.
