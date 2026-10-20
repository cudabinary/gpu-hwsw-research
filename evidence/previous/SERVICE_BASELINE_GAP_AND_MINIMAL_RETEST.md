# 전체 서비스 최강 기준선의 남은 공백

원본 P2는 현재 상주 소비자 측정에서 LJ의 최강 비-RCC였다. 초기 service gate가 원본 P2를 후보에서 제외한 것은 분석 설계상의 누락이다.
현재 결과는 Push+RCC_TABLE이 PUSH_N 및 측정된 순차 DO_RIE보다 빠르다는 것까지 입증한다.
동일 owned-output 계약의 원본 P2 cold/ready 서비스까지 이기는지는 현재 데이터로 확정할 수 없다.

이미 종료한 3개 CPU benchmark 프로세스를 재시작하거나 추가 프로세스를 숨겨 실행하지 않았다.
기존 원시 값을 합성하여 원본 P2 서비스 시간을 만들어내지 않았다.
별도 과거 Consumer-first P2 결과는 출처와 계약이 달라 직접 분모로 쓰지 않았다.

최소 후속 검증은 새로운 자료구조나 임계값 없이 다음만 비교하는 것이다.

- 입력/순서: 기존 LJ4096 original 고정, relabel은 순서 민감도 대조.
- 경로: frozen P2의 deferred/ready와 PUSH_N 및 Push+RCC_TABLE.
- q8/q32, 전체 owned output, frozen builder, A 고정.
- 사전 고정 3개 프로세스 × 7회, 순서 교차. 결과를 보고 경로/seed를 재선택하지 않는다.
- 원본 P2 service 누락을 보완하는 CPU 실험이며 GPU는 필요하지 않다.

이 파일은 미실행 보완 계획이다. GPU 사용 권한이 없어서 중단한 것이 아니며,
현재 CPU 측정 한도 안에서 결론을 과장하지 않기 위해 남긴 연구상의 한계다.
