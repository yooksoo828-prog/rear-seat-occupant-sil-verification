# 뒷좌석 승객 감지 SIL 검증 — Audit Landing Page

뒷좌석 승객 감지(Rear-Seat Occupant Detection) 소프트웨어를 **SIL(Software-in-the-Loop)** 로 검증한 프로젝트이며, 시험 문서와 형상 관리를
**ISO/IEC/IEEE 29119-3 (Test Documentation)** 에 맞춰 정리했다. 이 페이지는 감사자(auditor)가 먼저 읽는 요약이며, 근거 파일로 바로 이동할 수 있다.

| 구분 | 내용 |
|---|---|
| Document ID | `ISO29119-SIL-RSPD-v1.0` |
| 확정 기준선 | `v1.0` — 2026-11-11 김윤수 확정, 결정 D1~D8 |
| 기준선 SHA-256 | `79f21ce910853ee7358d97c031a7553258a9fb2151bdcdaca17db3c1ea205f6d` |
| Git 태그 | `v1.0-baseline` (기준선 확정 커밋) |
| 시험 범위 | 본시험 TC-01 ~ TC-16, 결과 152행 |

## 1. 핵심 문서 바로가기

| 문서 | 설명 |
|---|---|
| [ISO29119_Audit_Report.md](sil_main/results_main/ISO29119_Audit_Report.md) | **통합 감사 보고서** (Test Plan · Test Design/Procedure/Traceability · Execution Log/Incident Report · Completion Report · 부록 152행) |
| [baseline_v1.0.json](sil_main/baseline/baseline_v1.0.json) | 확정 기준선(D1~D8 기록 포함) |
| [trace_SR_TC_result.csv](sil_main/results_main/trace_SR_TC_result.csv) | 요구사항(SR) → 시험(TC) → 결과 추적성 |
| [baseline_verification.csv](sil_main/results_main/baseline_verification.csv) | 실행 전 기준선↔코드 값 비교 87개 항목 |
| [tc11_side_by_side.csv](sil_main/results_main/tc11_side_by_side.csv) | TC-11 온도(0·20·50 °C)·보정 유/무 나란히 보기 |

## 2. ISO/IEC/IEEE 29119-3 산출물 대응표

| 29119-3 산출물 | 이 저장소의 대응 파일 |
|---|---|
| Test Plan (테스트 계획서) | 감사 보고서 Chapter 1, [baseline_v1.0.json](sil_main/baseline/baseline_v1.0.json) |
| Test Design / Test Procedure Specification | 감사 보고서 Chapter 2, [sil_main/README.md](sil_main/README.md), `sil_main/run_main.py`, `sil_main/main_lib/` |
| Requirements Traceability | [trace_SR_TC_result.csv](sil_main/results_main/trace_SR_TC_result.csv), 감사 보고서 2.3절 |
| Test Environment / Data Requirements | `sil_main/results_main/config.json` (Python·NumPy·RNG·시드 규칙), `sil_main/sil/` |
| Actual Results / Test Result | `sil_main/results_main/summary.csv`, `sil_main/results_main/report.md` |
| Test Execution Log | `sil_main/results_main/trials.csv`, `output_log.csv`, `events.csv` (측정 로그 `trial_samples.csv.gz`는 아래 주의 참고) |
| Test Incident Report | 감사 보고서 3.3절 (INC-01~03) 및 GitHub Issues |
| Test Completion Report | 감사 보고서 Chapter 4 |
| 사전 상태 기록 (참고, 집계 제외) | `sil_main/results_status_before_baseline/`, `sil_main/results_precheck/`, `sil_main/results_p08r0/` |

## 3. 검증 결과 요약

| 지표 | 값 |
|---|---|
| 기준선↔코드 값 비교 | **87 / 87 일치** |
| 목표 충족(통계 확인) | **49** (단측 95% 정확 이항 상한 ≤ 목표) |
| 일치 (결정적 시험) | **27** |
| 기준 충족(전 시행) | **12** |
| 불합격 (문서화된 이상 항목) | **3** — INC-01·02·03 |
| 미실행 (문서화) | **4** — O-A, O-B, O-C 원 조건, TC-12(O-S) |
| 기록(합격 판정 없음) / 가정 기반 민감도 기록 | 44 / 13 (합격 건수에 포함하지 않음) |
| 합계 | 152행 |
| **SR-09** | **부분 커버 — 전체 충족 선언 보류(D3)**. TC-11은 빈 좌석·R2·R0, 0·20·50 °C, 보정 유/무만 다룸 |

### 이상 항목 (불합격 3건)

| ID | 조건 | 결과 | 성격 |
|---|---|---|---|
| INC-01 | TC-04 / 04b-1 — 점유 대상과 같은 높이(R1 = 20 cm)의 정지 화물 | 300/300 오검출 (목표 ≤ 5 %) | 단일점 거리 센서의 구조적 한계 |
| INC-02 | TC-04 / 04b-2 — 정지 화물(R1) 대 움직이는 점유 대상(±1.0 cm, 0.25 Hz) | 300/300 오검출 (목표 ≤ 5 %) | 위와 같은 원인. 목표·합격선을 사후에 바꾸지 않고 기록(D6, D7) |
| INC-03 | TC-11 / 11a-T50-nocomp/TC-04a — 50 °C, 보정 없음, 낮은 화물 R0(5 cm) | 300/300 오검출. 보정 있음(11b-T50-comp)은 0/300(상한 0.994 %) | 음속 변화에 의한 ToF 단축. 보정 채택은 후속 결정(D3) |

### 한계와 주의

- 가상 반사면 R0~R3(5/20/40/60 cm)는 실제 더미·인체·가방 치수가 아니다(D1). 결과는 **SIL 모델과 입력 분포에 대한 결과**이며 실제 센서 성능을 입증하지 않는다.
- 측정 로그 `trial_samples.csv.gz`(압축 해제 약 100 MB)는 `.gitignore`의 `*.csv.gz` 규칙에 따라 **저장소에 포함되지 않는다**. 요약·추적성·검증·보고서 파일은 모두 추적한다.
- `sil_prelim/`(예비시험)과 `sil_main/results_*` 결과 파일은 수정하지 않는다. 합격선·목표·시행 수는 기준선 v1.0 그대로이다.

## 4. 재현 명령

필요: Python 3.10 이상, numpy. 모든 명령은 `sil_main/` 폴더에서 실행한다(`../sil_prelim/`이 옆에 있어야 함).

```bash
cd sil_main
python3 -m pip install numpy

# 1) 코드 자체 점검 — 통계 수치, 예비시험 재현, 재현성, 집계 재계산, 기준선 SHA-256·87항목 확인
#    (본시험은 임시 복사본에서 실행되므로 저장소의 results_main/ 은 바뀌지 않음)
python3 selftest.py

# 2) 감사 보고서 재생성 — results_main/ 을 읽기만 하며 ISO29119_Audit_Report.md 를 만듦
python3 build_iso29119_report.py
```

```bash
# 3) 본시험 재실행 (선택) — 기준선 v1.0이 확정되어 있어야 함
#    주의: results_main/ 을 지우고 다시 만들므로 ISO29119_Audit_Report.md 도 사라짐 → 이어서 2)를 다시 실행
python3 run_main.py main
python3 build_iso29119_report.py
```

CI(`.github/workflows/verify.yml`)는 `main` 브랜치에 push·pull request 할 때마다 Python 3.11에서 `selftest.py`를 실행한다.

## 5. 저장소 구성

| 경로 | 내용 |
|---|---|
| `sil_prelim/` | 예비 SIL 시험(모델·결과). 보존용, 수정하지 않음 |
| `sil_main/` | 본시험 TC-01~TC-16 하니스, 기준선, 결과 |
| `sil_main/baseline/` | `baseline_v1.0.json`(확정), `baseline_draft.json`(확정 전 초안, 보존용) |
| `sil_main/results_main/` | 본시험 결과(기준선 v1.0) + 통합 감사 보고서 |
| `sil_main/results_status_before_baseline/`, `results_precheck/`, `results_p08r0/` | 기준선 확정 전 기록·사전점검·추가 시험. **본시험 집계에 포함하지 않음** |
| `.github/workflows/verify.yml` | CI: `selftest.py` |
