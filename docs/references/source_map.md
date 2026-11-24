# 문서와 근거 출처 지도

> 이 문서는 `docs/references/build_source_map.py`가 `document_sources.csv`에서 자동 생성한다. 직접 고치지 말고 CSV를 고친 뒤 다시 생성할 것.

문서 13개, 고유 근거 출처 42건, 문서–출처 연결 100건.

## 1. 문서별 근거 출처

| V모델 순서 | 문서 | 단계 | 상태 | 근거 출처 수 |
| --- | --- | --- | --- | --- |
| 10 | 프로젝트 선정 이유 | 1 프로젝트 선정 이유 | 검토 완료 | 5 |
| 20 | 검증의 중요성 | 2 검증의 중요성 | 검토 완료 | 11 |
| 30 | 센서 사양·사전지식 | 3 센서·사전지식 | 검토 완료 | 9 |
| 40 | SIL | 4 검증 방법론 | 검토 완료 | 9 |
| 41 | HIL | 4 검증 방법론 | 검토 완료 | 9 |
| 42 | 검증 방법 비교표 (실물·HIL·SIL) | 4 검증 방법론 | 초안 | 14 |
| 50 | 요구사항 설계 | 5 요구사항·시험 설계 | 검토 완료 | 11 |
| 60 | 시험 설계 | 5 요구사항·시험 설계 | 검토 완료 | 16 |
| 70 | SIL 설계·결과 | 6 SIL 구축·실행 | 초안 | 0 |
| 80 | SIL의 한계 | 7 SIL의 한계 | 조사 전 | 0 |
| 90 | 업계 동향·결론 | 8 업계 동향·결론 | 조사 전 | 0 |
| 100 | 최종 보고서 | 9 최종 보고서 | 조사 전 | 0 |
| 990 | 요구사항·시험 설계 통합본 v0.4.1 (보관) | 0 관리 | 검토 완료 | 16 |

### 10 프로젝트 선정 이유

단계 1 프로젝트 선정 이유 · 상태 검토 완료 · 마지막 수정 2026년 11월 11일 오후 1:29

- R-01 NHTSA SCI — Comprehensive Study of 2019 U.S. Pediatric Vehicular Hyperthermia Fatalities (DOT HS 813 360)
- R-02 Federal Register 88 FR 65149–65150 (FMVSS, Docket NHTSA-2022-0097)
- R-03 Federal Register 90 FR 390 — FMVSS; Occupant Crash Protection, Seat Belt Reminder Systems (최종규칙)
- R-04 Euro NCAP — Safe Driving Occupant Monitoring Protocol
- R-05 기아 2026 타스만 취급설명서 — 후석 승객 알림 시스템 작동 방법

### 20 검증의 중요성

단계 2 검증의 중요성 · 상태 검토 완료 · 마지막 수정 2026년 11월 11일 오후 1:28

- R-06 Nissan North America — Part 573 Defect Information Report, Recall 14V-138
- R-07 NHTSA ODI — Recall Query RQ15-001 Investigation Resume (Nissan 14V-138 후속)
- R-08 Ariane 5 Flight 501 Failure: Report by the Inquiry Board
- R-09 NASA — Mars Climate Orbiter Mishap Investigation Board Phase I Report
- R-10 NIST Planning Report 02-3 (RTI) — The Economic Impacts of Inadequate Infrastructure for Software Testing
- R-11 NHTSA — 2025 Annual Report (Annual Recalls Report)
- R-03 Federal Register 90 FR 390 — FMVSS; Occupant Crash Protection, Seat Belt Reminder Systems (최종규칙)
- R-12 Federal Register 91 FR 17144 — Seat Belt Reminder Systems (중간최종규칙)
- R-04 Euro NCAP — Safe Driving Occupant Monitoring Protocol
- R-05 기아 2026 타스만 취급설명서 — 후석 승객 알림 시스템 작동 방법
- R-13 NASA — Systems Engineering Handbook, 5.3 Product Verification

### 30 센서 사양·사전지식

단계 3 센서·사전지식 · 상태 검토 완료 · 마지막 수정 2026년 11월 11일 오후 1:29

- R-14 HC-SR04 Ultrasonic Ranging Module 데이터시트 (ElecFreaks)
- R-15 Rudyk 외 (2025) Influence of environmental factors on the accuracy of the ultrasonic rangefinder
- R-16 Arunglabi 외 (2026) HC-SR04 온도 변화 영향 분석 (Tinkercad 시뮬레이션)
- R-17 Haq 외 (2026) Accuracy of HC-SR04 Ultrasonic Servo in Servo-Scanned 2D Ranging
- R-18 NHTSA (2006) Vehicle Backover Avoidance Technology Study
- R-19 Chua 외 (2018) Development of an automatic vehicular heatstroke detection system
- R-20 Smaili 외 (2021) Errors in Distance and Angle Measurements of Ultrasonic Sensor HC-SR04
- R-21 ElecFreaks — HC-SR04 User Guide
- R-22 Toa & Whitehead (2021) — Ultrasonic Sensing Basics (TI SLAA907D)

### 40 SIL

단계 4 검증 방법론 · 상태 검토 완료 · 마지막 수정 2026년 11월 11일 오후 1:29

- R-23 Shylla et al. (2023) Model in loop (MIL), software in loop (SIL) and hardware in loop (HIL) testing in MBD
- R-24 ISO 26262-6:2018 Product development at the software level (ISO 카탈로그 페이지)
- R-25 Zhu 외(2025) High-Fidelity Ultrasonic Radar In-the-Loop Accelerated Test for Automatic Parking Systems
- R-26 Kim, D.-J., Kim, Y.-C., Jung, D.-H., & Kim, M.-S. (2024). 차량용 3D 초음파 센서 평가를 위한 SILS에 관한 연구
- R-27 Fei, Z., Andersson, M., & Tingberg, A. (2024). Correlation of software-in-the-loop simulation with physical testing for autonomous driving
- R-28 Won, J., Seok, J., Lee, S., & Yoo, J. (2025). 자율주행 차량 시스템 개발을 위한 Software-in-the-Loop Simulation 구현 방법론
- R-29 Kim, J., & Choi, Y. (2024). SIL검증과 HIL검증 비교를 통한 SIL검증 유효성 증대 방안 연구 (Study on how to increase SIL test effectiveness by comparing SIL test to HIL test)
- R-30 Jeong, S., Kwak, Y., & Lee, W. J. (2016). Software-in-the-loop simulation for early-stage testing of AUTOSAR software component
- R-31 Arsie, I., Betta, G., Capriglione, D., Pietrosanto, A., & Sommella, P. (2014). Functional testing of measurement-based control systems: An application to automotive

### 41 HIL

단계 4 검증 방법론 · 상태 검토 완료 · 마지막 수정 2026년 11월 11일 오후 1:28

- R-32 Short & Pont (2005) Hardware in the loop simulation of embedded automotive control systems
- R-33 Isermann, Schaffnit & Sinsel (1998) Hardware-in-the-loop simulation for the design and testing of engine-control systems
- R-34 Bullock et al. (2004) Hardware-in-the-loop simulation
- R-35 Nguyen et al. (2020) Hardware-in-the-loop assessment methods (European Guide to Power System Testing, ch. 4)
- R-36 Lee, Huang & Lan (2018) HIL test case specification for verification of software safety requirements in the context of ISO 26262
- R-37 ISO 26262-4:2018 Product development at the system level (ISO 카탈로그 페이지)
- R-24 ISO 26262-6:2018 Product development at the software level (ISO 카탈로그 페이지)
- R-25 Zhu 외(2025) High-Fidelity Ultrasonic Radar In-the-Loop Accelerated Test for Automatic Parking Systems
- R-38 Ma et al. (2023) Research on the autonomous parking strategy based on the ultrasonic echo simulator

### 42 검증 방법 비교표 (실물·HIL·SIL)

단계 4 검증 방법론 · 상태 초안 · 마지막 수정 2026년 11월 11일 오후 1:29

- R-32 Short & Pont (2005) Hardware in the loop simulation of embedded automotive control systems
- R-33 Isermann, Schaffnit & Sinsel (1998) Hardware-in-the-loop simulation for the design and testing of engine-control systems
- R-34 Bullock et al. (2004) Hardware-in-the-loop simulation
- R-35 Nguyen et al. (2020) Hardware-in-the-loop assessment methods (European Guide to Power System Testing, ch. 4)
- R-37 ISO 26262-4:2018 Product development at the system level (ISO 카탈로그 페이지)
- R-24 ISO 26262-6:2018 Product development at the software level (ISO 카탈로그 페이지)
- R-25 Zhu 외(2025) High-Fidelity Ultrasonic Radar In-the-Loop Accelerated Test for Automatic Parking Systems
- R-38 Ma et al. (2023) Research on the autonomous parking strategy based on the ultrasonic echo simulator
- R-23 Shylla et al. (2023) Model in loop (MIL), software in loop (SIL) and hardware in loop (HIL) testing in MBD
- R-26 Kim, D.-J., Kim, Y.-C., Jung, D.-H., & Kim, M.-S. (2024). 차량용 3D 초음파 센서 평가를 위한 SILS에 관한 연구
- R-27 Fei, Z., Andersson, M., & Tingberg, A. (2024). Correlation of software-in-the-loop simulation with physical testing for autonomous driving
- R-28 Won, J., Seok, J., Lee, S., & Yoo, J. (2025). 자율주행 차량 시스템 개발을 위한 Software-in-the-Loop Simulation 구현 방법론
- R-29 Kim, J., & Choi, Y. (2024). SIL검증과 HIL검증 비교를 통한 SIL검증 유효성 증대 방안 연구 (Study on how to increase SIL test effectiveness by comparing SIL test to HIL test)
- R-30 Jeong, S., Kwak, Y., & Lee, W. J. (2016). Software-in-the-loop simulation for early-stage testing of AUTOSAR software component

### 50 요구사항 설계

단계 5 요구사항·시험 설계 · 상태 검토 완료 · 마지막 수정 2026년 11월 11일 오후 3:03

- R-39 NASA — Appendix D: Requirements Verification Matrix
- R-40 NASA — Appendix C: How to Write a Good Requirement
- R-22 Toa & Whitehead (2021) — Ultrasonic Sensing Basics (TI SLAA907D)
- R-20 Smaili 외 (2021) Errors in Distance and Angle Measurements of Ultrasonic Sensor HC-SR04
- R-16 Arunglabi 외 (2026) HC-SR04 온도 변화 영향 분석 (Tinkercad 시뮬레이션)
- R-14 HC-SR04 Ultrasonic Ranging Module 데이터시트 (ElecFreaks)
- R-15 Rudyk 외 (2025) Influence of environmental factors on the accuracy of the ultrasonic rangefinder
- R-19 Chua 외 (2018) Development of an automatic vehicular heatstroke detection system
- R-41 Euro NCAP — Test and Assessment Protocol: Child Presence Detection
- R-03 Federal Register 90 FR 390 — FMVSS; Occupant Crash Protection, Seat Belt Reminder Systems (최종규칙)
- R-12 Federal Register 91 FR 17144 — Seat Belt Reminder Systems (중간최종규칙)

### 60 시험 설계

단계 5 요구사항·시험 설계 · 상태 검토 완료 · 마지막 수정 2026년 11월 11일 오후 1:29

- R-03 Federal Register 90 FR 390 — FMVSS; Occupant Crash Protection, Seat Belt Reminder Systems (최종규칙)
- R-12 Federal Register 91 FR 17144 — Seat Belt Reminder Systems (중간최종규칙)
- R-41 Euro NCAP — Test and Assessment Protocol: Child Presence Detection
- R-14 HC-SR04 Ultrasonic Ranging Module 데이터시트 (ElecFreaks)
- R-20 Smaili 외 (2021) Errors in Distance and Angle Measurements of Ultrasonic Sensor HC-SR04
- R-17 Haq 외 (2026) Accuracy of HC-SR04 Ultrasonic Servo in Servo-Scanned 2D Ranging
- R-16 Arunglabi 외 (2026) HC-SR04 온도 변화 영향 분석 (Tinkercad 시뮬레이션)
- R-15 Rudyk 외 (2025) Influence of environmental factors on the accuracy of the ultrasonic rangefinder
- R-19 Chua 외 (2018) Development of an automatic vehicular heatstroke detection system
- R-22 Toa & Whitehead (2021) — Ultrasonic Sensing Basics (TI SLAA907D)
- R-37 ISO 26262-4:2018 Product development at the system level (ISO 카탈로그 페이지)
- R-24 ISO 26262-6:2018 Product development at the software level (ISO 카탈로그 페이지)
- R-36 Lee, Huang & Lan (2018) HIL test case specification for verification of software safety requirements in the context of ISO 26262
- R-40 NASA — Appendix C: How to Write a Good Requirement
- R-39 NASA — Appendix D: Requirements Verification Matrix
- R-42 NIST/SEMATECH e-Handbook 7.2.4.1 Confidence intervals

### 70 SIL 설계·결과

단계 6 SIL 구축·실행 · 상태 초안 · 마지막 수정 2026년 11월 11일 오후 2:27

- 연결된 근거 출처 없음 (상태가 초안이거나 조사 전)

### 80 SIL의 한계

단계 7 SIL의 한계 · 상태 조사 전 · 마지막 수정 2026년 11월 11일 오후 1:29

- 연결된 근거 출처 없음 (상태가 초안이거나 조사 전)

### 90 업계 동향·결론

단계 8 업계 동향·결론 · 상태 조사 전 · 마지막 수정 2026년 11월 11일 오후 1:29

- 연결된 근거 출처 없음 (상태가 초안이거나 조사 전)

### 100 최종 보고서

단계 9 최종 보고서 · 상태 조사 전 · 마지막 수정 2026년 11월 11일 오후 1:29

- 연결된 근거 출처 없음 (상태가 초안이거나 조사 전)

### 990 요구사항·시험 설계 통합본 v0.4.1 (보관)

단계 0 관리 · 상태 검토 완료 · 마지막 수정 2026년 11월 11일 오후 1:28

- R-03 Federal Register 90 FR 390 — FMVSS; Occupant Crash Protection, Seat Belt Reminder Systems (최종규칙)
- R-12 Federal Register 91 FR 17144 — Seat Belt Reminder Systems (중간최종규칙)
- R-41 Euro NCAP — Test and Assessment Protocol: Child Presence Detection
- R-14 HC-SR04 Ultrasonic Ranging Module 데이터시트 (ElecFreaks)
- R-20 Smaili 외 (2021) Errors in Distance and Angle Measurements of Ultrasonic Sensor HC-SR04
- R-17 Haq 외 (2026) Accuracy of HC-SR04 Ultrasonic Servo in Servo-Scanned 2D Ranging
- R-16 Arunglabi 외 (2026) HC-SR04 온도 변화 영향 분석 (Tinkercad 시뮬레이션)
- R-15 Rudyk 외 (2025) Influence of environmental factors on the accuracy of the ultrasonic rangefinder
- R-19 Chua 외 (2018) Development of an automatic vehicular heatstroke detection system
- R-22 Toa & Whitehead (2021) — Ultrasonic Sensing Basics (TI SLAA907D)
- R-37 ISO 26262-4:2018 Product development at the system level (ISO 카탈로그 페이지)
- R-24 ISO 26262-6:2018 Product development at the software level (ISO 카탈로그 페이지)
- R-36 Lee, Huang & Lan (2018) HIL test case specification for verification of software safety requirements in the context of ISO 26262
- R-40 NASA — Appendix C: How to Write a Good Requirement
- R-39 NASA — Appendix D: Requirements Verification Matrix
- R-42 NIST/SEMATECH e-Handbook 7.2.4.1 Confidence intervals

## 2. 근거 출처별 사용처

| ID | 근거 출처 | 인용한 문서 수 | 인용한 문서 |
| --- | --- | --- | --- |
| R-01 | NHTSA SCI — Comprehensive Study of 2019 U.S. Pediatric Vehicular Hyperthermia Fatalities (DOT HS 813 360) | 1 | 프로젝트 선정 이유 |
| R-02 | Federal Register 88 FR 65149–65150 (FMVSS, Docket NHTSA-2022-0097) | 1 | 프로젝트 선정 이유 |
| R-03 | Federal Register 90 FR 390 — FMVSS; Occupant Crash Protection, Seat Belt Reminder Systems (최종규칙) | 5 | 프로젝트 선정 이유, 검증의 중요성, 요구사항 설계, 시험 설계, 요구사항·시험 설계 통합본 v0.4.1 (보관) |
| R-04 | Euro NCAP — Safe Driving Occupant Monitoring Protocol | 2 | 프로젝트 선정 이유, 검증의 중요성 |
| R-05 | 기아 2026 타스만 취급설명서 — 후석 승객 알림 시스템 작동 방법 | 2 | 프로젝트 선정 이유, 검증의 중요성 |
| R-06 | Nissan North America — Part 573 Defect Information Report, Recall 14V-138 | 1 | 검증의 중요성 |
| R-07 | NHTSA ODI — Recall Query RQ15-001 Investigation Resume (Nissan 14V-138 후속) | 1 | 검증의 중요성 |
| R-08 | Ariane 5 Flight 501 Failure: Report by the Inquiry Board | 1 | 검증의 중요성 |
| R-09 | NASA — Mars Climate Orbiter Mishap Investigation Board Phase I Report | 1 | 검증의 중요성 |
| R-10 | NIST Planning Report 02-3 (RTI) — The Economic Impacts of Inadequate Infrastructure for Software Testing | 1 | 검증의 중요성 |
| R-11 | NHTSA — 2025 Annual Report (Annual Recalls Report) | 1 | 검증의 중요성 |
| R-12 | Federal Register 91 FR 17144 — Seat Belt Reminder Systems (중간최종규칙) | 4 | 검증의 중요성, 요구사항 설계, 시험 설계, 요구사항·시험 설계 통합본 v0.4.1 (보관) |
| R-13 | NASA — Systems Engineering Handbook, 5.3 Product Verification | 1 | 검증의 중요성 |
| R-14 | HC-SR04 Ultrasonic Ranging Module 데이터시트 (ElecFreaks) | 4 | 센서 사양·사전지식, 요구사항 설계, 시험 설계, 요구사항·시험 설계 통합본 v0.4.1 (보관) |
| R-15 | Rudyk 외 (2025) Influence of environmental factors on the accuracy of the ultrasonic rangefinder | 4 | 센서 사양·사전지식, 요구사항 설계, 시험 설계, 요구사항·시험 설계 통합본 v0.4.1 (보관) |
| R-16 | Arunglabi 외 (2026) HC-SR04 온도 변화 영향 분석 (Tinkercad 시뮬레이션) | 4 | 센서 사양·사전지식, 요구사항 설계, 시험 설계, 요구사항·시험 설계 통합본 v0.4.1 (보관) |
| R-17 | Haq 외 (2026) Accuracy of HC-SR04 Ultrasonic Servo in Servo-Scanned 2D Ranging | 3 | 센서 사양·사전지식, 시험 설계, 요구사항·시험 설계 통합본 v0.4.1 (보관) |
| R-18 | NHTSA (2006) Vehicle Backover Avoidance Technology Study | 1 | 센서 사양·사전지식 |
| R-19 | Chua 외 (2018) Development of an automatic vehicular heatstroke detection system | 4 | 센서 사양·사전지식, 요구사항 설계, 시험 설계, 요구사항·시험 설계 통합본 v0.4.1 (보관) |
| R-20 | Smaili 외 (2021) Errors in Distance and Angle Measurements of Ultrasonic Sensor HC-SR04 | 4 | 센서 사양·사전지식, 요구사항 설계, 시험 설계, 요구사항·시험 설계 통합본 v0.4.1 (보관) |
| R-21 | ElecFreaks — HC-SR04 User Guide | 1 | 센서 사양·사전지식 |
| R-22 | Toa & Whitehead (2021) — Ultrasonic Sensing Basics (TI SLAA907D) | 4 | 센서 사양·사전지식, 요구사항 설계, 시험 설계, 요구사항·시험 설계 통합본 v0.4.1 (보관) |
| R-23 | Shylla et al. (2023) Model in loop (MIL), software in loop (SIL) and hardware in loop (HIL) testing in MBD | 2 | SIL, 검증 방법 비교표 (실물·HIL·SIL) |
| R-24 | ISO 26262-6:2018 Product development at the software level (ISO 카탈로그 페이지) | 5 | SIL, HIL, 검증 방법 비교표 (실물·HIL·SIL), 시험 설계, 요구사항·시험 설계 통합본 v0.4.1 (보관) |
| R-25 | Zhu 외(2025) High-Fidelity Ultrasonic Radar In-the-Loop Accelerated Test for Automatic Parking Systems | 3 | SIL, HIL, 검증 방법 비교표 (실물·HIL·SIL) |
| R-26 | Kim, D.-J., Kim, Y.-C., Jung, D.-H., & Kim, M.-S. (2024). 차량용 3D 초음파 센서 평가를 위한 SILS에 관한 연구 | 2 | SIL, 검증 방법 비교표 (실물·HIL·SIL) |
| R-27 | Fei, Z., Andersson, M., & Tingberg, A. (2024). Correlation of software-in-the-loop simulation with physical testing for autonomous driving | 2 | SIL, 검증 방법 비교표 (실물·HIL·SIL) |
| R-28 | Won, J., Seok, J., Lee, S., & Yoo, J. (2025). 자율주행 차량 시스템 개발을 위한 Software-in-the-Loop Simulation 구현 방법론 | 2 | SIL, 검증 방법 비교표 (실물·HIL·SIL) |
| R-29 | Kim, J., & Choi, Y. (2024). SIL검증과 HIL검증 비교를 통한 SIL검증 유효성 증대 방안 연구 (Study on how to increase SIL test effectiveness by comparing SIL test to HIL test) | 2 | SIL, 검증 방법 비교표 (실물·HIL·SIL) |
| R-30 | Jeong, S., Kwak, Y., & Lee, W. J. (2016). Software-in-the-loop simulation for early-stage testing of AUTOSAR software component | 2 | SIL, 검증 방법 비교표 (실물·HIL·SIL) |
| R-31 | Arsie, I., Betta, G., Capriglione, D., Pietrosanto, A., & Sommella, P. (2014). Functional testing of measurement-based control systems: An application to automotive | 1 | SIL |
| R-32 | Short & Pont (2005) Hardware in the loop simulation of embedded automotive control systems | 2 | HIL, 검증 방법 비교표 (실물·HIL·SIL) |
| R-33 | Isermann, Schaffnit & Sinsel (1998) Hardware-in-the-loop simulation for the design and testing of engine-control systems | 2 | HIL, 검증 방법 비교표 (실물·HIL·SIL) |
| R-34 | Bullock et al. (2004) Hardware-in-the-loop simulation | 2 | HIL, 검증 방법 비교표 (실물·HIL·SIL) |
| R-35 | Nguyen et al. (2020) Hardware-in-the-loop assessment methods (European Guide to Power System Testing, ch. 4) | 2 | HIL, 검증 방법 비교표 (실물·HIL·SIL) |
| R-36 | Lee, Huang & Lan (2018) HIL test case specification for verification of software safety requirements in the context of ISO 26262 | 3 | HIL, 시험 설계, 요구사항·시험 설계 통합본 v0.4.1 (보관) |
| R-37 | ISO 26262-4:2018 Product development at the system level (ISO 카탈로그 페이지) | 4 | HIL, 검증 방법 비교표 (실물·HIL·SIL), 시험 설계, 요구사항·시험 설계 통합본 v0.4.1 (보관) |
| R-38 | Ma et al. (2023) Research on the autonomous parking strategy based on the ultrasonic echo simulator | 2 | HIL, 검증 방법 비교표 (실물·HIL·SIL) |
| R-39 | NASA — Appendix D: Requirements Verification Matrix | 3 | 요구사항 설계, 시험 설계, 요구사항·시험 설계 통합본 v0.4.1 (보관) |
| R-40 | NASA — Appendix C: How to Write a Good Requirement | 3 | 요구사항 설계, 시험 설계, 요구사항·시험 설계 통합본 v0.4.1 (보관) |
| R-41 | Euro NCAP — Test and Assessment Protocol: Child Presence Detection | 3 | 요구사항 설계, 시험 설계, 요구사항·시험 설계 통합본 v0.4.1 (보관) |
| R-42 | NIST/SEMATECH e-Handbook 7.2.4.1 Confidence intervals | 2 | 시험 설계, 요구사항·시험 설계 통합본 v0.4.1 (보관) |
