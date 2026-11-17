# 뒷좌석 승객 감지 SIL — 본시험 준비 (TC-01~TC-16)

시험 설계 11~12절의 본시험을 구현한 코드와 현재까지의 결과임. 예비시험 코드·결과(`../sil_prelim/`)는 바꾸지 않고 보존함.

## 현재 상태

- **기준선 v1.0 확정(2026-11-11, 사용자 결정 D1~D8)** 후 본시험을 실행했음. 기준선은 `baseline/baseline_v1.0.json`(sha256은 `results_main/config.json`에 기록)이며 실행 전에 파일 값과 코드에 들어간 값을 비교해 `results_main/baseline_verification.csv`에 남김(87개 항목, 하나라도 다르면 중단).
- 결과: `results_main/`(`summary.csv` = 시험별 결과표, `report.md` = 읽기용 사본, `tc11_side_by_side.csv`, `coverage_TC11.csv`, `trace_SR_TC_result.csv`).
- `results_precheck/`(기준선 확정 전 점검, 판정 아님)와 `results_p08r0/`(추가 시험, 판정 없음)는 본시험 집계에 포함하지 않음. `results_status_before_baseline/`은 기준선 확정 전 상태 기록(모든 TC 미실행)이며 보존용임.
- 입력이 없는 케이스만 미실행: O-A·O-B·O-C 원 조건(가상 반사면 대체 조건으로 TC-02a·02b·03은 실행), TC-12(O-S).

## 폴더

| 경로 | 내용 |
|---|---|
| `sil/` | 센서 모델·판단 프로그램·시나리오·평가 함수. 예비시험 패키지를 복사해 아래 3가지만 추가함(기본값은 예비시험과 같음). 확장 후에도 예비시험 결과 5개 파일이 바이트 단위로 같음(`selftest.py`) |
| `main_lib/engine.py` | TC-01~TC-16과 P-08-R0 구현(입력·정답·기록 신호·합격 기준) |
| `main_lib/stats.py` | 단측 95% 정확 이항 상한, 목표 충족(통계 확인)·관측 충족(통계 미확인)·불합격 판정 |
| `main_lib/decisions.py` | 결정 항목 D1~D8, TC별 차단 결정, SR→TC 연결 |
| `baseline/baseline_v1.0.json` | 확정 기준선(D1~D8 기록 포함) |
| `baseline/baseline_draft.json` | 확정 전 초안(보존용) |
| `run_main.py` | 실행기 |
| `selftest.py` | 코드 자체 점검 |
| `results_main/` | 본시험 결과(기준선 v1.0) |
| `results_status_before_baseline/` | 기준선 확정 전 상태 기록(보존용) |
| `results_precheck/` | 사전점검 결과 |
| `results_p08r0/` | 추가 시험 P-08-R0 결과 |

`sil/`에 추가한 것: ① `Detector.db_basis`('rx' = 후보 첫 수신 시각 기준(예비시험과 같음), 'req' = 후보 첫 측정 요청 시각 기준) ② `Scenario.loss_schedule`(TC-06에서 기울임 적용 시점에 손실 확률을 바꿈) ③ `on_sample`/`decide`에 요청 시각 전달. 'req'는 본시험 전 결정 항목 D2의 선택지로 넣은 것이며 기본값은 'rx'임.

## 실행 방법

필요: Python 3.10 이상, numpy. `sil_main/` 폴더에서 실행함.

```
python3 run_main.py status               # 기준선 확정 전 상태 기록 → results_status_before_baseline/
python3 run_main.py precheck             # 소규모 사전점검(판정 아님) → results_precheck/
python3 run_main.py additional           # 추가 시험 P-08-R0 → results_p08r0/
python3 run_main.py all                  # 위 셋
python3 selftest.py                      # 통계 수치·예비시험 재현·재현성·집계 점검
python3 run_main.py main                 # 본시험. baseline/baseline_v1.0.json이 확정되어야 실행
```

본시험 실행 순서: 결정적 시험(TC-07, 13, 14, 15, 08) → 무작위 시험(TC-01~06, 07c, 09, 10, 11, 12) → TC-16(로그 간격은 앞선 로그 사용). `main`은 `results_main/`을 지우고 다시 만듦. 결과를 본 뒤 반복 횟수나 합격 기준을 바꾸지 않음. 설정·구현을 바꿔야 하면 변경 사유와 전후를 기록하고 baseline 버전을 올림.

## 재실행 명령 (`sil_main/` 폴더에서, `../sil_prelim/`이 옆에 있어야 함)

```
python3 selftest.py                 # 통계 수치, 예비시험 재현, 사전점검·본시험 두 번 실행 동일, 집계 재계산
python3 run_main.py main            # 본시험 → results_main/ (약 15초)
python3 run_main.py precheck        # 사전점검 → results_precheck/
python3 run_main.py additional      # P-08-R0 → results_p08r0/
```

이번에 실제로 실행한 순서: 기준선 v1.0 파일 저장 → `python3 run_main.py main`(값 확인 87개 일치 후 실행, 결과 행 152개) → `python3 run_main.py precheck`(코드 라벨·열 추가 뒤 재생성, 수치·상태는 이전과 같음) → `python3 selftest.py`(전부 통과). 본시험을 두 번 실행하면 요약·시행·출력·사건 파일이 같고, 측정 로그는 압축 해제 내용이 같음(gzip 헤더 시각은 다름).

## 결과 파일

| 파일 | 내용 |
|---|---|
| `summary.csv` | 조건·검사 단위 결과: 관련 SR, 종류(rate·all_trials·deterministic·record·notrun), n, 오류 k, 관측 비율, 단측 95% 상한, 목표, 상태, 기대, 실제, 반사면 표시, 비고 |
| `trials.csv` | 시행별 정답·출력·결과, 첫 유효 판정 시각, 사건 시각 t_gt, 새 출력 시각, 응답 시간, 판정에 쓴 샘플의 요청 시각·수신 시각, 뒤집힘, 복구 시간, 시드 |
| `trial_samples.csv.gz` | 측정 로그: 측정 요청 시각, 수신 시각, 상태·원인, 참 거리, 잡음, 펄스 폭, 환산 거리, 중앙값, Δ, 출력, 정답, 시드 |
| `output_log.csv`, `events.csv` | 출력이 바뀐 시각, UNKNOWN 진입·복구 사건 |
| `trace_SR_TC_result.csv` | SR→TC→결과 상태 집계 |
| `baseline_verification.csv` | 실행 전 기준선·코드 값 비교(87개 항목) |
| `tc11_side_by_side.csv`, `coverage_TC11.csv` | TC-11 온도·보정 구성별 나란히 보기와 실제로 다룬 조건 |
| `report.md` | 시험별 결과표 읽기용 사본 |
| `config.json` | 사용한 설정, Python·numpy 버전, 난수 생성기, 시드 규칙 |
| `tdb_comparison.csv`(사전점검) | T_db 후보별(0 s, 0.5 s 수신 기준, 0.5 s 요청 기준) 결과 비교 |
| `p08_r0_results.csv`(추가 시험) | P-08-R0: 잡음 없는 계산값, 잡음 없는 시행, 무작위 시행을 따로 기록 |

시드 규칙: `seed = base_seed * 2**64 + crc32('<접두>/<TC>/<조건>') * 2**20 + 시행 번호`(base_seed 20261111, 사전점검 접두 `PRE/`). 조건마다 독립이며 시행 수 제한이 없음(예비시험 규칙은 시행 100회 이상에서 이웃 조건과 겹칠 수 있어 바꿈). 잡음·손실 난수는 서로 독립임.

## 상태 표기

| 상태 | 쓰임 |
|---|---|
| 목표 충족(통계 확인) / 관측 충족(통계 미확인) / 불합격 | 비율 조건. 관측 비율과 단측 95% 정확 이항 상한을 목표와 비교(시험 설계 9.4절). 오류율은 독립 시행 수 기준이며 UNKNOWN은 분모에 포함하고 미확정률로 따로 계산 |
| 기준 충족(전 시행) / 불합격 | 모든 시행이 기준을 만족해야 하는 조건(응답 시간, 뒤집힘, 최초 판정, 복구). 미충족 시행 수와 단측 95% 상한을 함께 기록 |
| 일치 / 불일치 | 결정적 시험의 기대 출력 비교 |
| 기록(합격 판정 없음), 가정 기반 민감도 기록 | 참고 시험, 민감도 수준, 계획 밖 참고 |
| 미실행 | 기준선 미확정이거나 입력 정의가 없는 항목. 사유를 함께 기록 |
| `점검 · …` | 사전점검 결과. 소규모이며 판정이 아님 |

## 범위와 한계

- 가정 반사면 R0~R3(프로젝트 가정, 가상 반사면)은 6세 더미·인체·실제 가방의 치수가 아니며 결과표의 `surface` 열에 표시함. TC-02a·02b·03은 R1·R2·R3 '가상 반사면 대체 조건'이고 O-A·O-B·O-C 원 조건의 결과가 아님.
- 시간 기준: T_db 0.5 s는 측정 요청 시각 기준(db_basis=req)이며 최초 판정·복구 기한과 응답 시간은 결과 수신·처리 시각으로 검증함. 로그에 요청·수신 시각을 모두 남김.
- TC-11은 빈 좌석·R2·R0, 0·20·50 °C, 보정 무·유만 다룸. SR-09 전체 충족 판정은 하지 않음. 온도 보정 채택 여부는 본시험 후 결정(기준선 v1.0 시점). 이후 2026-11-13 김윤수 결정으로 v1.1 기본 구성에 채택됨(Notion TP-01 PR-2 참조). v1.0 기준선과 결과는 바뀌지 않음.
- 후속 검토: 온도 보정 채택(2026-11-13 결정됨, v1.1 반영·재확인 대기), 초기 빈 좌석 보정(d_empty), O-A/B/C/S 치수, 차량 시동과 센서 전원의 관계, 착석 위치 분포.
- 가방과 사람의 거리 이력이 같으면 거리 기반 알고리즘은 구분하지 못함. TC-04b의 불합격은 목표를 바꾸지 않고 기록하며 7단계 'SIL의 한계'에서 다룸.
- SIL 결과는 사용한 모델과 입력 분포에 대한 결과이며 실제 센서의 성능을 입증하지 않음.
