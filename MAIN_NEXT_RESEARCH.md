# MAIN 다음 연구

목표는 ISCA/MICRO/HPCA/ASPLOS급 GPU Architecture/HW–SW co-design이다. BFS/TCSC/RCC는 첫 실험 대상이며 목표 자체가 아니다.

1. 검증된 SW 소비자를 공통 API로 선택하고, OLD_P2 service baseline 누락을 RCC 트랙에서 해결한다. RCC 개발 결과를 자동 병합하지 않는다.
2. GPU 공통 API backend를 먼저 구현·별도 검증한다. 현재 역사적 native owner는 완료됐지만 공통 API와 교체 가능한 CUDA 모듈은 없다. 기존 파일럿은 성능 연구가 아니다.
3. GPU 성능/계측 계획을 별도로 고정한다. 강한 SW 이후의 instruction/atomic, SM residency, L2/DRAM 이동, launch/synchronization을 구분한다. 미계측 Nsight 원인이나 HW 필요성을 확정하지 않는다.
4. Knowledge/Control/Timing gap을 분리한다. 불변 CSR이 A 전에 존재하므로 기존 행 완료 인터페이스의 지연을 원천적 정보 부재라고 부르지 않는다.
5. 구조적 병목이 실제 확인되면 다른 GPU workload에서 일반성을 검사한다. 무료 데이터 이동·무한 대역폭·출력 쓰기 생략을 가정하지 않는다.

이번 단계는 연구 환경 분리 후 중단하며 새 알고리즘·성능 GPU 실험을 실행하지 않았다.
