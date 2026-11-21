# docs/29119 — 29119 적합성 문서

ISO/IEC/IEEE 29119-2:2021(시험 프로세스)과 29119-3:2021(시험 문서)에 대한 이 프로젝트의 적합성 선언과 증거 문서 모음이다.
Notion에서 2026-11-17에 이 저장소로 이전했다. 팀원 실명은 마스킹했다(김*수, 강**엘, 문*호).

> **현재 상태: 표준 적합성을 주장하지 않는다.** 충족으로 인정된 outcome은 10/41개(PR #5·#7 승인 기반)이고, 선언에 대한 팀 합의는 2026-11-20 PR #5 승인으로 받았다.
> **정본 전환**: PR #5(팀원 2명 승인, 2026-11-20 병합)로 이 폴더가 정본이 되었다. Notion 원본은 이전 시점의 읽기 전용 기록으로만 둔다. 각 문서 머리말의 "승인 전까지 정본이 아니다"는 이전 시점의 안내이며 이 병합으로 해소되었다.

## 읽는 순서

| 순서 | 문서 | 내용 |
| --- | --- | --- |
| 1 | [00_conformance_declaration.md](00_conformance_declaration.md) | 29119-2 기준 선언: 7개 프로세스 포함, 6.2 제외, 판정 규칙 |
| 2 | [01_outcome_checklist.md](01_outcome_checklist.md) | 41개 outcome 상태. 원본은 [CSV](01_outcome_checklist.csv)이며 md는 `render_checklist.py`가 생성 |
| 3 | [02_conformance_declaration_29119-3.md](02_conformance_declaration_29119-3.md) | 29119-3 기준 선언(신규 초안) |
| 4 | [03_29119-3_conformance_check.md](03_29119-3_conformance_check.md) | Clause 5·Annex A shall 항목 점검표(신규 초안) |

## 산출물 (29119-3 정보 항목)

| 폴더 | 문서 | 29119-3 |
| --- | --- | --- |
| [plan/](plan/TP-01.md) | TP-01 시험 계획서 | 7.2 |
| [status/](status/TS-01.md) | TS-01 시험 상태 보고서 #1 · [TS-02](status/TS-02.md) #2(2026-11-21 신규) | 7.3 |
| [completion/](completion/TCR-01.md) | TCR-01 시험 완료 보고서(중간본) | 7.4 |
| [design/](design/TM-01-05.md) | TM-01~05 시험 모델·커버리지 항목 | 8.2 |
| [design/](design/TCS-01.md) | TCS-01 시험 케이스 명세 | 8.3 |
| [design/](design/TPS-01.md) | TPS-01 시험 절차 명세 | 8.4 |
| [environment/](environment/TER-01.md) | TER-01 시험 데이터·환경 요구사항 | 8.5, 8.6 |
| [environment/](environment/TRR-01.md) | TRR-01 데이터·환경 준비 상태 보고서 | 8.7, 8.8 |
| [results/](results/TRS-01.md) | TRS-01 실제 결과와 시험 결과 | 8.9 |
| [results/](results/V1.0-vs-V1.1.md) | v1.0 대 v1.1 결과 비교(자동 생성) | 8.9 보조 |
| [results/](results/TEL-01.md) | TEL-01 시험 실행 로그 | 8.10 |
| [incidents/](incidents/IR-01.md) | IR-01 · [IR-02](incidents/IR-02.md) · [IR-03](incidents/IR-03.md) 사건 보고서 | 8.11 |

## 체크리스트 갱신 방법

```bash
# CSV를 고친 뒤 md를 다시 생성
python3 docs/29119/render_checklist.py
# 검증만 (CI가 실행함)
python3 docs/29119/render_checklist.py --check
```

"충족"으로 바꾸려면 CSV의 `reviewer`, `review_date`, `approval_ref`(승인된 PR 링크)를 모두 채워야 한다. 비어 있으면 검증이 실패한다.

## 이 이전에서 하지 않은 것

- 산출물의 내용과 판정은 수정하지 않았다(이전 안내와 이전자 주석 추가, 실명 마스킹, 표 형식 변환만).
- 팀 합의·승인·전달 기록을 만들어 넣지 않았다. 해당 항목은 "미실시"로 남아 있다.
- 카카오톡 캡처 등 대화 원본은 저장소에 올리지 않았다. "원본 첨부 없음" 표기는 그대로 둔다.
