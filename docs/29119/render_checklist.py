#!/usr/bin/env python3
"""outcome 체크리스트 렌더러·검증기 (표준 라이브러리만 사용).

  python3 docs/29119/render_checklist.py          # CSV -> 01_outcome_checklist.md 의 생성 구간 갱신
  python3 docs/29119/render_checklist.py --check  # 갱신하지 않고 검증만 (CI용, 문제가 있으면 종료 코드 1)

검증 내용 (적합성 선언 5절 규칙을 코드로 옮긴 것):
  1) 선언한 7개 프로세스의 outcome 개수가 29119-2:2021 원문과 같음 (7.2 8, 7.3 7, 7.4 5, 8.2 5, 8.3 6, 8.4 4, 8.5 6 = 41)
  2) id 중복 없음, 상태 값이 정해진 다섯 가지 중 하나
  3) '충족'은 reviewer, review_date, approval_ref 가 모두 있어야 함 (증거 없이 충족으로 올리지 못하게 함)
  4) md 의 생성 구간이 CSV 와 일치
"""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
CSV_PATH = HERE / "01_outcome_checklist.csv"
MD_PATH = HERE / "01_outcome_checklist.md"
BEGIN = "<!-- BEGIN GENERATED (render_checklist.py) -->"
END = "<!-- END GENERATED -->"

STATUSES = ["충족", "증거 있음(검토 대기)", "부분", "증거 없음", "해당 없음"]
PROCESSES = {
    "7.2": ("시험 전략과 계획", 8),
    "7.3": ("시험 모니터링과 통제", 7),
    "7.4": ("시험 완료", 5),
    "8.2": ("시험 설계와 구현", 5),
    "8.3": ("시험 환경과 데이터 관리", 6),
    "8.4": ("시험 실행", 4),
    "8.5": ("시험 사건 보고", 6),
}


def cell(text):
    return (text or "").replace("|", "\\|").replace("\n", " ")


def load():
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def validate(rows):
    errors = []
    ids = [r["id"] for r in rows]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        errors.append(f"id 중복: {dup}")
    for p, (_, expected) in PROCESSES.items():
        n = sum(1 for r in rows if r["process"] == p)
        if n != expected:
            errors.append(f"{p}: outcome {n}개 (원문 {expected}개)")
    for r in rows:
        if r["process"] not in PROCESSES:
            errors.append(f"{r['id']}: 알 수 없는 프로세스 {r['process']}")
        if r["status"] not in STATUSES:
            errors.append(f"{r['id']}: 알 수 없는 상태 '{r['status']}'")
        if r["status"] == "충족":
            for col in ("reviewer", "review_date", "approval_ref"):
                if not r[col].strip():
                    errors.append(f"{r['id']}: '충족'인데 {col} 이 비어 있음")
    total = sum(n for _, n in PROCESSES.values())
    if len(rows) != total:
        errors.append(f"전체 {len(rows)}개 (원문 {total}개)")
    return errors


def render(rows):
    out = []
    for p, (title, _) in PROCESSES.items():
        group = [r for r in rows if r["process"] == p]
        out.append(f"## {p} {title} ({len(group)}개)")
        out.append("")
        out.append("| ID | outcome(번역) | 현재 증거 | 상태 | 남은 일 |")
        out.append("| --- | --- | --- | --- | --- |")
        for r in group:
            status = r["status"]
            if r["status_note"].strip():
                status += f"({r['status_note'].strip()})"
            out.append(
                f"| {cell(r['id'])} | {cell(r['outcome'])} | {cell(r['evidence'])} | {cell(status)} | {cell(r['remaining'])} |"
            )
        out.append("")
    out.append("## 현재 집계")
    out.append("")
    head = ["프로세스", "항목 수"] + STATUSES
    out.append("| " + " | ".join(head) + " |")
    out.append("| " + " | ".join(["---"] * len(head)) + " |")
    totals = {s: 0 for s in STATUSES}
    for p in PROCESSES:
        group = [r for r in rows if r["process"] == p]
        counts = {s: sum(1 for r in group if r["status"] == s) for s in STATUSES}
        for s in STATUSES:
            totals[s] += counts[s]
        out.append("| " + " | ".join([p, str(len(group))] + [str(counts[s]) for s in STATUSES]) + " |")
    out.append("| " + " | ".join(["합계", str(len(rows))] + [str(totals[s]) for s in STATUSES]) + " |")
    out.append("")
    out.append(f"집계 확인: 합계 {len(rows)} = " + " + ".join(str(totals[s]) for s in STATUSES) + ". 이 집계는 CSV에서 계산한 값임.")
    out.append("")
    if totals["충족"] == 0:
        out.append("**충족으로 인정된 항목은 아직 0개**. 선언 5절 규칙에 따라 \"완전 적합\"이라고 쓸 수 없음.")
    elif totals["충족"] < len(rows) - totals["해당 없음"]:
        out.append(f"충족 {totals['충족']}개. 남은 항목이 있어 \"완전 적합\"이라고 쓸 수 없음.")
    else:
        out.append("모든 항목이 충족 또는 해당 없음임. 선언 5절 규칙의 충족 여부는 사람이 확인할 것.")
    out.append("")
    return "\n".join(out)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    check_only = "--check" in sys.argv[1:]
    rows = load()
    errors = validate(rows)
    text = MD_PATH.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        errors.append(f"{MD_PATH.name}: 생성 구간 표식이 없음")
    if errors:
        print("검증 실패:")
        for e in errors:
            print("  -", e)
        return 1
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    new = head + BEGIN + "\n" + render(rows) + END + tail
    if check_only:
        if new != text:
            print(f"{MD_PATH.name} 이 CSV와 다름. python3 docs/29119/render_checklist.py 로 다시 생성할 것.")
            return 1
        print(f"통과: outcome {len(rows)}개, md 일치")
        return 0
    MD_PATH.write_text(new, encoding="utf-8", newline="\n")
    print(f"갱신: outcome {len(rows)}개")
    return 0


if __name__ == "__main__":
    sys.exit(main())
