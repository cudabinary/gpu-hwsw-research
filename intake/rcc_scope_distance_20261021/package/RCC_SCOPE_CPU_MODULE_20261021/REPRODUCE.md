# CPU 재현법

## 1. 무결성만 확인
```bash
python3 tools/verify_package.py
```

## 2. CPU 재빌드 및 정확성
기존 설치된 g++와 Python만 사용한다. 제공된 바이너리를 실행하지 않아도 새로 빌드할 수 있다.
```bash
make all
./build/scope_probe test
./build/distance_probe test
```

- Scope: 4,736 graph 구성, 416,768 mode-query 비교.
- DistanceGuard: 640 graph 구성, 51,200 mode-query 비교.
- 두 검사는 tiny exhaustive graph와 기존 baseline 비교를 포함하고 서로 일부 겹친다.
- sanitizer나 GPU 검사는 포함하지 않는다.

## 3. 저장 출력의 독립 검증
```bash
python3 tools/verify_guards.py
```
이 명령은 raw `.edges`에서 Python deque BFS를 다시 계산해 768개의 guard 출력 배열을 검증하고, 반례/수학 부등식을 검사한다.

Scope의 배열 검증과 CSV 재집계는 기존 pandas가 있는 환경에서:
```bash
python3 tools/verify_and_analyze.py
python3 tools/analyze_guard.py
```
재집계 파일을 다시 쓰므로 원본 압축을 보존하고 별도 추출 폴더에서 수행한다. 패키지 파일을 재작성한 후에는 최초 manifest와 달라질 수 있다.

## 4. 새로운 CPU 출력 생성 (선택)
```bash
mkdir -p replay
./build/scope_probe diagnose fixtures replay
./build/distance_probe diagnose fixtures replay
```
출력 저장/검증은 성능 타이밍 구간 밖이다. 기존 진단 파일을 덮지 않는다.

## 5. 성능을 새로 재실행할 때
기존 보존 수치 재계산과 새 벤치마크를 구분한다. 각 명령은 foreground 단일 CPU 프로세스이며 GPU를 사용하지 않는다.
```bash
./build/scope_probe bench fixtures 0 > replay/scope_session0.csv
./build/scope_probe cold fixtures 0 > replay/scope_cold_session0.csv
./build/distance_probe bench fixtures 0 > replay/guard_session0.csv
```
Session 0/1/2 외에는 실행기가 거부한다. round는 1차 resident 7, 1차 cold 3, 2차 guard resident 7로 고정한다. 이전 연구 머신/다른 CPU의 절대시간과 연결하지 않는다. 요청 범위는 `PROTOCOL_FROZEN.json`/`GUARD_PROTOCOL_FROZEN.json`에 고정되어 있다.

`bench`: reverse는 상주; 증거 cache·workspace 준비, 유지·반환 복사·해제 포함. `cold`: CSR 상주; 필요한 reference reverse의 생성과 내부 검증도 포함. raw 입력 로딩/CSR 파싱은 포함하지 않는다. 2차 distance guard의 cold reverse 전체서비스 수치는 측정하지 않았다.

## 한계
추가 scratch/cache 수치는 배열 payload 회계이며 프로세스 전체 memory hard cap이 아니다. 무제한 외부 snapshot reader를 유지하지 말 것. executor는 단일 소유자 API이며 CUDA/CPU 동시 호출용이 아니다. 새 sanitizer 실행은 이 패키지의 승인 범위에 들어 있지 않다.
