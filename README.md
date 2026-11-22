# 뒷좌석 승객 감지 SIL 검증 — Audit Landing Page

뒷좌석 승객 감지(Rear-Seat Occupant Detection) 소프트웨어를 **SIL(Software-in-the-Loop)** 로 검증한 프로젝트이며, 시험 문서와 형상 관리를
**ISO/IEC/IEEE 29119-3 (Test Documentation)** 에 맞춰 정리했다. 이 페이지는 감사자(auditor)가 먼저 읽는 요약이며, 근거 파일로 바로 이동할 수 있다.

| 구분 | 내용 |
|---|---|
| Document ID | `ISO29119-SIL-RSPD-v1.0` |
| 확정 기준선 | `v1.0` — 2026-11-11 김*수 확정, 결정 D1~D8 |
| 기준선 SHA-256 | `79f21ce910853ee7358d97c031a7553258a9fb2151bdcdaca17db3c1ea205f6d` |
| Git 태그 | `v1.0-baseline` (기준선 확정 커밋) |
| 시험 범위 | 본시험 TC-01 ~ TC-16, 결과 152행 |
| 표준 적합성 | **아직 주장하지 않음.** 29119-2 프로세스 선언·41개 outcome 체크리스트·29119-3 점검표는 [docs/29119/](docs/29119/README.md)에 있으며 충족 인정 14/41개(2026-11-22, PR #5·#7·#9 승인). 전체 적합성은 주장하지 않음 |

## 1. 핵심 문서 바로가기

| 문서 | 설명 |
|---|---|
| [ISO29119_Audit_Report.md](sil_main/results_main/ISO29119_Audit_Report.md) | **통합 감사 보고서** (Test Plan · Test Design/Procedure/Traceability · Execution Log/Incident Report · Completion Report · 부록 152행) |
| [docs/29119/](docs/29119/README.md) | **29119 적합성 문서 일체**: 적합성 선언(29119-2·-3), outcome 체크리스트(41개), 29119-3 Annex A 점검표, 계획·상태·완료 보고서, 시험 모델·케이스·절차, 환경·데이터, 결과·로그, 사건 보고서(IR-01~03) |
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
| INC-03 | TC-11 / 11a-T50-nocomp/TC-04a — 50 °C, 보정 없음, 낮은 화물 R0(5 cm) | 300/300 오검출. 보정 있음(11b-T50-comp)은 0/300(상한 0.994 %) | 음속 변화에 의한 ToF 단축. 보정 채택은 기준선 이후 결정(D3): 2026-11-13 김*수 결정으로 v1.1 기본 구성에 채택(Notion TP-01 PR-2 참조), v1.0 결과는 그대로 |

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

## 5. 제출물 (`deliverables/`)

기말고사 제출용 문서이며, `sil_main/results_main/`의 검증된 결과와 감사 보고서를 요약해 자동 생성한다(원본 결과 파일은 읽기만 하고 수정하지 않음).

| 파일 | 내용 |
|---|---|
| [후석탑승자감지_SIL검증_최종보고서_v1.0.docx](deliverables/후석탑승자감지_SIL검증_최종보고서_v1.0.docx) | 국문 최종보고서(Word): 표지·1~5장(4.5절에 v1.1 재확인 추가), 그림 3종·콜아웃·머리글/바닥글. 152행·87행 전체 표는 감사 보고서 링크로 대체 |
| [후석탑승자감지_SIL검증_발표자료_v1.0.pptx](deliverables/후석탑승자감지_SIL검증_발표자료_v1.0.pptx) | 5~10분 발표용 10슬라이드(16:9, 7번이 v1.1 재확인), KPI 카드·그림 포함, 슬라이드별 발표자 노트 포함 |
| [assets/](deliverables/assets/) | 300 DPI 그림: `fig1_sil_architecture.png`(3단 SIL 구조), `fig2_overall_results.png`(152행 판정 분포), `fig3_tc11_temp_comp.png`(TC-11 온도 보정 효과) |
| [build_deliverables.py](deliverables/build_deliverables.py) | 그림·Word·PowerPoint 생성 스크립트 |

```bash
pip install python-docx python-pptx matplotlib     # 그림의 한글 표시에는 Windows의 Malgun Gothic 폰트가 필요
python deliverables/build_deliverables.py       # 저장소 루트에서 실행. 수치가 결과 파일과 다르면 중단
```

표지의 `학번 / 성명` 칸은 비워 두었으므로 제출 전에 직접 기입한다. 발표자료 9번 슬라이드의 스크린샷 영역에는 GitHub Actions·Issues 화면을 붙여 넣는다.

## 6. 저장소 구성

| 경로 | 내용 |
|---|---|
| `sil_prelim/` | 예비 SIL 시험(모델·결과). 보존용, 수정하지 않음 |
| `sil_main/` | 본시험 TC-01~TC-16 하니스, 기준선, 결과 |
| `sil_main/baseline/` | `baseline_v1.0.json`(확정), `baseline_draft.json`(확정 전 초안, 보존용) |
| `sil_main/results_main/` | 본시험 결과(기준선 v1.0) + 통합 감사 보고서 |
| `sil_main/results_status_before_baseline/`, `results_precheck/`, `results_p08r0/` | 기준선 확정 전 기록·사전점검·추가 시험. **본시험 집계에 포함하지 않음** |
| `deliverables/` | 기말 제출물(Word 보고서, PowerPoint 발표자료)과 생성 스크립트 |
| `.github/workflows/verify.yml` | CI: `selftest.py` |
