# 다음 연구 인계: 검증된 Direction 소비자 + 정확한 종료 증거

## 가장 먼저 할 일

`CODEX_WORK_ORDER_KO.txt`가 실제 지시문이다. `MERGE_REVIEW_KO.md`는 왜 이 작업이 다음 우선순위인지 설명한다.

최신 Codex 결과는 **LJ4096 q32 cold CPU에서 유효한 전체 개선**을 확인했다. 이전 TCSC의 실패만 반복 요약하지 않는다. 하지만 병행이 순차보다 빠르거나 준비가 거의 무료라는 증거는 없다. 새로운 GPU/하드웨어 기여도 없다.

내 RCC도 무조건 합치지 않는다. 이번 독립 프로브에서 Codex가 이미 유지하는 미방문 indegree 합의 소진(RIE)을 종료 조건으로 쓰면, LJ에서는 RCC를 더해서 생략하는 일이 없었다. 반면 분리된 도달 영역의 합성 조건에서는 RCC가 추가 정보를 제공했다. **소비 알고리즘과 종료 증거를 독립 선택지로 비교**한다.

## 포함 파일

- `original_archives/`: 사용자 Codex ZIP과 RCC 원본 ZIP의 바이트 단위 사본.
- `source_reports/`: 빠르게 읽을 원 보고서 사본. 원본 ZIP 전체의 대체물이 아니다.
- `independent_bridge/`: 이번에 직접 작성·실행한 C++ 종료 adapter, 원본 Codex vendor 소스, 입력, 검사·원시 성능·작업량 결과.
- `evidence/`: 원본 CRC/SHA 결과, 공통 5개 입력 동등성, Codex CSV 재집계 및 독립 재빌드 검사 로그.
- `ROLE_SPLIT_AND_NEXT_MERGE.md`: Codex/ChatGPT의 분리된 연구 역할.
- `tools/verify_delivery.py`: 현재 패키지 SHA 검증. GPU/외부 업로드 없음.
- `tools/unpack_sources.py`: 필요할 때 원본 두 ZIP을 빈 sources 폴더에 해제. 코드 실행·다운로드 없음.

## 실행 권한

CPU 파일 분석·구현·정적 컴파일만이다. GPU query/run, Nsight, sanitizer, 설치, 외부 다운로드/업로드, 유료 자원은 미승인이다. 기존 consumer ZIP의 9,692 BFS GPU 제안도 승인된 것으로 간주하지 않는다. 기존 approval false를 유지한다.

## 전달 방법

이 ZIP과 `CODEX_WORK_ORDER_KO.txt`를 함께 전달한다. Codex 프로젝트에 원본이 이미 있으면 해시로 확인하고 그대로 읽는다. 원본·다른 작업폴더를 덮어쓰지 않는다.
