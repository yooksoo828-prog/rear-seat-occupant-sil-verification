# docs/references — 문헌·근거 출처

프로젝트가 수치와 시험 설계를 정할 때 참고한 문헌·법규·표준·데이터시트의 **문서별 연결 지도**이다.
Notion의 "문서 목록" 데이터베이스에서 2026-11-24에 내보낸 CSV를 정리했다(Notion의 마지막 수정일은 2026-11-11).

## 들어 있는 것

| 파일 | 내용 |
| --- | --- |
| [source_map.md](source_map.md) | 문서 13개별 근거 출처, 근거 출처별 사용처(자동 생성) |
| [document_sources.csv](document_sources.csv) | 위 지도의 원본. 한 행이 (문서, 근거 출처) 한 쌍. 비공개 Notion 링크는 제거하고 제목만 남김 |
| [build_source_map.py](build_source_map.py) | CSV에서 지도를 생성·검증 |

문서 13개, 고유 근거 출처 42건, 연결 100건이다. 근거가 연결된 문서는 9개이고, 4개(SIL 설계·결과, SIL의 한계, 업계 동향·결론, 최종 보고서)는 상태가 초안 또는 조사 전이라 연결된 출처가 없다.

## 들어 있지 않은 것 (한계)

- **논문·문서별 요약과 "어떤 수치를 왜 가져왔는가"를 풀어 쓴 본문은 없다.** 내보낸 CSV에는 제목과 연결 관계만 있었고 각 문서·출처 페이지의 본문은 포함되지 않았다.
- **"시험 설계", "요구사항 설계" 문서 본문도 저장소에 없다.** 이 문서들이 인용하는 절(예: 시험 설계 9.4절 통계 판정, 11.2절 시험 목록)은 `docs/29119/`의 문서에서 이름만 참조된다.
- 논문 PDF는 저작권 때문에 저장소에 올리지 않는다. 앞으로도 올리지 않고 서지 정보와 우리가 쓴 요약만 둔다.

## 저장소 안의 다른 근거 기록과의 관계

| 위치 | 무엇이 있나 | 이 지도와의 관계 |
| --- | --- | --- |
| `deliverables/Requirements_Specification_SR-01-14_v1.0.docx` | 참고문헌 8편의 정식 서지, 요구사항 수치별 `[법규]` `[문헌]` `[프로젝트 선택]` 등 근거 구분 | 아래 교차 확인 참조 |
| `docs/29119/environment/TER-01.md` | 대상 치수 조사 기록(Humanetics 사양표, 사이즈코리아 논문 등)과 직접 확인한 범위 | 이 지도에는 없는 출처가 있음(치수 조사용) |
| `docs/29119/design/TM-01-05.md` | 오류 추정 점검표의 근거(NHTSA, Euro NCAP CPD, TI, Haq 2026, Arunglabi 2026, Rudyk 2025) | Haq 2026은 이 지도에 있음 |
| `sil_main/sil/config.py` | 상수별 출처 주석 | |

### 요구사항 명세서의 참고문헌 8편과의 교차 확인
요구사항 명세서의 8편(Arunglabi 2026, Chua 2018, ElecFreaks 데이터시트, Euro NCAP CPD 2024, NHTSA 2025(90 FR 390), Rudyk 2025, Smaili 2021, Toa & Whitehead 2021)은 **모두 이 지도의 근거 출처에 있다.** 반대로 이 지도에는 요구사항 명세서의 참고문헌에 없는 출처가 더 있다(예: Haq 2026, ISO 26262-4·6, Lee 2018, NASA 부록 C·D, NIST e-Handbook). 이들은 시험 설계·요구사항 설계 문서의 방법론 근거이다.

## 남은 일 (필요하면)
문헌별 요약과 시험 설계·요구사항 설계 본문을 옮기려면 Notion에서 해당 페이지를 **하위 페이지 포함**으로 내보내야 한다(Markdown & CSV, "Include subpages"). 이번 내보내기에는 데이터베이스 표만 들어 있었다.

## 갱신 방법
```bash
python3 docs/references/build_source_map.py          # CSV를 고친 뒤 지도를 다시 생성
python3 docs/references/build_source_map.py --check  # 검증(CI가 실행함)
```
