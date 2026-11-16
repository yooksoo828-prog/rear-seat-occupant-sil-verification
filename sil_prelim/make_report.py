"""results/results.csv → results/report.md (시험별 기대·실제·일치·원인 표)."""
import csv, json, sys

D = sys.argv[1] if len(sys.argv) > 1 else "results"
rows = list(csv.DictReader(open(f"{D}/results.csv", encoding="utf-8")))
cfg = json.load(open(f"{D}/config.json", encoding="utf-8"))

TITLE = {
    "P-01": "P-01 정상 착석·빈 좌석 기본 동작", "P-02": "P-02 사람과 같은 거리 입력을 만드는 가방",
    "P-03": "P-03 임계값 경계와 초기 히스테리시스(필터 뒤 Δ 직접 주입)", "P-04": "P-04 초기화와 최초 판정",
    "P-05": "P-05 에코 없음과 복구", "P-06": "P-06 입력 갱신 중단·범위 밖 값과 복구",
    "P-07": "P-07 전체 응답 시간", "P-08": "P-08 온도 보정과 잡음·손실 민감도(한 요인씩, 기록만)",
}
MARK = {"True": "일치", "False": "불일치", "기록": "기록"}

out = ["# 예비시험 결과 (P-01~P-08)", "",
       "예비시험은 SIL 구현과 시험 환경의 문제를 찾는 단계이며, 이 결과를 본시험의 통계적 성능 입증으로 쓰지 않음.",
       "대상은 가정 반사면 R0~R3(프로젝트 가정)이며 6세 더미나 인체를 대표하지 않음.", "",
       f"실행 환경: Python {cfg['environment']['python']}, numpy {cfg['environment']['numpy']}, "
       f"난수 {cfg['environment']['rng']}", ""]
seen = set()
for t in TITLE:
    out += [f"## {TITLE[t]}", "", "| 항목 | 기대 결과 | 실제 결과 | 일치 | 원인 구분 |", "|---|---|---|---|---|"]
    for r in rows:
        if r["test"] != t:
            continue
        key = (r["case"].split(" ", 1)[-1] if t == "P-08" else r["case"])
        if t == "P-08" and key in seen:
            continue
        seen.add(key)
        note = f" ({r['note']})" if r["note"] else ""
        out.append(f"| {r['case']} | {r['expected']} | {r['actual']} | {MARK[r['match']]} | {r['cause']}{note} |")
    out.append("")
n = len(rows)
ok = sum(r["match"] == "True" for r in rows)
ng = sum(r["match"] == "False" for r in rows)
out.insert(5, f"항목 {n}개: 일치 {ok}, 불일치 {ng}, 기록 {n - ok - ng} (P-08의 중복 기준 조건 S03은 표에 한 번만 표시)\n")
open(f"{D}/report.md", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
