"""본시험 실행기 (시험 설계 11절, TC-01~TC-16) — 예비시험 코드(sil_prelim)와 별도 폴더·별도 결과.

사용법
  python3 run_main.py status                 기준선 확정 전 상태(확인표·결정 항목·TC별 미실행 사유)를 results_status_before_baseline/에 기록
  python3 run_main.py precheck               소규모 사전점검(판정 아님) → results_precheck/
  python3 run_main.py additional             추가 시험 P-08-R0(판정 없음)   → results_p08r0/
  python3 run_main.py main [baseline.json]   본시험. baseline_v1.0.json이 확정(confirmed=true)이고 빈 값이 없을 때만 실행 → results_main/
  python3 run_main.py all                    status + precheck + additional

본시험은 baseline/baseline_v1.0.json이 확정되기 전에는 실행하지 않으며, 그 경우 모든 TC를 '미실행'과 사유로 기록함.
"""
import csv, hashlib, json, os, platform, re, shutil, sys
from dataclasses import replace

import numpy as np

from sil.config import PrelimConfig, Geometry, SensorModel, Detector, Evaluation
from main_lib import engine as E
from main_lib.engine import Runner, write_csv
from main_lib import decisions as DEC

HERE = os.path.dirname(os.path.abspath(__file__))
DRAFT = os.path.join(HERE, "baseline", "baseline_draft.json")
V1 = os.path.join(HERE, "baseline", "baseline_v1.0.json")

# 기준선 확인표: (항목, 값, 근거 문서·절, 상태, 적용 TC, 결정)
BASELINE_TABLE = [
    ("센서 높이 H_s", "100 cm", "시험 설계 4.2, 10.2, 12절", "구현 설정(예비), 12절 미확정", "전 TC", ""),
    ("빈 좌석 기준 d_empty", "100 cm(H_s 그대로) 또는 초기 보정 측정값", "시험 설계 4.2·12절, SIL 5.5절", "미정", "전 TC", "D4"),
    ("가정 반사면 R0/R1/R2/R3", "5 / 20 / 40 / 60 cm", "시험 설계 4.2", "프로젝트 가정(더미·인체·가방 치수 아님)", "TC-04a, TC-11, 점검", ""),
    ("O-A·O-B·O-C·O-S 반사면", "미확보(TBR)", "시험 설계 4.3·12절 / SIL 설계·결과 2.1절", "충돌: SIL 2.1절은 참고 치수를 제시하나 시험 설계 미반영, 출처 미검증", "TC-02, 03, 04b, 05, 06, 08a, 09, 10, 11, 12, 13a, 14, 15", "D1"),
    ("착석 위치 분포", "TBR", "시험 설계 12절", "미정", "TC-02, 03", "D1"),
    ("기준 온도·보정 구성(TC-01~10)", "미정", "시험 설계 8.1·11.2(TC-11)·12절, SIL 5.5절", "미정", "TC-01~10", "D3"),
    ("온도 보정의 요구사항 여부", "미정", "시험 설계 12절", "미정", "TC-11, SR-09", "D3"),
    ("Δ_on / Δ_off / 초기 구간 기준", "10 / 5 / 7.5 cm", "시험 설계 10.2, 12절", "구현 설정(예비)", "TC-07, 전 정적 TC", ""),
    ("필터 창 k, M, T_to, T_stale", "5, 5회, 30 ms, 1.0 s", "시험 설계 10.2, 12절", "구현 설정(예비)", "TC-07, 13~15", ""),
    ("T_recover, T_first, t_eval, 확인 구간", "1.0 s, 1.0 s, 3.0 s, 1.0 s", "시험 설계 10.2, 12절", "구현 설정(예비)", "TC-08, 09, 13, 15", ""),
    ("디바운스 T_db와 시간 기준", "0 s / 0.5 s, 수신 기준 / 요청 기준", "시험 설계 10.2·12절, SIL 3.2·5.5절", "미정", "TC-07~10, 13~15", "D2"),
    ("측정 주기", "100 ms(> 60 ms)", "시험 설계 10.2, SR-06", "구현 설정(예비), 하한은 [문헌]", "TC-16, 전 TC", ""),
    ("기준 잡음·손실·편향·기울기", "σ = 1 cm, p_loss = 0, b = 0, φ = 0°", "시험 설계 8절", "문서 명시(프로젝트 가정)", "전 TC", ""),
    ("민감도 수준", "σ {1, 0.5, 2}, p_loss {0, 0.1, 0.3, 0.5}, b {0, 2, 5}, φ {0, 15, 30, 45}°(p_loss {0, 0.3, 0.7, 1.0})", "시험 설계 8.2~8.4", "수준은 문서 명시. 조합 방식·05a/05b 구분·07c 대상은 문서에 없음", "TC-05, 06, 07c", "D7"),
    ("TC-04b-2 움직임 가정", "문서에 값 없음(예비시험: ±1 cm, 0.25 Hz)", "시험 설계 5·8절", "미정", "TC-04b-2", "D7"),
    ("반복 횟수", "TC-02·03·05 기준 300, TC-01·04·08·09·10 60, 수준당 60", "시험 설계 11.2, 9.4, 12절", "계획값. SR-14 통계 확인을 위한 300회 이상 여부 미정", "TC별", "D5"),
    ("신뢰수준·방법", "단측 95% 정확 이항", "시험 설계 9.4절", "문서 명시(프로젝트 선택)", "판정 전체", ""),
    ("달성 목표", "미검출 1%, 오검출 5%, 응답 3 s, 뒤집힘 0회, 미확정 1%", "시스템 요구사항 명세서 SR-02~04·07(b)·08·14", "잠정, 12절에서 고정 필요", "판정 전체", "D6"),
    ("센서 전원과 시동의 관계", "TBR", "시험 설계 12절", "미정", "TC-08", "D8"),
    ("시드 규칙", "base 20261111, crc32(조건명) 기반, 시행 번호", "시험 설계 8.4(시드 저장 요구)", "구현 선택(예비시험 규칙에서 시행 수 제한을 없앰)", "무작위 TC 전체", ""),
]

PRE_OBJECTS = {  # 사전점검용 임시 입력: 기준선 아님. 코드 경로 점검을 위한 가정 반사면
    "O-A": {"label": "R1(가정, O-A 대체 점검용)", "h_cm": 20.0}, "O-B": {"label": "R2(가정, O-B 대체 점검용)", "h_cm": 40.0},
    "O-C": {"label": "R3(가정, O-C 대체 점검용)", "h_cm": 60.0}}
PRE_TC_OBJECTS = {k: "O-A" for k in ("TC-05", "TC-06", "TC-08a", "TC-09", "TC-10", "TC-13a", "TC-14", "TC-15", "cargo_top_equals")}
PRE_LEVELS_EXTRA = {"TC05_combination": "단일 요인(점검용)", "TC05a_vs_05b": "동일 격자(점검용)",
                    "TC07c_targets": [("empty", "empty", 0.0), ("R0", "cargo", 5.0), ("R1", "occupant", 20.0)]}
VARIANTS = [("Tdb0", 0.0, "rx"), ("Tdb0.5-rx", 0.5, "rx"), ("Tdb0.5-req", 0.5, "req")]


def env_info():
    return {"python": platform.python_version(), "numpy": np.__version__, "rng": "numpy.random.PCG64 via SeedSequence(seed).spawn",
            "seed_rule": "seed = base_seed * 2**64 + crc32('<접두>/<TC>/<조건>') * 2**20 + 시행 번호"}


def cfg_from(b, db_override=None):
    g, s, d, ev = b["geometry"], b["sensor"], b["detector"], b["evaluation"]
    det_kw = {k: d[k] for k in ("delta_on_cm", "delta_off_cm", "k", "M", "T_stale_s", "valid_min_cm", "valid_max_cm", "c_fixed_mps")}
    det_kw.update(d_empty_cm=d["d_empty_cm"], T_db_s=d["T_db_s"], db_basis=d["db_basis"])
    if db_override:
        det_kw.update(db_override)
    return PrelimConfig(
        geometry=Geometry(H_s_cm=g["H_s_cm"], R0_cm=g["R0_cm"], R1_cm=g["R1_cm"], R2_cm=g["R2_cm"], R3_cm=g["R3_cm"]),
        sensor=SensorModel(T_air_C=20.0, sigma_cm=s["sigma_cm"], p_loss=s["p_loss"], bias_cm=s["bias_cm"], period_s=s["period_s"], T_to_s=s["T_to_s"]),
        detector=Detector(**det_kw),
        evaluation=Evaluation(t_eval_s=ev["t_eval_s"], T_first_s=ev["T_first_s"], T_recover_s=ev["T_recover_s"], hold_s=ev["hold_s"],
                              response_limit_s=ev["response_limit_s"], temp_input_err_C=b["environment"]["temp_input_err_C"], base_seed=b["seed"]["base_seed"]))


def open_items(b):
    """baseline에서 값이 비어 있는 필수 항목."""
    need = [("detector", "d_empty_cm"), ("detector", "T_db_s"), ("detector", "db_basis"), ("environment", "T_base_C"),
            ("environment", "temp_comp_base"), ("repetitions", "TC-01"), ("repetitions", "TC-04")]
    miss = [f"{a}.{k}" for a, k in need if b[a][k] is None]
    if not b.get("confirmed"):
        miss.insert(0, "confirmed=false")
    return miss


def write_common(out, stage, cfg_dict, R=None, summary=None):
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "config.json"), "w", encoding="utf-8") as f:
        json.dump({"stage": stage, "config": cfg_dict, "environment": env_info()}, f, ensure_ascii=False, indent=2, default=str)
    if R is not None:
        write_csv(os.path.join(out, "trials.csv"), R.trials)
        write_csv(os.path.join(out, "output_log.csv"), R.outlog)
        write_csv(os.path.join(out, "events.csv"), R.events)
        R.close()
    write_csv(os.path.join(out, "summary.csv"), summary if summary is not None else R.summary, list(E.SUMMARY_FIELDS))


def write_trace(out, summary):
    rows = []
    tc_of = {"SR-01": ["TC-02", "TC-03", "TC-05", "TC-06"], "SR-02": ["TC-02", "TC-03", "TC-05", "TC-11"],
             "SR-03": ["TC-01", "TC-11"], "SR-04": ["TC-04", "TC-11"], "SR-05": ["TC-07"], "SR-06": ["TC-16"],
             "SR-07(a)": ["TC-08"], "SR-07(b)": ["TC-09"], "SR-08": ["TC-06", "TC-10"], "SR-09": ["TC-11"],
             "SR-10": ["TC-13", "TC-05"], "SR-11": ["TC-14"], "SR-12": ["TC-15"], "SR-13": ["TC-08", "TC-13", "TC-14", "TC-15"],
             "SR-14": ["TC-01", "TC-02", "TC-03", "TC-04", "TC-05", "TC-11"]}
    for sr, meth, pre, tcs in DEC.TRACE:
        for tc in tc_of[sr]:
            rs = [r for r in summary if r["tc"] == tc and (sr.startswith("SR-07") is False or True)]
            cnt = {}
            for r in rs:
                cnt[r["status"]] = cnt.get(r["status"], 0) + 1
            rows.append({"SR": sr, "검증": meth, "예비시험": pre, "TC": tc, "결과 행 수": len(rs),
                         "상태 집계": "; ".join(f"{k} {v}" for k, v in sorted(cnt.items())) if cnt else "결과 없음"})
    write_csv(os.path.join(out, "trace_SR_TC_result.csv"), rows)


def make_runner(stage, out, cfg, objects, reps, targets, tc_objects, env, prefix="", small=10):
    return Runner(stage, out, cfg, objects, reps, targets, tc_objects, env, small=small, small_long=3, prefix=prefix)


# =====================================================================
def do_status(out):
    b = json.load(open(DRAFT, encoding="utf-8"))
    miss = open_items(b)
    os.makedirs(out, exist_ok=True)
    write_csv(os.path.join(out, "baseline_check.csv"),
              [dict(zip(["항목", "값", "근거 문서·절", "상태", "적용 TC", "결정 항목"], r)) for r in BASELINE_TABLE])
    write_csv(os.path.join(out, "decisions.csv"),
              [{"결정": k, "항목": v[0], "문서 상태·충돌": v[1], "영향 TC": v[2], "권장": v[3]} for k, v in DEC.DECISIONS.items()])
    rows = []
    for tc, desc, sr, ds in DEC.TC_ROWS:
        reason = ("기준선 v1.0 미확정(결정 " + ", ".join(ds) + "). ") if ds else "기준선 v1.0 미확정(측정 주기 100 ms는 구현 설정(예비)). "
        reason += "본시험 실행·합격 판정은 기준선 확정 뒤에 수행함. 확정 전 점검은 results_precheck 참조"
        rows.append({"stage": "main", "tc": tc[:5], "cond_id": tc, "condition": desc, "sr": sr, "kind": "notrun", "status": E.S_NOTRUN, "note": reason})
    write_common(out, "main-status", b, summary=rows)
    write_trace(out, rows)
    return miss, rows


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def prelim_motion():
    """예비시험 코드(sil_prelim/run_prelim.py)의 P-02 b-2 움직임 값을 읽음."""
    src = open(os.path.join(os.path.dirname(HERE), "sil_prelim", "run_prelim.py"), encoding="utf-8").read()
    m = re.search(r"amp,\s*hz\s*=\s*([0-9.]+),\s*([0-9.]+)", src)
    return (float(m.group(1)), float(m.group(2))) if m else (None, None)


def verify_baseline(b, cfg, R, lv, mot, out):
    """실행 전 확인: 기준선 파일의 값과 실제 코드(설정 객체·실행기·시험 함수 입력)에 들어간 값이 같은지 비교해 baseline_verification.csv에 기록.
    하나라도 다르면 실행하지 않음."""
    rows = []

    def row(item, base_v, code_v, where, tol=1e-12):
        if isinstance(base_v, (int, float)) and isinstance(code_v, (int, float)) and not isinstance(base_v, bool):
            ok = abs(base_v - code_v) <= tol
        else:
            ok = base_v == code_v
        rows.append({"항목": item, "기준선 v1.0": base_v, "코드 값": code_v, "코드 위치": where, "일치": "일치" if ok else "불일치"})

    g, d, s_, e = b["geometry"], b["detector"], b["sensor"], b["evaluation"]
    for k in ("H_s_cm", "R0_cm", "R1_cm", "R2_cm", "R3_cm"):
        row(f"geometry.{k}", g[k], getattr(cfg.geometry, k), "cfg.geometry")
    row("빈 좌석 높이", g["empty_seat_h_cm"], 0.0, "시나리오 static(kind='empty', h=0.0)")
    for k in ("O-A", "O-B", "O-C", "R1"):
        row(f"objects.{k}.h_cm", b["objects"][k]["h_cm"], R.objects[k]["h_cm"], "Runner.objects")
    row("O-A = R1(TC-02a)", cfg.geometry.R1_cm, R.objects["O-A"]["h_cm"], "TC-02a 입력")
    row("O-B = R2(TC-02b, TC-11)", cfg.geometry.R2_cm, R.objects["O-B"]["h_cm"], "TC-02b·TC-11 입력")
    row("O-C = R3(TC-03)", cfg.geometry.R3_cm, R.objects["O-C"]["h_cm"], "TC-03 입력")
    row("원 조건 O-S", b["objects"]["O-S"], R.objects.get("O-S"), "TC-12 미실행")
    for k, attr in (("TC-05", "tc05_object"), ("TC-06", "tc06_object"), ("TC-08a", "tc08_object"), ("TC-09", "tc09_object"),
                    ("TC-10", "tc10_object"), ("TC-13a", "tc13_object"), ("TC-14", "tc14_object"), ("TC-15", "tc15_object"),
                    ("cargo_top_equals", "cargo_top_equals")):
        nm = getattr(R, attr)
        row(f"tc_objects.{k}", b["tc_objects"][k], nm, f"Runner.{attr}")
        row(f"  {k}의 반사면 높이", cfg.geometry.R1_cm, R.objects[nm]["h_cm"], f"Runner.objects[{nm}]")
    for k in ("d_empty_cm", "T_db_s", "db_basis", "delta_on_cm", "delta_off_cm", "k", "M", "T_stale_s", "valid_min_cm", "valid_max_cm", "c_fixed_mps"):
        row(f"detector.{k}", d[k], getattr(cfg.detector, k), "cfg.detector")
    row("초기 구간 기준 delta_mid_cm", (d["delta_on_cm"] + d["delta_off_cm"]) / 2, cfg.detector.delta_mid_cm, "cfg.detector.delta_mid_cm(계산값)")
    for k in ("sigma_cm", "p_loss", "bias_cm", "period_s", "T_to_s"):
        row(f"sensor.{k}", s_[k], getattr(cfg.sensor, k), "cfg.sensor")
    for k in ("t_eval_s", "T_first_s", "T_recover_s", "hold_s", "response_limit_s"):
        row(f"evaluation.{k}", e[k], getattr(cfg.evaluation, k), "cfg.evaluation")
    row("environment.temp_input_err_C", b["environment"]["temp_input_err_C"], cfg.evaluation.temp_input_err_C, "cfg.evaluation")
    row("environment.T_base_C", b["environment"]["T_base_C"], R.T_base, "Runner.T_base")
    row("environment.temp_comp_base", b["environment"]["temp_comp_base"], R.comp_base, "Runner.comp_base")
    row("seed.base_seed", b["seed"]["base_seed"], cfg.evaluation.base_seed, "cfg.evaluation.base_seed")
    for k in ("TC-01", "TC-02", "TC-03", "TC-04", "TC-05_base", "TC-05_level", "TC-06_level", "TC-07c_level", "TC-08", "TC-09", "TC-10", "TC-13_noisy"):
        row(f"repetitions.{k}", b["repetitions"][k], R.reps[k], "Runner.reps")
    for k in ("miss_rate", "false_alarm_rate", "unknown_rate", "response_s", "flips"):
        row(f"targets.{k}", b["targets"][k], R.targets[k], "Runner.targets")
    pa, ph = prelim_motion()
    row("TC-04b-2 진폭(cm) = 예비시험 P-02", b["motion_assumption"]["amp_cm"], pa, "sil_prelim/run_prelim.py")
    row("TC-04b-2 주파수(Hz) = 예비시험 P-02", b["motion_assumption"]["hz"], ph, "sil_prelim/run_prelim.py")
    row("TC-04b-2 진폭·주파수가 시험 함수에 전달됨", (b["motion_assumption"]["amp_cm"], b["motion_assumption"]["hz"]), (mot["amp_cm"], mot["hz"]), "E.tc04(R, mot)")
    for k in ("sigma_cm", "p_loss", "bias_cm", "tilt_deg", "tilt_p_loss"):
        row(f"sensitivity_levels.{k}", b["sensitivity_levels"][k], lv[k], "E.tc05/06 입력")
    row("TC-07c 대상", b["sensitivity_levels"]["TC07c_targets"], lv["TC07c_targets"], "E.tc07c 입력")
    row("TC-07c 임계값 조합", b["sensitivity_levels"]["TC07c_threshold_pairs"], lv["TC07c_threshold_pairs"], "E.tc07c 입력")
    # 동작 확인: 잡음 없는 R1 착석의 최초 판정 시각(요청 기준 T_db 0.5 s이면 0.9 s대)
    from sil.scenario import static
    from sil.simulate import run_trial
    tr = run_trial(static("verify-R1", "occupant", cfg.geometry.R1_cm, duration=3.0), cfg, 1, cfg.detector, 0.0, 0.0, None)
    f = next((t for t, v in tr["out_log"] if v != "UNKNOWN"), None)
    ok = f is not None and 0.900 <= f <= 0.915
    rows.append({"항목": "동작 확인: 잡음 없는 R1 최초 유효 판정 시각", "기준선 v1.0": "0.900–0.915 s(요청 기준 T_db 0.5 s)", "코드 값": f,
                 "코드 위치": "run_trial(db_basis=req)", "일치": "일치" if ok else "불일치"})
    rows.append({"항목": "T_db 시간 기준 동작", "기준선 v1.0": "req", "코드 값": cfg.detector.db_basis, "코드 위치": "Detector.decide: tb = t_req", "일치": "일치" if cfg.detector.db_basis == "req" else "불일치"})
    write_csv(os.path.join(out, "baseline_verification.csv"), rows)
    bad = [r for r in rows if r["일치"] != "일치"]
    return rows, bad


def tc11_tables(out, summary):
    """TC-11 구성(온도·보정)·대상별 결과를 나란히 정리. 합산 없음."""
    pat = re.compile(r"^(11[ab])-T(\d+)-(nocomp|comp)/(TC-\d+[ab]?)$")
    tgt = {"TC-01": "빈 좌석", "TC-02b": "R2(TC-02b 대응)", "TC-04a": "R0(TC-04a 대응)"}
    cells = {}
    for r in summary:
        if r["tc"] != "TC-11" or r["kind"] != "rate":
            continue
        m = pat.match(r["cond_id"])
        if not m:
            continue
        _, T, comp, t = m.groups()
        cells.setdefault((tgt[t], r["metric"], int(T)), {})[comp] = r
    rows = []
    for (t, metric, T), d in sorted(cells.items(), key=lambda x: (x[0][0], x[0][1], x[0][2])):
        row = {"대상": t, "지표": metric, "온도(°C)": T}
        for comp, lab in (("nocomp", "보정 없음"), ("comp", "보정 있음")):
            r = d.get(comp)
            row[f"{lab} k/n"] = f"{r['k']}/{r['n']}" if r else ""
            row[f"{lab} 관측"] = r["observed"] if r else ""
            row[f"{lab} 상한95"] = r["upper95"] if r else ""
            row[f"{lab} 판정"] = r["status"] if r else ""
        rows.append(row)
    write_csv(os.path.join(out, "tc11_side_by_side.csv"), rows)
    cov = []
    for tg in ("빈 좌석", "R2(TC-02b 대응)", "R0(TC-04a 대응)"):
        for T in (0, 20, 50):
            for comp in ("nocomp", "comp"):
                cov.append({"대상": tg, "온도(°C)": T, "보정": "유" if comp == "comp" else "무", "실행": "실행(각 300회)"})
    write_csv(os.path.join(out, "coverage_TC11.csv"), cov)
    return rows


def write_report(out, b, sha, summary, ver_rows):
    """결과 요약 report.md(시험별 상태표). 보고서 본문이 아니라 결과표의 읽기용 사본임."""
    from collections import Counter, OrderedDict
    by = OrderedDict()
    for r in summary:
        by.setdefault(r["tc"], []).append(r)
    L = ["# 본시험 결과 요약 (기준선 v1.0)", "", f"- 기준선 파일: baseline/baseline_v1.0.json (sha256 {sha})",
         f"- 기준선·코드 값 확인: {len(ver_rows)}개 항목 모두 일치(baseline_verification.csv)", "- 판정 규칙: 단측 95% 정확 이항 상한(시험 설계 9.4절). 목표 충족(통계 확인) / 관측 충족(통계 미확인) / 불합격",
         "- 사전점검(results_precheck)과 P-08-R0(results_p08r0)은 이 집계에 포함하지 않음", ""]
    cnt = Counter(r["status"] for r in summary)
    L += ["## 상태 집계", "", "| 상태 | 행 수 |", "|---|---|"] + [f"| {k} | {v} |" for k, v in sorted(cnt.items())] + [""]
    for tc, rs in by.items():
        L += [f"## {tc}", "", "| 조건 | 지표 | n | k | 관측 | 상한95 | 목표 | 상태 |", "|---|---|---|---|---|---|---|---|"]
        for r in rs:
            def f(x):
                return "" if x in (None, "") else x
            L.append(f"| {r['cond_id']} | {f(r['metric'])} | {f(r['n'])} | {f(r['k'])} | {f(r['observed'])} | {f(r['upper95'])} | {f(r['target'])} | {r['status']} |")
        L.append("")
    open(os.path.join(out, "report.md"), "w", encoding="utf-8").write("\n".join(L))


def do_main(out, path):
    path = path or V1
    if not os.path.exists(path):
        print(f"[본시험 미실행] {path} 없음 → 기준선 미확정. results_main에 TC별 '미실행'과 사유를 기록함")
        do_status(out)
        return 2
    b = json.load(open(path, encoding="utf-8"))
    miss = open_items(b)
    if miss:
        print("[본시험 미실행] 기준선에 비어 있거나 확정되지 않은 항목:", ", ".join(miss))
        do_status(out)
        return 2
    sha = sha256_of(path)
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    shutil.copy(path, os.path.join(out, os.path.basename(path)))
    cfg = cfg_from(b)
    objects = {k: v for k, v in b["objects"].items() if isinstance(v, dict) and "h_cm" in v}
    targets = b["targets"]
    env = b["environment"]
    R = make_runner("main", out, cfg, objects, b["repetitions"], targets, b["tc_objects"], env, prefix="")
    lv = b["sensitivity_levels"]
    mot = b["motion_assumption"]
    ver, bad = verify_baseline(b, cfg, R, lv, mot, out)
    if bad:
        print("[본시험 중단] 기준선과 코드 값이 다름:")
        for r in bad:
            print("  ", r["항목"], "기준선", r["기준선 v1.0"], "코드", r["코드 값"])
        R.close()
        return 3
    print(f"기준선·코드 값 확인: {len(ver)}개 항목 모두 일치 (sha256 {sha[:12]}…)")
    # 결정적 시험 → 상태 전이·고장 → 무작위 시험 (TC-16b는 로그가 쌓인 뒤)
    E.tc07(R); E.tc13(R); E.tc14(R); E.tc15(R); E.tc08(R)
    E.tc01(R); E.tc02(R); E.tc03(R); E.tc04(R, mot); E.tc05(R, lv); E.tc06(R, lv); E.tc07c(R, lv, None)
    E.tc09(R); E.tc10(R); E.tc11(R); E.tc12(R); E.tc16(R)
    write_common(out, "main", {**b, "_baseline_file": os.path.basename(path), "_baseline_sha256": sha,
                               "_command": "python3 run_main.py main"}, R)
    write_trace(out, R.summary)
    tc11_tables(out, R.summary)
    write_report(out, b, sha, R.summary, ver)
    print(f"본시험 완료: 결과 행 {len(R.summary)}개 → {out}")
    return 0


def do_precheck(out):
    b = json.load(open(DRAFT, encoding="utf-8"))
    # 사전점검용 임시 입력(기준선 아님): 예비시험 값을 그대로 씀
    b = json.loads(json.dumps(b))
    b["detector"].update(d_empty_cm=100.0, T_db_s=0.0, db_basis="rx")
    b["environment"].update(T_base_C=20.0, temp_comp_base=False)
    b["repetitions"].update({"TC-01": 60, "TC-04": 60})
    cfg = cfg_from(b)
    targets = b["targets"]
    lv = dict(b["sensitivity_levels"]); lv.update(PRE_LEVELS_EXTRA)
    mot = {"amp_cm": 1.0, "hz": 0.25}
    R = make_runner("precheck", out, cfg, PRE_OBJECTS, b["repetitions"], targets, PRE_TC_OBJECTS, b["environment"], prefix="PRE/")
    # 1) 결정적: 임계값 경계, 고장 주입·복구 (T_db 후보별 비교)
    for name, tdb, basis in VARIANTS:
        d = R.dc(T_db_s=tdb, db_basis=basis)
        tag = f"|{name}"
        E.tc07(R, tag, d); E.tc13(R, tag, d); E.tc14(R, tag, d); E.tc15(R, tag, d, n_extra=20)
    # 2) 대표 정상 조건, 초기화, 응답, 유지 (T_db 후보별)
    for name, tdb, basis in VARIANTS:
        d = R.dc(T_db_s=tdb, db_basis=basis)
        tag = f"|{name}"
        E.tc08(R, tag, d); E.tc09(R, tag, d); E.tc10(R, d, tag)
    # 3) 나머지 코드 경로(기준 T_db = 0, 예비시험 설정)
    E.tc01(R); E.tc02(R); E.tc03(R); E.tc04(R, mot); E.tc05(R, lv); E.tc06(R, lv); E.tc07c(R, lv, None)
    E.tc11(R); E.tc12(R); E.tc16(R)
    write_common(out, "precheck", {**b, "_precheck_note": "사전점검용 임시 입력. 기준선 아님. 대상은 가정 반사면 R1~R3 대체",
                                   "_precheck_objects": PRE_OBJECTS, "_variants": VARIANTS, "_precheck_n": R.small, "_precheck_n_long": R.small_long}, R)
    write_trace(out, R.summary)
    tdb = []
    for r in R.summary:
        if "|Tdb" in (r["cond_id"] or "") and r["kind"] in ("all_trials", "deterministic") and r["status"] != E.S_SENS:
            base, var = r["cond_id"].split("|")
            tdb.append({"T_db 후보": var, "TC": r["tc"], "조건": base, "상태(점검, 판정 아님)": r["status"], "기대": r["expected"], "실제": r["actual"]})
    write_csv(os.path.join(out, "tdb_comparison.csv"), sorted(tdb, key=lambda x: (x["TC"], x["조건"], x["T_db 후보"])))
    print(f"사전점검 완료: 결과 행 {len(R.summary)}개 → {out}")
    return 0


def do_additional(out):
    b = json.load(open(DRAFT, encoding="utf-8"))
    b = json.loads(json.dumps(b))
    b["detector"].update(d_empty_cm=100.0, T_db_s=0.0, db_basis="rx")     # 예비시험 설정과 동일
    b["environment"].update(T_base_C=20.0, temp_comp_base=False)
    cfg = cfg_from(b)
    R = make_runner("additional", out, cfg, {}, b["repetitions"], b["targets"], {}, b["environment"], prefix="")
    rows = E.p08_r0(R, n=10)
    write_common(out, "additional(P-08-R0)", {**b, "_note": "예비시험 이후 추가한 시험. 예비시험 설정(T_db=0, d_empty=100, 20 °C 기준) 사용. 합격 판정 없음"}, R)
    write_csv(os.path.join(out, "p08_r0_results.csv"), rows)
    print(f"추가 시험 P-08-R0 완료 → {out}")
    for r in rows:
        print(r["T_C"], "보정" if r["temp_comp"] else "무보정", "Δ계산", r["delta_calc_noiseless_cm"], "잡음없음 시행 Δ", r["delta_sim_noiseless_cm"],
              r["noiseless_output_at_t_eval"], "무작위", r["random_OCC"], r["random_UNOCC"], r["random_UNKNOWN"])
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    arg = sys.argv[2] if len(sys.argv) > 2 else None
    if mode == "status":
        miss, rows = do_status(arg or os.path.join(HERE, "results_status_before_baseline"))
        print("미확정 항목:", ", ".join(miss)); print(f"TC 행 {len(rows)}개를 '미실행'으로 기록")
    elif mode == "precheck":
        do_precheck(arg or os.path.join(HERE, "results_precheck"))
    elif mode == "additional":
        do_additional(arg or os.path.join(HERE, "results_p08r0"))
    elif mode == "main":
        sys.exit(do_main(os.path.join(HERE, "results_main"), arg))
    elif mode == "all":
        do_status(os.path.join(HERE, "results_status_before_baseline")); do_precheck(os.path.join(HERE, "results_precheck")); do_additional(os.path.join(HERE, "results_p08r0"))
    else:
        print(__doc__)
