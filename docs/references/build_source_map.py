#!/usr/bin/env python3
"""document_sources.csv 에서 '문서 대 근거 출처' 지도(source_map.md)를 만든다 (표준 라이브러리만 사용).

  python3 docs/references/build_source_map.py          # source_map.md 생성
  python3 docs/references/build_source_map.py --check  # 생성 결과가 파일과 같은지 확인(CI용)

CSV 의 한 행은 (문서, 근거 출처) 한 쌍이다. 출처가 비어 있는 행은 근거를 아직 연결하지 않은 문서이다.
"""
import collections
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSV_PATH = HERE / "document_sources.csv"
OUT = HERE / "source_map.md"


def build():
    rows = list(csv.DictReader(open(CSV_PATH, encoding="utf-8", newline="")))
    docs = collections.OrderedDict()
    for r in rows:
        d = docs.setdefault(r["v_order"], {"name": r["document"], "stage": r["stage"], "status": r["status"],
                                           "mod": r["last_modified"], "src": []})
        if r["source"]:
            d["src"].append(r["source"])
    first = []
    for d in docs.values():
        for s in d["src"]:
            if s not in first:
                first.append(s)
    sid = {s: f"R-{i:02d}" for i, s in enumerate(first, 1)}
    cited = collections.defaultdict(list)
    for k, d in docs.items():
        for s in d["src"]:
            cited[s].append(d["name"])
    W = []
    w = W.append
    w("# 문서와 근거 출처 지도")
    w("")
    w("> 이 문서는 `docs/references/build_source_map.py`가 `document_sources.csv`에서 자동 생성한다. 직접 고치지 말고 CSV를 고친 뒤 다시 생성할 것.")
    w("")
    n_pairs = sum(len(d["src"]) for d in docs.values())
    w(f"문서 {len(docs)}개, 고유 근거 출처 {len(first)}건, 문서–출처 연결 {n_pairs}건.")
    w("")
    w("## 1. 문서별 근거 출처")
    w("")
    w("| V모델 순서 | 문서 | 단계 | 상태 | 근거 출처 수 |")
    w("| --- | --- | --- | --- | --- |")
    for k, d in docs.items():
        w(f"| {k} | {d['name']} | {d['stage']} | {d['status']} | {len(d['src'])} |")
    w("")
    for k, d in docs.items():
        w(f"### {k} {d['name']}")
        w("")
        w(f"단계 {d['stage']} · 상태 {d['status']} · 마지막 수정 {d['mod']}")
        w("")
        if d["src"]:
            for s in d["src"]:
                w(f"- {sid[s]} {s}")
        else:
            w("- 연결된 근거 출처 없음 (상태가 초안이거나 조사 전)")
        w("")
    w("## 2. 근거 출처별 사용처")
    w("")
    w("| ID | 근거 출처 | 인용한 문서 수 | 인용한 문서 |")
    w("| --- | --- | --- | --- |")
    for s in first:
        names = cited[s]
        w(f"| {sid[s]} | {s.replace('|', '/')} | {len(names)} | {', '.join(names)} |")
    w("")
    return "\n".join(W)


def main():
    text = build()
    if "--check" in sys.argv[1:]:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print("source_map.md 가 CSV와 다름. python3 docs/references/build_source_map.py 로 다시 생성할 것.")
            return 1
        print("통과: source_map.md 일치")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print("작성:", OUT.name)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
