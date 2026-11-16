# 예비시험 결과 (P-01~P-08)

예비시험은 SIL 구현과 시험 환경의 문제를 찾는 단계이며, 이 결과를 본시험의 통계적 성능 입증으로 쓰지 않음.
대상은 가정 반사면 R0~R3(프로젝트 가정)이며 6세 더미나 인체를 대표하지 않음.

항목 90개: 일치 59, 불일치 4, 기록 27 (P-08의 중복 기준 조건 S03은 표에 한 번만 표시)

실행 환경: Python 3.13.18, numpy 2.5.3, 난수 numpy.random.PCG64 via SeedSequence(seed).spawn

## P-01 정상 착석·빈 좌석 기본 동작

| 항목 | 기대 결과 | 실제 결과 | 일치 | 원인 구분 |
|---|---|---|---|---|
| empty 결정적 | UNOCCUPIED | UNOCCUPIED | 일치 | - |
| empty 무작위 10회(σ=1 cm) | UNOCCUPIED 10회 | OCC 0, UNOCC 10, UNK 0 | 일치 | - |
| empty 로그 완전성 | 요청 51건 모두 기록 | 모두 기록 | 일치 | - |
| empty 지표 계산 점검 | 손 계산 (10, 0, 0) | 함수 (10, 0, 0) | 일치 | - |
| R1 결정적 | OCCUPIED | OCCUPIED | 일치 | - |
| R1 무작위 10회(σ=1 cm) | OCCUPIED 10회 | OCC 10, UNOCC 0, UNK 0 | 일치 | - |
| R1 로그 완전성 | 요청 51건 모두 기록 | 모두 기록 | 일치 | - |
| R1 지표 계산 점검 | 손 계산 (10, 0, 0) | 함수 (10, 0, 0) | 일치 | - |
| R2 결정적 | OCCUPIED | OCCUPIED | 일치 | - |
| R2 무작위 10회(σ=1 cm) | OCCUPIED 10회 | OCC 10, UNOCC 0, UNK 0 | 일치 | - |
| R2 로그 완전성 | 요청 51건 모두 기록 | 모두 기록 | 일치 | - |
| R2 지표 계산 점검 | 손 계산 (10, 0, 0) | 함수 (10, 0, 0) | 일치 | - |
| R3 결정적 | OCCUPIED | OCCUPIED | 일치 | - |
| R3 무작위 10회(σ=1 cm) | OCCUPIED 10회 | OCC 10, UNOCC 0, UNK 0 | 일치 | - |
| R3 로그 완전성 | 요청 51건 모두 기록 | 모두 기록 | 일치 | - |
| R3 지표 계산 점검 | 손 계산 (10, 0, 0) | 함수 (10, 0, 0) | 일치 | - |
| 측정 요청 최소 간격(SR-06) | > 0.060 s | 0.100 s | 일치 | - |

## P-02 사람과 같은 거리 입력을 만드는 가방

| 항목 | 기대 결과 | 실제 결과 | 일치 | 원인 구분 |
|---|---|---|---|---|
| (a) R0 화물(결정적+무작위 11회) | UNOCC 11회 | OCC 0, UNOCC 11, UNK 0 | 일치 | - |
| (b-1) 화물 윗면 = R1 높이, 같은 정지 거리 이력 11회 | 요구(SR-04): UNOCC / 예상: 사람과 출력 동일(구분 불가) | 입력 동일 11/11, 출력 동일 11/11; 화물 출력 OCC 11, UNOCC 0, UNK 0 | 불일치 | 알고리즘 특성(거리 입력만으로 구분 불가) (SR-04 기준은 바꾸지 않고 불일치를 그대로 기록) |
| (b-1) 화물 윗면 = R2 높이, 같은 정지 거리 이력 11회 | 요구(SR-04): UNOCC / 예상: 사람과 출력 동일(구분 불가) | 입력 동일 11/11, 출력 동일 11/11; 화물 출력 OCC 11, UNOCC 0, UNK 0 | 불일치 | 알고리즘 특성(거리 입력만으로 구분 불가) (SR-04 기준은 바꾸지 않고 불일치를 그대로 기록) |
| (b-2) 사람만 움직임 가정(±1.0 cm, 0.25 Hz), 화물 정지 11회 | 출력 차이 유무 기록(현재 알고리즘은 시간 변동을 쓰지 않음) | 판정 시점 출력이 다른 시행 0/11; 화물 OCC 11, UNOCC 0, UNK 0; 사람 OCC 11, UNOCC 0, UNK 0 | 기록 | 알고리즘 특성(시간 변동 미사용) (움직임 크기는 근거 없는 가정) |

## P-03 임계값 경계와 초기 히스테리시스(필터 뒤 Δ 직접 주입)

| 항목 | 기대 결과 | 실제 결과 | 일치 | 원인 구분 |
|---|---|---|---|---|
| T_db=0.0 UNOCCUPIED에서 Δ=9.0 cm | UNOCCUPIED | UNOCCUPIED | 일치 | - |
| T_db=0.0 UNOCCUPIED에서 Δ=10.0 cm | OCCUPIED | OCCUPIED | 일치 | - |
| T_db=0.0 UNOCCUPIED에서 Δ=11.0 cm | OCCUPIED | OCCUPIED | 일치 | - |
| T_db=0.0 OCCUPIED에서 Δ=6.0 cm | OCCUPIED | OCCUPIED | 일치 | - |
| T_db=0.0 OCCUPIED에서 Δ=5.0 cm | UNOCCUPIED | UNOCCUPIED | 일치 | - |
| T_db=0.0 OCCUPIED에서 Δ=4.0 cm | UNOCCUPIED | UNOCCUPIED | 일치 | - |
| T_db=0.0 최초 판정에서 Δ=6.0 cm | UNOCCUPIED | UNOCCUPIED | 일치 | - |
| T_db=0.0 최초 판정에서 Δ=7.5 cm | OCCUPIED | OCCUPIED | 일치 | - |
| T_db=0.0 최초 판정에서 Δ=9.0 cm | OCCUPIED | OCCUPIED | 일치 | - |
| T_db=0.0 연속 전이 9→10→9→5 cm | UNOCCUPIED → OCCUPIED → OCCUPIED → UNOCCUPIED | UNOCCUPIED → OCCUPIED → OCCUPIED → UNOCCUPIED | 일치 | - |
| T_db=0.5 UNOCCUPIED에서 Δ=9.0 cm | UNOCCUPIED | UNOCCUPIED | 일치 | - |
| T_db=0.5 UNOCCUPIED에서 Δ=10.0 cm | OCCUPIED | OCCUPIED | 일치 | - |
| T_db=0.5 UNOCCUPIED에서 Δ=11.0 cm | OCCUPIED | OCCUPIED | 일치 | - |
| T_db=0.5 OCCUPIED에서 Δ=6.0 cm | OCCUPIED | OCCUPIED | 일치 | - |
| T_db=0.5 OCCUPIED에서 Δ=5.0 cm | UNOCCUPIED | UNOCCUPIED | 일치 | - |
| T_db=0.5 OCCUPIED에서 Δ=4.0 cm | UNOCCUPIED | UNOCCUPIED | 일치 | - |
| T_db=0.5 최초 판정에서 Δ=6.0 cm | UNOCCUPIED | UNOCCUPIED | 일치 | - |
| T_db=0.5 최초 판정에서 Δ=7.5 cm | OCCUPIED | OCCUPIED | 일치 | - |
| T_db=0.5 최초 판정에서 Δ=9.0 cm | OCCUPIED | OCCUPIED | 일치 | - |
| T_db=0.5 연속 전이 9→10→9→5 cm | UNOCCUPIED → OCCUPIED → OCCUPIED → UNOCCUPIED | UNOCCUPIED → OCCUPIED → OCCUPIED → UNOCCUPIED | 일치 | - |

## P-04 초기화와 최초 판정

| 항목 | 기대 결과 | 실제 결과 | 일치 | 원인 구분 |
|---|---|---|---|---|
| R2 최초 유효 판정 시각(11회) | 모두 ≤ 1.0 s, 이전은 UNKNOWN | 0.4034–0.4036 s | 일치 | - |
| R2 최초 판정 이후 출력 | 계속 OCCUPIED | 정답 외 출력 시행 0/11 | 일치 | - |
| empty 최초 유효 판정 시각(11회) | 모두 ≤ 1.0 s, 이전은 UNKNOWN | 0.4057–0.4059 s | 일치 | - |
| empty 최초 판정 이후 출력 | 계속 UNOCCUPIED | 정답 외 출력 시행 0/11 | 일치 | - |

## P-05 에코 없음과 복구

| 항목 | 기대 결과 | 실제 결과 | 일치 | 원인 구분 |
|---|---|---|---|---|
| R2 에코 4회 연속 제거(11회) | UNKNOWN 진입 없음, 이전 상태 유지 | UNKNOWN 진입 0/11, 정답 외 유효 출력 0/11 | 일치 | - |
| R2 에코 5회 연속 제거(11회) | UNKNOWN 진입, 복구 ≤ 1.0 s, 점유에서 UNOCC 없음 | 진입 11/11, 복구 시간 0.400–0.400 s, 정답 외 유효 출력 0/11, 최종 정답 11/11 | 일치 | - |
| R2 에코 6회 연속 제거(11회) | UNKNOWN 진입, 복구 ≤ 1.0 s, 점유에서 UNOCC 없음 | 진입 11/11, 복구 시간 0.400–0.400 s, 정답 외 유효 출력 0/11, 최종 정답 11/11 | 일치 | - |
| empty 에코 4회 연속 제거(11회) | UNKNOWN 진입 없음, 이전 상태 유지 | UNKNOWN 진입 0/11, 정답 외 유효 출력 0/11 | 일치 | - |
| empty 에코 5회 연속 제거(11회) | UNKNOWN 진입, 복구 ≤ 1.0 s, 점유에서 UNOCC 없음 | 진입 11/11, 복구 시간 0.400–0.400 s, 정답 외 유효 출력 0/11, 최종 정답 11/11 | 일치 | - |
| empty 에코 6회 연속 제거(11회) | UNKNOWN 진입, 복구 ≤ 1.0 s, 점유에서 UNOCC 없음 | 진입 11/11, 복구 시간 0.400–0.400 s, 정답 외 유효 출력 0/11, 최종 정답 11/11 | 일치 | - |

## P-06 입력 갱신 중단·범위 밖 값과 복구

| 항목 | 기대 결과 | 실제 결과 | 일치 | 원인 구분 |
|---|---|---|---|---|
| R2 결과 전달 2 s 중단(11회) | 마지막 유효 샘플부터 ≤ 1.1 s 내 UNKNOWN, 복구 ≤ 1.0 s | UNKNOWN 전환 1.096–1.097 s, 복구 0.400–0.400 s, 최종 정답 11/11 | 일치 | - |
| R2 값 1 cm로 4회 치환(결정적) | 무효 처리, 상태 유지 | UNKNOWN 진입 없음 | 일치 | - |
| R2 값 1 cm로 5회 치환(결정적) | 무효 처리, UNKNOWN 후 복구 | UNKNOWN 진입 있음, 최종 OCCUPIED | 일치 | - |
| R2 값 401 cm로 4회 치환(결정적) | 무효 처리, 상태 유지 | UNKNOWN 진입 없음 | 일치 | - |
| R2 값 401 cm로 5회 치환(결정적) | 무효 처리, UNKNOWN 후 복구 | UNKNOWN 진입 있음, 최종 OCCUPIED | 일치 | - |
| empty 값 1 cm로 4회 치환(결정적) | 무효 처리, 상태 유지 | UNKNOWN 진입 없음 | 일치 | - |
| empty 값 1 cm로 5회 치환(결정적) | 무효 처리, UNKNOWN 후 복구 | UNKNOWN 진입 있음, 최종 UNOCCUPIED | 일치 | - |
| empty 값 401 cm로 4회 치환(결정적) | 무효 처리, 상태 유지 | UNKNOWN 진입 없음 | 일치 | - |
| empty 값 401 cm로 5회 치환(결정적) | 무효 처리, UNKNOWN 후 복구 | UNKNOWN 진입 있음, 최종 UNOCCUPIED | 일치 | - |

## P-07 전체 응답 시간

| 항목 | 기대 결과 | 실제 결과 | 일치 | 원인 구분 |
|---|---|---|---|---|
| T_db=0.0 착석(빈 좌석→R1) 11회 | 계산 예상 약 0.2–0.3 s(+에코 수신 지연), 목표 ≤ 3 s | 0.205–0.285 s, 기한 초과 0회 | 일치 | - |
| T_db=0.0 이석(R1→빈 좌석) 11회 | 계산 예상 약 0.2–0.3 s(+에코 수신 지연), 목표 ≤ 3 s | 0.206–0.302 s, 기한 초과 0회 | 일치 | - |
| T_db=0.5 착석(빈 좌석→R1) 11회 | 계산 예상 약 0.7–0.8 s(+에코 수신 지연), 목표 ≤ 3 s | 0.705–0.899 s, 기한 초과 0회 | 불일치 | 문서 모호함: T_db를 후보 수신 시각부터의 시간으로 재면 에코 수신 시각의 흔들림(수십 µs) 때문에 0.5 s에 조금 못 미쳐 한 주기(0.1 s)를 더 기다림. 해당 4/11회 (events.csv) |
| T_db=0.5 이석(R1→빈 좌석) 11회 | 계산 예상 약 0.7–0.8 s(+에코 수신 지연), 목표 ≤ 3 s | 0.706–0.868 s, 기한 초과 0회 | 불일치 | 문서 모호함: T_db를 후보 수신 시각부터의 시간으로 재면 에코 수신 시각의 흔들림(수십 µs) 때문에 0.5 s에 조금 못 미쳐 한 주기(0.1 s)를 더 기다림. 해당 5/11회 (events.csv) |

## P-08 온도 보정과 잡음·손실 민감도(한 요인씩, 기록만)

| 항목 | 기대 결과 | 실제 결과 | 일치 | 원인 구분 |
|---|---|---|---|---|
| ①온도·보정 S01 T=0°C 보정=무 σ=1 p_loss=0 R1 | 기록(정답 OCCUPIED) | OCC 10, UNOCC 0, UNK 0; UNKNOWN 진입 시행 0/10; t_eval까지 최초 판정 없음 0/10; 잡음 없는 Δ 17.92 cm | 기록 | - |
| ①온도·보정 S01 T=0°C 보정=무 σ=1 p_loss=0 empty | 기록(정답 UNOCCUPIED) | OCC 0, UNOCC 10, UNK 0; UNKNOWN 진입 시행 0/10; t_eval까지 최초 판정 없음 0/10; 잡음 없는 Δ -2.6 cm | 기록 | - |
| ①온도·보정 S02 T=0°C 보정=유 σ=1 p_loss=0 R1 | 기록(정답 OCCUPIED) | OCC 10, UNOCC 0, UNK 0; UNKNOWN 진입 시행 0/10; t_eval까지 최초 판정 없음 0/10; 잡음 없는 Δ 20.0 cm | 기록 | - |
| ①온도·보정 S02 T=0°C 보정=유 σ=1 p_loss=0 empty | 기록(정답 UNOCCUPIED) | OCC 0, UNOCC 10, UNK 0; UNKNOWN 진입 시행 0/10; t_eval까지 최초 판정 없음 0/10; 잡음 없는 Δ 0.0 cm | 기록 | - |
| ①온도·보정 S03 T=20°C 보정=무 σ=1 p_loss=0 R1 | 기록(정답 OCCUPIED) | OCC 10, UNOCC 0, UNK 0; UNKNOWN 진입 시행 0/10; t_eval까지 최초 판정 없음 0/10; 잡음 없는 Δ 20.79 cm | 기록 | - |
| ①온도·보정 S03 T=20°C 보정=무 σ=1 p_loss=0 empty | 기록(정답 UNOCCUPIED) | OCC 0, UNOCC 10, UNK 0; UNKNOWN 진입 시행 0/10; t_eval까지 최초 판정 없음 0/10; 잡음 없는 Δ 0.99 cm | 기록 | - |
| ①온도·보정 S04 T=20°C 보정=유 σ=1 p_loss=0 R1 | 기록(정답 OCCUPIED) | OCC 10, UNOCC 0, UNK 0; UNKNOWN 진입 시행 0/10; t_eval까지 최초 판정 없음 0/10; 잡음 없는 Δ 20.0 cm | 기록 | - |
| ①온도·보정 S04 T=20°C 보정=유 σ=1 p_loss=0 empty | 기록(정답 UNOCCUPIED) | OCC 0, UNOCC 10, UNK 0; UNKNOWN 진입 시행 0/10; t_eval까지 최초 판정 없음 0/10; 잡음 없는 Δ 0.0 cm | 기록 | - |
| ①온도·보정 S05 T=50°C 보정=무 σ=1 p_loss=0 R1 | 기록(정답 OCCUPIED) | OCC 10, UNOCC 0, UNK 0; UNKNOWN 진입 시행 0/10; t_eval까지 최초 판정 없음 0/10; 잡음 없는 Δ 24.74 cm | 기록 | - |
| ①온도·보정 S05 T=50°C 보정=무 σ=1 p_loss=0 empty | 기록(정답 UNOCCUPIED) | OCC 0, UNOCC 10, UNK 0; UNKNOWN 진입 시행 0/10; t_eval까지 최초 판정 없음 0/10; 잡음 없는 Δ 5.92 cm | 기록 | - |
| ①온도·보정 S06 T=50°C 보정=유 σ=1 p_loss=0 R1 | 기록(정답 OCCUPIED) | OCC 10, UNOCC 0, UNK 0; UNKNOWN 진입 시행 0/10; t_eval까지 최초 판정 없음 0/10; 잡음 없는 Δ 20.0 cm | 기록 | - |
| ①온도·보정 S06 T=50°C 보정=유 σ=1 p_loss=0 empty | 기록(정답 UNOCCUPIED) | OCC 0, UNOCC 10, UNK 0; UNKNOWN 진입 시행 0/10; t_eval까지 최초 판정 없음 0/10; 잡음 없는 Δ 0.0 cm | 기록 | - |
| ②잡음 S07 T=20°C 보정=무 σ=0.5 p_loss=0 R1 | 기록(정답 OCCUPIED) | OCC 10, UNOCC 0, UNK 0; UNKNOWN 진입 시행 0/10; t_eval까지 최초 판정 없음 0/10; 잡음 없는 Δ 20.79 cm | 기록 | - |
| ②잡음 S07 T=20°C 보정=무 σ=0.5 p_loss=0 empty | 기록(정답 UNOCCUPIED) | OCC 0, UNOCC 10, UNK 0; UNKNOWN 진입 시행 0/10; t_eval까지 최초 판정 없음 0/10; 잡음 없는 Δ 0.99 cm | 기록 | - |
| ②잡음 S08 T=20°C 보정=무 σ=2 p_loss=0 R1 | 기록(정답 OCCUPIED) | OCC 10, UNOCC 0, UNK 0; UNKNOWN 진입 시행 0/10; t_eval까지 최초 판정 없음 0/10; 잡음 없는 Δ 20.79 cm | 기록 | - |
| ②잡음 S08 T=20°C 보정=무 σ=2 p_loss=0 empty | 기록(정답 UNOCCUPIED) | OCC 0, UNOCC 10, UNK 0; UNKNOWN 진입 시행 0/10; t_eval까지 최초 판정 없음 0/10; 잡음 없는 Δ 0.99 cm | 기록 | - |
| ③반사 손실 S03 T=20°C 보정=무 σ=1 p_loss=0 R1 | 기록(정답 OCCUPIED) | OCC 10, UNOCC 0, UNK 0; UNKNOWN 진입 시행 0/10; t_eval까지 최초 판정 없음 0/10; 잡음 없는 Δ 20.79 cm | 기록 | - |
| ③반사 손실 S03 T=20°C 보정=무 σ=1 p_loss=0 empty | 기록(정답 UNOCCUPIED) | OCC 0, UNOCC 10, UNK 0; UNKNOWN 진입 시행 0/10; t_eval까지 최초 판정 없음 0/10; 잡음 없는 Δ 0.99 cm | 기록 | - |
| ③반사 손실 S09 T=20°C 보정=무 σ=1 p_loss=0.1 R1 | 기록(정답 OCCUPIED) | OCC 10, UNOCC 0, UNK 0; UNKNOWN 진입 시행 0/10; t_eval까지 최초 판정 없음 0/10; 잡음 없는 Δ 20.79 cm | 기록 | - |
| ③반사 손실 S09 T=20°C 보정=무 σ=1 p_loss=0.1 empty | 기록(정답 UNOCCUPIED) | OCC 0, UNOCC 10, UNK 0; UNKNOWN 진입 시행 0/10; t_eval까지 최초 판정 없음 0/10; 잡음 없는 Δ 0.99 cm | 기록 | - |
| ③반사 손실 S10 T=20°C 보정=무 σ=1 p_loss=0.3 R1 | 기록(정답 OCCUPIED) | OCC 8, UNOCC 0, UNK 2; UNKNOWN 진입 시행 1/10; t_eval까지 최초 판정 없음 1/10; 잡음 없는 Δ 20.79 cm | 기록 | 알고리즘 특성: 초기화·복구가 연속 유효 샘플 k개를 요구하여 손실이 잦으면 UNKNOWN이 유지됨 (손실 확률 자체는 모델 가정) |
| ③반사 손실 S10 T=20°C 보정=무 σ=1 p_loss=0.3 empty | 기록(정답 UNOCCUPIED) | OCC 0, UNOCC 9, UNK 1; UNKNOWN 진입 시행 0/10; t_eval까지 최초 판정 없음 1/10; 잡음 없는 Δ 0.99 cm | 기록 | 알고리즘 특성: 초기화·복구가 연속 유효 샘플 k개를 요구하여 손실이 잦으면 UNKNOWN이 유지됨 (손실 확률 자체는 모델 가정) |
| ③반사 손실 S11 T=20°C 보정=무 σ=1 p_loss=0.5 R1 | 기록(정답 OCCUPIED) | OCC 4, UNOCC 0, UNK 6; UNKNOWN 진입 시행 2/10; t_eval까지 최초 판정 없음 6/10; 잡음 없는 Δ 20.79 cm | 기록 | 알고리즘 특성: 초기화·복구가 연속 유효 샘플 k개를 요구하여 손실이 잦으면 UNKNOWN이 유지됨 (손실 확률 자체는 모델 가정) |
| ③반사 손실 S11 T=20°C 보정=무 σ=1 p_loss=0.5 empty | 기록(정답 UNOCCUPIED) | OCC 0, UNOCC 5, UNK 5; UNKNOWN 진입 시행 3/10; t_eval까지 최초 판정 없음 5/10; 잡음 없는 Δ 0.99 cm | 기록 | 알고리즘 특성: 초기화·복구가 연속 유효 샘플 k개를 요구하여 손실이 잦으면 UNKNOWN이 유지됨 (손실 확률 자체는 모델 가정) |
