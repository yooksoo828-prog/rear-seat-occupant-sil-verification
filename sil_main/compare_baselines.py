#!/usr/bin/env python3
"""기준선 두 개의 본시험 결과를 비교해 마크다운 문서를 만든다 (표준 라이브러리만 사용).

  python3 compare_baselines.py results_main results_v1.1 ../docs/29119/results/V1.0-vs-V1.1.md

입력 폴더는 읽기만 하고 수정하지 않는다. 출력에는 시각을 넣지 않아 같은 입력이면 같은 문서가 나온다.
"""
import collections
import csv
import gzip
import json
import sys
from pathlib import Path


def load_csv(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main(a_dir, b_dir, out):
    a, b = Path(a_dir), Path(b_dir)
    ca = json.load(open(a / "config.json", encoding="utf-8"))["config"]
    cb = json.load(open(b / "config.json", encoding="utf-8"))["config"]
    sa, sb = load_csv(a / "summary.csv"), load_csv(b / "summary.csv")
    key = lambda r: (r["tc"], r["cond_id"], r["metric"])
    same_keys = [key(r) for r in sa] == [key(r) for r in sb]
    W = []
    w = W.append
    w("# 기준선 v1.0 대 v1.1 본시험 결과 비교")
    w("")
    w("> 이 문서는 `sil_main/compare_baselines.py`가 두 결과 폴더를 읽어 자동 생성한다. 직접 고치지 말고 스크립트로 다시 생성할 것.")
    w("")
    w("## 1. 비교 대상")
    w("")
    w("| 항목 | v1.0 | v1.1 |")
    w("| --- | --- | --- |")
    w(f"| 결과 폴더 | `{a.name}/` | `{b.name}/` |")
    w(f"| 기준선 파일 | `{ca.get('_baseline_file')}` | `{cb.get('_baseline_file')}` |")
    w(f"| 기준선 SHA-256 | `{ca.get('_baseline_sha256','')[:16]}…` | `{cb.get('_baseline_sha256','')[:16]}…` |")
    w(f"| environment.temp_comp_base | {ca['environment']['temp_comp_base']} | {cb['environment']['temp_comp_base']} |")
    w(f"| 실행 명령 | `{ca.get('_command')}` | `{cb.get('_command')}` |")
    w("")
    w("바꾼 것은 `environment.temp_comp_base`(온도 보정 기본값) 하나뿐이다. 입력, 난수 시드, 반복 횟수, 합격 기준은 같다.")
    w("")
    w("## 2. 판정 수준 비교 (summary.csv)")
    w("")
    w(f"- 결과 행 수: v1.0 {len(sa)}행, v1.1 {len(sb)}행. 행 순서·조건 일치: {'예' if same_keys else '**아니오**'}")
    ca_cnt = collections.Counter(r["status"] for r in sa)
    cb_cnt = collections.Counter(r["status"] for r in sb)
    w("")
    w("| 상태 | v1.0 | v1.1 |")
    w("| --- | --- | --- |")
    for s in sorted(set(ca_cnt) | set(cb_cnt)):
        w(f"| {s} | {ca_cnt.get(s, 0)} | {cb_cnt.get(s, 0)} |")
    diff = []
    if same_keys:
        for i, (x, y) in enumerate(zip(sa, sb), 1):
            if (x["k"], x["n"], x["status"], x["actual"]) != (y["k"], y["n"], y["status"], y["actual"]):
                diff.append((i, x, y))
    w("")
    w(f"**오류 건수(k), 시행 수(n), 상태, 실제 결과가 달라진 행: {len(diff)}개**")
    if diff:
        w("")
        w("| 행 | TC | 조건 | 지표 | k/n v1.0 | k/n v1.1 | 상태 v1.0 | 상태 v1.1 |")
        w("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for i, x, y in diff:
            w(f"| {i} | {x['tc']} | {x['cond_id']} | {x['metric']} | {x['k']}/{x['n']} | {y['k']}/{y['n']} | {x['status']} | {y['status']} |")
    ta, tb = load_csv(a / "tc11_side_by_side.csv"), load_csv(b / "tc11_side_by_side.csv")
    w("")
    w(f"TC-11 온도·보정 나란히 보기(`tc11_side_by_side.csv`): {'v1.0과 v1.1이 같음' if ta == tb else '**달라짐**'} ({len(ta)}행).")
    w("")
    w("## 3. 시행 수준 비교 (trials.csv)")
    w("")
    ra, rb = load_csv(a / "trials.csv"), load_csv(b / "trials.csv")
    k2 = lambda r: (r["tc"], r["cond"], r["trial"])
    ok_keys = [k2(r) for r in ra] == [k2(r) for r in rb]
    w(f"- 시행 행 수: v1.0 {len(ra)}, v1.1 {len(rb)}. 순서·키 일치: {'예' if ok_keys else '**아니오**'}")
    if ok_keys:
        res_cols = ["final_output", "ok", "result", "out_eval", "unknown_entered", "wrong_valid_output", "flips"]
        res_cols = [c for c in res_cols if c in ra[0]]
        n_res = sum(1 for x, y in zip(ra, rb) if any(x[c] != y[c] for c in res_cols))
        n_any = sum(1 for x, y in zip(ra, rb) if any(x[c] != y[c] for c in x))
        w(f"- 결과 열({', '.join(res_cols)})이 달라진 시행: **{n_res}개** / {len(ra)}")
        w(f"- 어느 열이든 달라진 시행(시각·환산값 포함): {n_any}개 / {len(ra)}")
    w("")
    w("## 4. 측정 수준 비교 (trial_samples.csv.gz)")
    w("")
    n = chg = 0
    err_a = err_b = 0.0
    n_err = 0
    with gzip.open(a / "trial_samples.csv.gz", "rt", encoding="utf-8", newline="") as fa, \
            gzip.open(b / "trial_samples.csv.gz", "rt", encoding="utf-8", newline="") as fb:
        ha, hb = csv.DictReader(fa), csv.DictReader(fb)
        for x, y in zip(ha, hb):
            n += 1
            if x["d_conv_cm"] != y["d_conv_cm"]:
                chg += 1
            if x["d_conv_cm"] and y["d_conv_cm"] and x["d_true_cm"] and x["noise_cm"]:
                truth = float(x["d_true_cm"]) + float(x["noise_cm"])
                err_a += abs(float(x["d_conv_cm"]) - truth)
                err_b += abs(float(y["d_conv_cm"]) - truth)
                n_err += 1
    w(f"- 측정 샘플 수: {n}")
    w(f"- 환산 거리(`d_conv_cm`)가 달라진 샘플: {chg}개")
    if n_err:
        w(f"- 유효 샘플 {n_err}개에서 **환산 오차 평균**(환산 거리와 잡음 포함 참 거리의 차이의 절댓값): v1.0 {err_a / n_err:.3f} cm, v1.1 {err_b / n_err:.3f} cm")
        w("  (TC-11의 보정 없음 조건처럼 온도가 달라지는 시험이 섞여 있어 이 평균은 전체 합계이며 개별 조건의 값이 아니다.)")
    w("")
    w("## 5. 읽는 법")
    w("")
    w("- 온도 보정을 기본값으로 켜도 **152개 결과 행의 판정은 하나도 바뀌지 않았는지**를 2절이 보여 준다.")
    w("- 4절은 보정이 실제로 적용되어 측정값이 달라졌는지를 보여 준다. 판정이 같아도 이 값이 달라야 보정이 적용된 것이다.")
    w("- 이 비교는 SIL 모델과 가상 반사면 입력에 대한 것이며 실제 센서의 성능을 뜻하지 않는다.")
    w("- v1.1은 추가 시험 케이스, 원 조건 대상 치수, H_s 110 cm 조건을 포함하지 않는다(`baseline_v1.1.json`의 `v1_1_scope` 참조).")
    w("")
    Path(out).write_text("\n".join(W), encoding="utf-8", newline="\n")
    print(f"작성: {out} (판정 변화 {len(diff)}행)")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    main(*sys.argv[1:])
