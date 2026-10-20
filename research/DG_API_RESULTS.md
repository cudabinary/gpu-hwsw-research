# DistanceGuard API 1.0.0 최종 실험 검증 — 2026-10-21

**CPU API 호환성·검사한 전체 거리 정확성 PASS. 합성 ready 한 조건의 고유 이득 유지. 기본 RCC 통합 HOLD.** Google/LJ에서는 강한 기준선과 matched ablation을 함께 이기는 실용적 전체시간 우위를 확보하지 못했다. 추가 최적화 반복·MAIN 변경·자동 병합·GPU 실행은 하지 않았다.

## 고정 입력과 실제 MAIN

작업은 `research/rcc` worktree에서만 수행했다. 이전 독립 감사 commit `5c489f154d4c7c0bb587972ee307fcaf03a313e2`의 202개 artifact와 OLD_P2 commit `1a79b1048cc639c3c23f1000373c3ed6e10bbf7c`의 60개 artifact를 commit blob bytes/SHA256으로 확인했다. 기존 intake/results/source는 현재 파일과도 일치했다. 이전 보고서·CSV·ZIP·vendor를 수정하지 않았다. 입력 ZIP SHA256은 계속 `c1ba7f6c6d595f84081dceb66052d76344a6685b902ccccde7e6e7c9f0a51d7c`이며 92개 manifest 대상 파일이 일치한다.

**실행한 기존 `build/main_client` SHA256:**

```text
d5238d6b796509e64cab143ac5c1d75cdf368c4aba2f7325c6e309ec7483862e
```

RCC와 MAIN worktree의 기존 MAIN executable이 같은 SHA이며 실행 전후 불변이다. `libgraph.so`도 양쪽에서 `11f75e3661fbd41a1e823d0f17f4c63e0007155d02eff6e02a23833873d5d795`로 불변이다. 기존 baseline/TABLE/LAST DSO, API header, 기본 `src/cpu_module.cpp`, MAIN client source를 고정했다. **MAIN 소스·바이너리를 수정하거나 재빌드하지 않았다.** `tools/verify.py`는 MAIN을 재빌드하므로 이번에는 호출하지 않고 기존 executable을 직접 실행했다. 공통 API 변경도 없다.

MAIN HEAD `94a041c0bf300cd684ec1402244470dac499e55e`, tracked 219개 파일과 status, 원본 연구 대응 37개·vendor 37개를 전후 대조했다. 기존 MAIN의 미추적 `analysis/`, `evidence/audit/ORIGINAL_PRESERVATION_FINAL.json` 및 RCC의 이전 미추적 run도 유지했다. 상세는 `results/dg_api_20261021/{PROTECTED,FROZEN,PREVIOUS}_{BEFORE,AFTER}.json`이다.

## 구현과 계약

새 코드는 `research/dg_api_module.cpp`, `dg_api_kernel.hpp`, `dg_api_factory.cpp`에만 독립 구현했다. 패키지의 DistanceGuard loop를 포팅하고 기존 frozen Builder/consumer/stop_bridge를 사용한다. API `0x00010000`, `rcc_create/rcc_destroy`, CPU backend만 지원한다. 기본 RCC factory나 로딩 기본값에 연결하지 않았다.

완료된 API-owned immutable Output을 다음 인증의 이전 거리 배열로 보유한다. public output은 탐색·인증 publication 전에 할당하고, 완료 시 workspace에서 한 번 복사한 뒤 non-allocating shared ownership 교체로 인증을 공개한다. retained distance payload 4n bytes를 cache limit에 청구한다. 독자가 보유한 결과는 다음 run/invalidate/release/destroy 후에도 살아 있다. 라이브러리는 프로세스 종료까지 매핑을 유지한다.

같은 Graph 인스턴스·identity·version에만 인증을 적용한다. 다른 객체나 버전은 INVALID_GRAPH다. 인증 부재, 비활성화, cache limit/주입 실패에는 정확한 Push+EARLY_N을 실행한다. 유한 row_budget 요청도 guard를 사용하지 않고 행 경계 예산을 지원하는 정확한 Push 경로를 사용한다. pre-cancel 및 부분 탐색은 출력·인증을 공개하지 않는다. output 할당 주입 실패는 기존 인증을 보존한다. reverse Builder의 optional allocation 실패는 fallback하며 필수 graph/workspace/output 할당 실패는 ALLOCATION_FAILED다. 실제 OOM을 유발한 fault campaign은 하지 않았고 계약에 있는 cache/output 주입과 소스 검토 범위다.

**API의 `bound < n` 의미를 그대로 유지했다.** 원본 helper는 이전 reach가 n이어도 거리 label을 쓸 수 있지만 이번 plugin은 이를 유효 인증으로 광고하거나 사용하지 않는다. 이 제한은 특히 Google에서 큰 차이를 만든다. 임의 외부 거리 배열 import, API 버전 확장, mutable borrowed 출력은 추가하지 않았다. seed prepare/update는 실제 BFS 비용을 지불한다.

새 build 하위 폴더의 정책 번호는 0 Push, 1 TABLE, 2 LAST matched controls, 3 OLD_P2, 4 Direction+RIE, 5 Direction+RIE+TABLE controls, 6 COUNT, 7 CLOSURE, 8 RADIUS, 9 FRONTIER, 10 immediate exact-result reuse다. `p9_0.so`는 FRONTIER ready, `p9_1.so`는 FRONTIER deferred다. `_phase.so`는 intrusive phase timer가 켜진 별도 진단 모듈이다. `dg_api_audit.hpp`/`dg_audit_snapshot`은 연구 진단용 선택 symbol이며 공통 API에 추가한 계약이 아니다. MAIN은 이 symbol을 사용하지 않는다.

OLD_P2/RIE control wrapper는 인증 부재에도 본래 Direction 알고리즘을 실행하도록 만든 성능 대조군이다. 전체 owned 출력·서비스 비용은 같지만 인증 제공 plugin의 fallback 적합성을 주장하지 않는다. MAIN 교체 검증 대상은 실제 기본 3종과 DistanceGuard 4종이다.

## 실제 교체와 독립 정확성

| 검사 | 결과 |
|---|---|
| 같은 기존 MAIN에서 BFS / RCC TABLE / RCC LAST | 각각 PASS |
| 같은 MAIN에서 DG COUNT/CLOSURE/RADIUS/FRONTIER × ready/deferred | 8개 모두 PASS |
| 각 MAIN 실행 | checks 193,136; 전체 배열 2,111; n=3 directed graph 512개 전수 포함 |
| DG 추가 계약 검사 | 176건 PASS; graph 인스턴스/버전, pre-cancel, row_budget=1 부분 취소, 실패 후 기존 인증, finite budget fallback, update, disabled, destroy 후 결과, all-n fallback |
| 별도 API 진단 | 12 graph × 2 source 순서 × 14 mode × 2 path × 33 요청 = 전체 배열 22,176 PASS |
| 독립 Python raw-edge deque BFS | 내보낸 2,688 배열 / 6,544,608 원소 PASS; 12 graph, 86 distinct graph-source oracle |
| 고정 primary service | 26,880 trials / 전체 배열 564,480 PASS; 모듈 파괴 후 보유 결과 재검증 |
| 별도 phase diagnostics | 1,008 trials / 전체 배열 33,264 PASS |

MAIN의 기존 cache limit 0·주입 실패·output 실패·동시 immutable reader·release/reprepare 검사도 각 교체에서 통과했다. 위 수는 중복 source와 graph를 포함한 검사 수이며 고유 실세계 표본 수가 아니다. 테스트 PASS는 모든 가능한 입력의 형식 증명이나 미수집 GPU 호환성을 뜻하지 않는다. CPU ABI는 기존 WSL Linux/g++/C++ runtime 조합에 한정된다.

## 동일 서비스 측정

성능 전에 `DG_API_PROTOCOL.json`과 모든 소스·바이너리 pin을 고정했다. 기존 g++15.2/C++20/O2, **5개 순차 새 프로세스 × 8 round × 반대 순서 2 sweep**, warmup/성능 재시도/결과 후 최적화 0회다. Google1024/LJ4096 파생 graph와 합성 oneway_dense, legacy/unique source, q8/q32, ready/deferred, 14개 mode를 모두 보존했다. q는 첫 요청 다음의 후속 요청 수다.

모든 mode의 첫 요청은 인증 없는 동일 Push+EARLY_N이다. 후속은 동일 source 목록이며 기존 API에 없는 즉시 결과 재사용을 숨겨 넣지 않았다. 별도 EXACT_REUSE가 그 강한 간단한 대조군이다. 이전 감사의 공통 exact reuse·다른 첫 요청·borrowed kernel 측정과 이번 수치를 섞지 않는다.

`service_ns`는 module factory, deferred prepare, API can_apply/run 호출, 알고리즘, 인증 유지, 출력 할당·복사, module release/destroy를 포함한 연속 구간에 **별도 실측 소비자 출력·컨테이너 해제**를 더한 값이다. oracle 검증은 두 구간 사이에 있으며 제외·별도 보고한다. 따라서 oracle를 포함하지 않는 구성 요소 합이고 하나의 연속 wall timer라고 부르지 않는다. ready는 factory/prepare를 과거 준비로 이동하여 따로 기록하고, history-inclusive 지표에는 다시 더한다. deferred는 CSR 변환·workspace/cache 준비를 batch 안에서 수행하고 reverse를 첫 필요한 후속 호출에서 지연 구축한다. ready는 이들을 먼저 구축한다.

공통 immutable API Graph 생성/입력 I/O/독립 oracle와 프로세스의 1회 dlopen startup은 batch 밖이다. MAIN도 라이브러리를 유지한다. dlopen은 각 caller stderr에 별도 실측했다. 새로운 Graph를 외부에서 구성하는 비용까지 포함한 응용 전체 wall time이라고 확대하지 않는다. 기존 배포 DSO의 두 번 출력 복사와 달리 새 matched TABLE/LAST 및 DG는 한 번 복사한다. 고유 이득 판정은 **배포 모듈과 matched 대조군 모두**를 요구한다. primary에서는 선택 telemetry 호출과 세부 timer를 껐다. API 기존 계수 경로와 새 guard 논리 계수는 실행 비용에 남아 있다.

두 mirrored sweep의 시간을 산술평균한 뒤 candidate/baseline 비율을 만들었다. 조건별 40개 짝 block, 5 session이다. gate는 median <0.95, 32/40 이상 승리, 5 session median 모두 <0.95를 동시에 요구한다. TABLE/LAST 배포·matched, OLD_P2, RIE, RIE+TABLE, EXACT_REUSE, DG_COUNT/RADIUS를 모두 통과해야 조건 양성이다. 10,000회 고정 seed session-cluster bootstrap의 기술적 95% 구간, session range, 모든 outlier를 보존했다. 5개의 같은 날 session이고 다중 비교 보정/다른 날짜 재현이 없으므로 모집단 보장으로 해석하지 않는다. 336개 동일-policy mirror 중앙 비율 범위는 0.9147–1.0339, raw 최대는 6.0209다.

## 전체시간과 고유 이득

다음은 ready q32의 DG_FRONTIER/기준선 짝 중앙 비율이다. 괄호는 위 session-cluster bootstrap 95% 구간이다. 1 미만이 빠르다. 모든 비교·session medians·승패는 `PAIR_STATS.json`, 절대시간은 `COSTS.json`에 있다.

| graph / source | / 배포 TABLE | / matched TABLE | / OLD_P2 | / Direction+RIE | / DG_COUNT |
|---|---:|---:|---:|---:|---:|
| Google legacy | 0.9468 | 1.0021 (1.0005–1.0032) | 0.5994 | 0.5852 | 1.0004 |
| Google unique | 0.9015 | 0.9792 (0.9713–0.9843) | 0.6035 | 0.5947 | 1.0118 |
| LJ legacy | 0.9886 | 0.9840 (0.9755–0.9902) | 1.1013 | 1.1318 | 1.0519 |
| LJ unique | 1.0156 | 1.0058 (1.0055–1.0151) | 1.1256 | 1.1530 | 1.0560 |
| oneway legacy | 0.7896 | 0.7331 (0.7195–0.7672) | 0.0907 | 0.0863 | 0.1102 |
| oneway unique | 1.4125 | 1.3117 (1.3061–1.3213) | 0.3103 | 0.2939 | 0.7870 |

Google legacy의 guard 인증 적용은 33번 중 2번뿐이고 실제 거리 label 읽기는 **0회**다. 네 DG ablation의 edge 수가 모두 131,150으로 같다. 원본 helper에서의 Google 추가 filter 생략은 이 엄격한 API 계약에서는 유지되지 않는다. TABLE 대비 관측 차이는 한 번 복사·fallback 경로 등으로 설명해야 하며 DistanceGuard의 고유 이득이라고 하지 않는다. matched LAST 대비도 legacy 비율 약1.02이며 전체 gate 실패다.

LJ legacy는 COUNT 874,228 → FRONTIER 825,955로 **48,273 edge probes를 추가 생략**했다. 그러나 RIE+TABLE은 815,173이어서 전체로는 FRONTIER가 10,782번 더 검사한다. API fallback·첫 공통 요청 때문에 과거 helper의 절대 edge 수와 다르다. FRONTIER의 추가 label 읽기는266,385회이며 old labels/필터 비용까지 지불한 시간은 COUNT보다5.19%, OLD_P2보다10.13%, RIE보다13.18% 느리다. 실제 파생 graph에서 강한 고유 전체시간 우위는 없다.

**유일한 전체 gate 양성은 oneway_dense / legacy / q32 / ready**다. 배포 TABLE 대비0.7896, LAST0.8019, matched TABLE0.7331, LAST0.7301이며 각각37/40 승리다. matched TABLE의 session median 범위0.7058–0.7903, bootstrap95% 0.7195–0.7672다. COUNT 대비0.1102, RADIUS0.5808, EXACT_REUSE0.4267도 통과한다. COUNT8,349,199 → CLOSURE2,057,647 → RADIUS1,104,106 → FRONTIER406,837 edges여서 matched filter 차분도 있다. 다만 일부 block에서 candidate가 느렸던 outlier를 삭제하지 않았다.

이 합성 양성도 **deferred에서는 matched TABLE 대비 약1.30**, ready에 실제 과거 준비를 합치면 약1.31로 역전된다. unique ready에서도1.3117로 느리다. q8 포함 다른 조건은 모든 강한 대조군을 동시에 통과하지 못했다. 준비비 포함 양성 조건은0개다. 사전 식별/선택 비용을 지불하는 온라인 정책이나 새 실제 holdout도 없다. 따라서 제한적인 이미 준비된 합성 요청 witness로만 인정한다.

## 준비·유지·어댑터 비용 분리

primary ready/legacy/q32의 절대 실측 중앙값(µs)은 아래와 같다. 과거 준비는 factory+CSR 전환+workspace/cache+필요 시 reverse다. 열별 중앙값의 합을 전체 중앙값과 동일시하지 않는다.

| graph / mode | 서비스 | 과거 준비 | query 전체 | 소비자 해제 |
|---|---:|---:|---:|---:|
| Google matched TABLE | 222.47 | 23.36 | 220.50 | 1.40 |
| Google FRONTIER | 224.16 | 59.17 | 221.98 | 1.37 |
| LJ matched TABLE | 1652.77 | 156.17 | 1649.86 | 1.73 |
| LJ OLD_P2 | 1485.43 | 376.89 | 1482.63 | 1.78 |
| LJ FRONTIER | 1630.05 | 376.19 | 1626.50 | 1.72 |
| oneway matched TABLE | 527.14 | 429.49 | 524.37 | 1.45 |
| oneway FRONTIER | 387.07 | 872.91 | 384.53 | 1.34 |

별도 intrusive phase build는 같은 algorithm core에서 세부 timer만 켠다. 아래는 ready/legacy/q32, 6개 진단 trial 중앙값(µs)이다. primary 배율의 분모로 사용하거나 다른 실행에서 뺄셈하지 않는다. `internal residual`은 **같은 trial**의 전체 run timer에서 알고리즘/할당/복사/유지/reverse 구간을 뺀 잔여다. 검증·분기·계수·내부 호출 및 timer overhead를 포함하며 순수한 간접호출 한 번의 지연은 아니다.

| graph | BFS/guard 알고리즘 | owned 할당 | 출력 복사 | 인증 유지 | 내부 residual | prepare CSR | prepare reverse |
|---|---:|---:|---:|---:|---:|---:|---:|
| Google | 223.721 | 7.116 | 1.775 | 0.846 | 4.257 | 22.088 | 53.538 |
| LJ | 1610.649 | 15.196 | 5.513 | 1.148 | 5.166 | 152.962 | 210.433 |
| oneway | 373.294 | 10.059 | 1.874 | 0.891 | 5.207 | 456.370 | 456.056 |

deferred reverse 계측은 각각36.590/208.721/427.714µs이며 service에 포함된다. ready도 매번 ensure_reverse 호출 확인 비용을 지불한다. caller dispatch·output vector·module release/destroy·마지막 소비자 해제는 service와 개별 열에 포함한다. P2 원래 비진단 경로의 exact inspected_edges는 미수집이다(`edge_available=false`); 0을 실제 무검사로 해석하지 않는다.

DG retained cache는 Google/oneway4096B, LJ16384B다. 추가 immutable CSR payload는34968/532500/225944B다. reverse와 workspace·임시 edge pair·allocator 메타데이터·보유 출력까지 포함한 peak memory 상한이라는 뜻은 아니다. 각 primary/phase process 관측 peak RSS19848KiB는 전체 로드된 대조군/fixture/oracle가 포함된 process 값이다. 유지에서 workspace 배열을 swap하는 원본과 달리 이미 반환한 API owned Output을 공유해 캐시를 갱신하며, 이 변경의 효과는 matched COUNT/TABLE/LAST 및 실제 복사비를 통해 분리했다.

## 최종 판정과 보존

- 정확성/API 계약: **검사 범위 PASS**, 동일 MAIN 교체 가능 실험 plugin.
- 기본 통합: **HOLD**, 기본 RCC·MAIN에 연결하거나 자동 병합하지 않음.
- 제한적 가능성: 이미 준비된 reverse/모듈 + 고정 합성 지역 요청 + 충분한 q에서만 후보 효과 확인. 준비 포함/unique/실제 파생 입력으로 일반화 금지.
- 신규성/논문: 기존 `SCOPE_DISTANCE_NOVELTY_AUDIT.md` 판정을 유지한다. 이번 API 어댑터·조건부 성능은 학술적 최초성이나 독립 논문 기여의 새 증거가 아니다. 새 문헌감사를 수행한 것으로 주장하지 않는다.
- 이번 고정 campaign 뒤 최적화 반복0, 새 GPU0, 유료 자원0, MAIN 재빌드0.

원시 service CSV 5개, phase CSV, 배열 JSONL, work CSV, 명령/stdout/stderr, 전체 pins, 불확실성·비용 JSON, 이전 증거/원본 보존 receipts를 `results/dg_api_20261021/`에 보존한다. 실제 실행 binaries도 `RUNTIME_BINARIES.tar.gz`와 bytes/SHA receipt로 보존한다. 컴파일 경고 두 건(들여쓰기/enum conditional)은 원문 로그에 있으며 오류·실패 trial는 없었다. 성능 결과를 본 뒤 소스·실행 조건을 바꾸지 않았다.

새 깨끗한 복사본에서만 `python3 tools/run_dg_api.py prepare`, `benchmark`, `python3 tools/analyze_dg_api.py`를 실행할 수 있다. 기존 결과 디렉터리는 prepare가 거부하고 benchmark는 single-use다. 이는 현재 MAIN 재빌드를 허가하는 명령이 아니며 기존 pinned MAIN/libgraph/default DSO가 먼저 필요하다. binary bundle은 이 정확한 실행물을 제공한다. 무결성 manifest는 `ARTIFACT_SHA256.json`; GitHub 인증/권한 receipt는 `GITHUB_AUTH.json`; commit/push의 최종 SHA는 commit 밖 로컬 `DELIVERY_STATUS.json`과 실제 remote ref를 확인한다.
