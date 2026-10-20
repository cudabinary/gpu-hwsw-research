# 신규성 및 HW 판단

Direction-Optimizing BFS, EARLY_N, 완료 도달 집합의 포함관계, WCC 상한, 결과 캐시는 기존 SW 방법의 적용/조합이다.
RIE의 충분조건은 이 정확한 메타데이터에서 증명됐으나 학술적 최초성은 별도 검토 없이 주장하지 않는다.
새 HW, GPU runtime 신규 알고리즘, 부분 인덱스 신규성은 입증되지 않았다.

실용 결과와 신규성을 구별한다. 유효한 reverse 소비자와 저렴한 종료 인증으로 실제 작업을 생략하는 것은 유용하다.
이 결과는 전용 Shadow Engine/무제한 대역폭/무료 쓰기의 필요성을 보이지 않는다.
필수 결과 n개 원소 반환, 추가 reverse 읽기·구축, GPU atomic/host level synchronization은 실제 비용이다.
GPU의 RIE는 이미 수집하는 통계로 마지막 불필요한 레벨을 생략했고, Push+RCC도 과거 완성 증거로 레벨을 생략했다.
이 관찰만으로 SM/L2/DRAM 중 어느 자원이 지배적인지, 새 HW가 강한 SW보다 빠른지 판정하지 않는다.
현재 근거는 CONTINUE_SW에 해당하며 HW 필요성은 UNKNOWN이다.
