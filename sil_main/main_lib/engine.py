"""본시험 시험 케이스(TC-01~TC-16) 구현과 추가 시험(P-08-R0).

시험 설계 11.2절의 입력·정답·기록 신호·합격 기준을 코드로 옮긴 것임. 코드는 예비시험의 센서 모델·판단 프로그램·
시나리오·평가 함수(sil/)를 그대로 쓰고, 입력 생성(scenario)·센서 모델(sensor_model)·판단(detector)·
정답(Scenario.truth)·평가(evaluate, stats)를 서로 다른 모듈에 둠.

stage:
  precheck   본시험 전 소규모 점검. 판정이 아님.
  main       확정된 기준선(baseline_v1.0.json)으로 실행하는 본시험.
  additional 예비시험 이후 추가한 시험(P-08-R0). 판정 없음.
"""
import csv, gzip, json, os, platform, zlib
from dataclasses import replace

import numpy as np

from sil.config import speed_of_sound
from sil.scenario import Scenario, Segment, Faults, static, OCC, UNOCC, UNK
from sil.simulate import run_trial
from sil.detector import OccupancyDetector, UNKNOWN
from sil import evaluate as ev
from . import stats

S_MATCH, S_MISMATCH = "일치", "불일치"
S_ALL_OK = "기준 충족(전 시행)"
S_REC = "기록(합격 판정 없음)"
S_SENS = "가정 기반 민감도 기록"
S_NOTRUN = "미실행"

SAMPLE_FIELDS = ["stage", "tc", "cond", "trial", "seed", "idx", "t_req", "t_rx", "status", "cause", "d_true_cm", "noise_cm",
                 "pulse_us", "d_conv_cm", "d_med_cm", "delta_cm", "output", "truth"]
SUMMARY_FIELDS = ["stage", "tc", "cond_id", "condition", "sr", "kind", "metric", "n", "k", "observed", "upper95", "target",
                  "status", "expected", "actual", "surface", "note"]


def seed_for(base, prefix, tc, cond, i):
    """seed = base_seed * 2**64 + crc32('<접두>/<TC>/<조건>') * 2**20 + 시행 번호 (조건마다 독립, 시행 수 제한 2**20)."""
    return base * 2 ** 64 + zlib.crc32(f"{prefix}{tc}/{cond}".encode()) * 2 ** 20 + i


class Runner:
    def __init__(self, stage, outdir, cfg, objects, reps, targets, tc_objects, env, small=10, small_long=3, prefix=""):
        self.stage, self.out, self.cfg = stage, outdir, cfg
        self.objects, self.reps, self.small, self.small_long, self.prefix = objects, reps, small, small_long, prefix
        self.targets = targets
        self.T_base, self.comp_base = env["T_base_C"], env["temp_comp_base"]
        self.cargo_top_equals = tc_objects.get("cargo_top_equals")
        self.tc05_object, self.tc06_object = tc_objects.get("TC-05"), tc_objects.get("TC-06")
        self.tc08_object, self.tc09_object = tc_objects.get("TC-08a"), tc_objects.get("TC-09")
        self.tc10_object, self.tc13_object = tc_objects.get("TC-10"), tc_objects.get("TC-13a")
        self.tc14_object, self.tc15_object = tc_objects.get("TC-14"), tc_objects.get("TC-15")
        self.base = cfg.evaluation.base_seed
        os.makedirs(outdir, exist_ok=True)
        self._f_samples = gzip.open(os.path.join(outdir, "trial_samples.csv.gz"), "wt", newline="", encoding="utf-8")
        self._w_samples = csv.DictWriter(self._f_samples, fieldnames=SAMPLE_FIELDS)
        self._w_samples.writeheader()
        self.trials, self.outlog, self.events, self.summary = [], [], [], []
        self.req_intervals = {}       # TC-16b용 측정 요청 간격
        self.vl = " [가상 반사면 대체 조건]" if stage == "main" else ""     # D1: 원 조건(O-A/B/C)을 대신한 가정 반사면 표시

    # ---------- 설정·반복 수 ----------
    def n(self, planned, long_run=False):
        if self.stage == "main":
            return planned
        return min(planned, self.small_long if long_run else self.small)

    def label(self, base):
        return "점검 · " + base if self.stage == "precheck" else base

    # ---------- 실행·기록 ----------
    def run(self, tc, cond, scn, i, det_cfg=None, sigma=None, p_loss=None, bias=None, log_samples=True, seed=None):
        sd = seed if seed is not None else seed_for(self.base, self.prefix, tc, cond, i)
        tr = run_trial(scn, self.cfg, sd, det_cfg, sigma, p_loss, bias)
        tr["tc"], tr["cond"], tr["trial"] = tc, cond, i
        if log_samples:
            for r in tr["rows"]:
                self._w_samples.writerow({"stage": self.stage, "tc": tc, "cond": cond, "trial": i, "seed": sd,
                                          **{k: r.get(k) for k in SAMPLE_FIELDS[5:]}})
        for t, v in tr["out_log"]:
            self.outlog.append({"stage": self.stage, "tc": tc, "cond": cond, "trial": i, "seed": sd, "t": t, "output": v})
        for t, k, d in tr["events"]:
            self.events.append({"stage": self.stage, "tc": tc, "cond": cond, "trial": i, "seed": sd, "t": t, "event": k, "detail": d})
        return tr

    def trial_row(self, tc, cond, i, tr, **kw):
        self.trials.append({"stage": self.stage, "tc": tc, "cond": cond, "trial": i, "seed": tr["seed"] if tr else None, **kw})

    def add(self, **kw):
        row = {k: None for k in SUMMARY_FIELDS}
        row.update(stage=self.stage, **kw)
        self.summary.append(row)

    def rate_rows(self, tc, cond, desc, truth, kind, outs, surface, sens=False, note="", sr=None):
        """정적 판정 조건의 오류율·미확정률·정답률 행. 분모는 전체 시행 수, UNKNOWN을 빼지 않음(9.2절)."""
        c = ev.rates(outs, truth)
        n = c["n"]
        T = self.targets
        metrics = []
        if truth == OCC:
            metrics.append(("미검출률", "SR-02", c["error"], T["miss_rate"]))
        else:
            metrics.append(("오검출률", "SR-03" if kind == "empty" else "SR-04", c["error"], T["false_alarm_rate"]))
        metrics.append(("미확정률", "SR-14", c["unknown"], T["unknown_rate"]))
        for name, sr_, k, tg in metrics:
            obs, ub, st = stats.judge_rate(k, n, tg)
            status = S_SENS if sens else self.label(st)
            self.add(tc=tc, cond_id=cond, condition=desc, sr=sr_ if sr is None else sr, kind="rate", metric=name, n=n, k=k,
                     observed=round(obs, 6), upper95=round(ub, 6), target=tg, status=status,
                     expected=f"정답 {truth}", actual=f"정답 {c['correct']}, 오류 {c['error']}, UNKNOWN {c['unknown']}",
                     surface=surface, note=note + ("" if not sens else " (민감도 수준: 합격 판정 없음)"))
        self.add(tc=tc, cond_id=cond, condition=desc, sr="SR-02/03/04", kind="record", metric="기한 내 정답률", n=n, k=c["correct"],
                 observed=round(c["correct"] / n, 6), status=S_REC, expected=f"정답 {truth}", surface=surface)

    def all_trials_rows(self, tc, cond, desc, sr, fails, n, expected, surface="-", sens=False, note="", detail=""):
        """'모든 시행에서 기준을 만족'해야 하는 조건. 실패 시행 수와 단측 95% 상한을 함께 기록."""
        ub = stats.upper_bound(fails, n)
        status = S_SENS if sens else self.label(S_ALL_OK if fails == 0 else stats.S_FAIL)
        self.add(tc=tc, cond_id=cond, condition=desc, sr=sr, kind="all_trials", metric="기준 미충족 시행 수", n=n, k=fails,
                 observed=round(fails / n, 6), upper95=round(ub, 6), target=0, status=status, expected=expected,
                 actual=f"미충족 {fails}/{n}" + (f"; {detail}" if detail else ""), surface=surface, note=note)

    def check(self, tc, cond, desc, sr, expected, actual, ok, note="", surface="-"):
        st = (S_MATCH if ok else S_MISMATCH)
        self.add(tc=tc, cond_id=cond, condition=desc, sr=sr, kind="deterministic", metric="기대=실제", status=self.label(st),
                 expected=expected, actual=actual, surface=surface, note=note, n=1, k=0 if ok else 1)

    def record(self, tc, cond, desc, sr, expected, actual, note="", surface="-", n=None):
        self.add(tc=tc, cond_id=cond, condition=desc, sr=sr, kind="record", metric="기록", status=S_REC,
                 expected=expected, actual=actual, surface=surface, note=note, n=n)

    def notrun(self, tc, cond, desc, sr, reason):
        self.add(tc=tc, cond_id=cond, condition=desc, sr=sr, kind="notrun", status=S_NOTRUN, note=reason)

    # ---------- 공통 ----------
    def dc(self, **kw):
        return replace(self.cfg.detector, **kw)

    def static_outs(self, tc, cond, kind, h, n, T=None, comp=None, sigma=None, p=None, bias=None, duration=5.0, motion=(0.0, 0.0),
                    det=None, pair_seed_cond=None, log_samples=True):
        T = self.T_base if T is None else T
        comp = self.comp_base if comp is None else comp
        det = det or self.dc(temp_comp=comp)
        scn = static(f"{tc}-{cond}", kind, h, duration=duration, T_air=T, motion=motion)
        outs, trs = [], []
        for i in range(1, n + 1):
            sd = seed_for(self.base, self.prefix, tc, pair_seed_cond or cond, i)
            tr = self.run(tc, cond, scn, i, det, sigma, p, bias, log_samples=log_samples, seed=sd)
            o = ev.output_at(tr["out_log"], self.cfg.evaluation.t_eval_s)
            outs.append(o); trs.append(tr)
            truth = scn.truth(self.cfg.evaluation.t_eval_s)
            self.trial_row(tc, cond, i, tr, truth=truth, out_eval=o, result="정답" if o == truth else ("UNKNOWN" if o == UNK else "오류"),
                           first_valid_s=ev.first_valid_time(tr["out_log"]), T_air=T, comp=comp,
                           sigma=sigma if sigma is not None else self.cfg.sensor.sigma_cm,
                           p_loss=p if p is not None else self.cfg.sensor.p_loss, bias=bias if bias is not None else self.cfg.sensor.bias_cm)
        if tc in ("TC-01", "TC-02") and trs:
            self.req_intervals.setdefault(tc, []).append(ev.min_request_interval(trs[0]["req_times"]))
        return outs, trs, scn.truth(self.cfg.evaluation.t_eval_s)

    def obj(self, name):
        return self.objects.get(name)

    def close(self):
        self._f_samples.close()


def write_csv(path, rows, fields=None):
    if not rows:
        return
    keys = fields or []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def req_of(tr, t_rx):
    """수신 시각이 t_rx인 샘플의 (측정 요청 시각, 수신 시각). 판정 시각은 수신·처리 시각이므로 둘을 함께 기록함(D2)."""
    if t_rx is None:
        return None, None
    row = next((r for r in tr["rows"] if r["t_rx"] is not None and abs(r["t_rx"] - t_rx) < 1e-6), None)
    return (None, None) if row is None else (row["t_req"], row["t_rx"])


def surface_label(o):
    if o is None:
        return "-"
    return o["label"]


# =====================================================================
#  TC-01 ~ TC-05 (정적 판정)
# =====================================================================
def tc01(R, T=None, comp=None, tag=""):
    n = R.n(R.reps["TC-01"])
    outs, _, truth = R.static_outs("TC-01", f"empty{tag}", "empty", 0.0, n, T, comp)
    R.rate_rows("TC-01", f"empty{tag}", f"빈 좌석 오검출(T={R.T_base if T is None else T}°C)", truth, "empty", outs, "빈 좌석")


def _need(R, tc, cond, desc, sr, *names):
    miss = [x for x in names if R.obj(x) is None]
    if miss:
        R.notrun(tc, cond, desc, sr, f"본시험 입력 미확정: {', '.join(miss)}의 반사면 정의(높이 근거) 없음(시험 설계 4.3·12절)")
        return False
    return True


ORIG_NOTRUN = {"O-A": "TC-02a", "O-B": "TC-02b", "O-C": "TC-03"}


def orig_notrun(R):
    """D1: O-A·O-B·O-C 원 조건은 반사면 근거가 없어 미실행. 가상 반사면 대체 조건과 구분해 기록함."""
    if R.stage != "main":
        return
    for name, tc in ORIG_NOTRUN.items():
        R.notrun(tc[:5], f"{tc}/원 조건 {name}", f"{name} 원 조건(실제 대상 반사면)", "SR-01/02/14",
                 f"원 조건 미실행(D1): {name}의 반사면 높이 근거 없음(시험 설계 4.3·12절 TBR). 가상 반사면 대체 조건으로 실행한 결과는 {tc} 행 참조. 이 결과를 {name}의 결과로 보지 않음")


def tc02(R):
    orig_notrun(R)
    for tc_cond, name in (("TC-02a", "O-A"), ("TC-02b", "O-B")):
        if not _need(R, tc_cond, tc_cond, f"최소 크기 대상 {name} 감지", "SR-01/02/14", name):
            continue
        o = R.obj(name)
        outs, _, truth = R.static_outs("TC-02", tc_cond, "occupant", o["h_cm"], R.n(R.reps["TC-02"]))
        R.rate_rows("TC-02", tc_cond, f"{o['label']} 착석 감지" if R.vl else f"{name} 착석 감지", truth, "occupant", outs, surface_label(o),
                    note=R.vl.strip() and ("가상 반사면 대체 조건: " + name + " 원 조건 아님"))


def tc03(R):
    if _need(R, "TC-03", "TC-03", "큰 체형 O-C 감지", "SR-01/02/14", "O-C"):
        o = R.obj("O-C")
        outs, _, truth = R.static_outs("TC-03", "TC-03", "occupant", o["h_cm"], R.n(R.reps["TC-03"]))
        R.rate_rows("TC-03", "TC-03", f"{o['label']} 착석 감지" if R.vl else "O-C 착석 감지", truth, "occupant", outs, surface_label(o),
                    note=R.vl.strip() and "가상 반사면 대체 조건: O-C 원 조건 아님")


def tc04(R, motion):
    n = R.n(R.reps["TC-04"])
    # 04a 낮은 화물 (C-1a = R0)
    outs, _, truth = R.static_outs("TC-04", "04a", "cargo", R.cfg.geometry.R0_cm, n)
    R.rate_rows("TC-04", "04a", "낮은 화물 C-1a(R0) 오검출", truth, "cargo", outs, "R0(가정)")
    # 04b-1, 04b-2 : 화물 윗면을 점유 대상과 같은 높이에 둠
    top = R.obj(R.cargo_top_equals) if R.cargo_top_equals else None
    if top is None:
        for c, d in (("04b-1", "점유 대상과 같은 정지 거리 이력의 화물"), ("04b-2", "점유 대상에만 움직임 가정")):
            R.notrun("TC-04", c, d, "SR-04", "본시험 입력 미확정: 화물 윗면 높이를 맞출 점유 대상(O-*) 반사면 정의 없음")
        return
    h = top["h_cm"]
    same_in = same_out = 0
    outs_c, outs_o = [], []
    scn_c = static("TC-04-b1-cargo", "cargo", h, duration=5.0, T_air=R.T_base)
    scn_o = static("TC-04-b1-occ", "occupant", h, duration=5.0, T_air=R.T_base)
    det = R.dc(temp_comp=R.comp_base)
    for i in range(1, n + 1):
        sd = seed_for(R.base, R.prefix, "TC-04", "04b-1", i)       # 같은 시드 = 같은 거리 이력
        a = R.run("TC-04", "04b-1/cargo", scn_c, i, det, seed=sd)
        b = R.run("TC-04", "04b-1/occupant-ref", scn_o, i, det, seed=sd)
        oa, ob = ev.output_at(a["out_log"], 3.0), ev.output_at(b["out_log"], 3.0)
        same_in += [r["d_conv_cm"] for r in a["rows"]] == [r["d_conv_cm"] for r in b["rows"]]
        same_out += a["out_log"] == b["out_log"]
        outs_c.append(oa); outs_o.append(ob)
        R.trial_row("TC-04", "04b-1/cargo", i, a, truth=UNOCC, out_eval=oa, result="정답" if oa == UNOCC else ("UNKNOWN" if oa == UNK else "오류"))
        R.trial_row("TC-04", "04b-1/occupant-ref", i, b, truth=OCC, out_eval=ob, result="정답" if ob == OCC else ("UNKNOWN" if ob == UNK else "오류"))
    R.rate_rows("TC-04", "04b-1", f"점유 대상과 같은 정지 거리 이력의 화물(윗면 {h:g} cm)", UNOCC, "cargo", outs_c, surface_label(top) + " 높이",
                note="기준을 바꾸지 않으며 불합격도 그대로 기록(시험 설계 11.2절)")
    R.record("TC-04", "04b-1", "같은 거리 이력 확인", "SR-04", "입력·출력이 점유 대상과 같음(구분 불가 예상)",
             f"입력 동일 {same_in}/{n}, 출력 동일 {same_out}/{n}", "알고리즘 특성(거리 입력만으로 구분 불가)", surface_label(top) + " 높이", n)
    if motion["amp_cm"] is None:
        R.notrun("TC-04", "04b-2", "점유 대상에만 움직임 가정", "SR-04", "본시험 입력 미확정: 움직임 가정의 진폭·주파수 없음")
        return
    scn_m = static("TC-04-b2-occ", "occupant", h, duration=5.0, T_air=R.T_base, motion=(motion["amp_cm"], motion["hz"]))
    outs_c, diff = [], 0
    for i in range(1, n + 1):
        sd = seed_for(R.base, R.prefix, "TC-04", "04b-2", i)
        a = R.run("TC-04", "04b-2/cargo", scn_c, i, det, seed=sd)
        b = R.run("TC-04", "04b-2/occupant-motion", scn_m, i, det, seed=sd)
        oa, ob = ev.output_at(a["out_log"], 3.0), ev.output_at(b["out_log"], 3.0)
        outs_c.append(oa); diff += oa != ob
        R.trial_row("TC-04", "04b-2/cargo", i, a, truth=UNOCC, out_eval=oa, result="정답" if oa == UNOCC else ("UNKNOWN" if oa == UNK else "오류"))
    R.rate_rows("TC-04", "04b-2", f"화물 정지 / 점유 대상 움직임(±{motion['amp_cm']} cm, {motion['hz']} Hz 가정)", UNOCC, "cargo", outs_c,
                surface_label(top) + " 높이", note="기준을 바꾸지 않으며 불합격도 그대로 기록")
    R.record("TC-04", "04b-2", "출력 차이 유무", "SR-04", "현재 알고리즘은 시간 변동을 쓰지 않음", f"판정 시점 출력이 다른 시행 {diff}/{n}",
             "알고리즘 특성. 움직임 크기는 근거 없는 가정", surface_label(top) + " 높이", n)


def tc05(R, levels):
    o = R.obj(R.tc05_object) if R.tc05_object else None
    if o is None or levels["TC05_combination"] is None or levels["TC05a_vs_05b"] is None:
        why = []
        if o is None:
            why.append("대상 반사면 정의 없음")
        if levels["TC05_combination"] is None:
            why.append("p_loss·b 수준의 조합 방식 미정")
        if levels["TC05a_vs_05b"] is None:
            why.append("두꺼운 옷(05a)과 담요(05b)의 입력 구분이 문서에 없음")
        R.notrun("TC-05", "TC-05", "흡음 표면에서 감지", "SR-01/02/10/14", "본시험 입력 미확정: " + "; ".join(why))
        return
    base_n, lvl_n = R.n(R.reps["TC-05_base"]), R.n(R.reps["TC-05_level"])
    grid = [("base", 0.0, 0.0, base_n, False)]
    grid += [(f"p{p:g}", p, 0.0, lvl_n, True) for p in levels["p_loss"] if p > 0]
    grid += [(f"b{b:g}", 0.0, b, lvl_n, True) for b in levels["bias_cm"] if b > 0]
    for tag, p, b, n, sens in grid:
        outs, _, truth = R.static_outs("TC-05", tag, "occupant", o["h_cm"], n, p=p, bias=b)
        R.rate_rows("TC-05", tag, f"p_loss={p:g}, 편향 b={b:g} cm", truth, "occupant", outs, surface_label(o), sens=sens,
                    note=("" if R.stage != "main" else "한 요인씩 변경(D7)"))
    if R.stage == "main":
        R.record("TC-05", "05a-05b", "두꺼운 옷(05a)·담요(05b) 구분", "SR-01/02/10/14", "입력 모델이 같으면 따로 검증하지 않음(D7)",
                 "05a와 05b는 같은 입력 모델(위 격자)을 쓰며 두 재질을 따로 검증한 것으로 집계하지 않음",
                 "흡음 표면의 실제 반사 특성은 이 모델에 없음(p_loss·편향 가정 수준으로만 표현)", surface_label(o))


# =====================================================================
#  TC-06, TC-10 (유지 구간)
# =====================================================================
def _hold_trials(R, tc, cond, h, n, p_sched, t_start, window, T=None, det=None, sens=False, desc="", surface="", extra=None):
    scn = Scenario(f"{tc}-{cond}", (Segment(0.0, "occupant", h),), t_start + window + 0.5, T if T is not None else R.T_base,
                   loss_schedule=p_sched)
    det = det or R.dc(temp_comp=R.comp_base)
    fails, nflip_tot, precond_fail, flips_list = 0, 0, 0, []
    for i in range(1, n + 1):
        tr = R.run(tc, cond, scn, i, det, log_samples=True)
        t0 = t_start if t_start is not None else None
        pre_ok = ev.output_at(tr["out_log"], t0) == OCC
        nf = ev.flips(tr["out_log"], t0, t0 + window)
        precond_fail += not pre_ok
        flips_list.append(nf)
        fails += (nf > 0) or (not pre_ok)
        R.trial_row(tc, cond, i, tr, truth=OCC, window_start=t0, window_end=t0 + window, premise_OCC=pre_ok, flips=nf,
                    unknown_entries=sum(1 for _, k, _ in tr["events"] if k == "unknown_entry"))
    R.all_trials_rows(tc, cond, desc, "SR-08", fails, n, "유지 구간 뒤집힘 0회(모든 시행)", surface, sens=sens,
                      detail=f"전제(점유 확정) 불충족 {precond_fail}, 뒤집힘 합계 {sum(flips_list)}")


def tc06(R, levels):
    o = R.obj(R.tc06_object) if R.tc06_object else None
    if o is None:
        R.notrun("TC-06", "TC-06", "상체 기울임 60초 유지", "SR-01/08", "본시험 입력 미확정: 대상 반사면 정의 없음(시험 설계 4.3·12절)")
        return
    n = R.n(R.reps["TC-06_level"], long_run=True)
    for phi, p in zip(levels["tilt_deg"], levels["tilt_p_loss"]):
        cond = f"phi{phi}-p{p:g}"
        _hold_trials(R, "TC-06", cond, o["h_cm"], n, ((0.0, 0.0), (5.0, p)), 5.0, 60.0, sens=(phi != 0),
                     desc=f"기울임 φ={phi}°(p_loss={p:g}) 적용 후 60초", surface=surface_label(o))


def tc10(R, det=None, tag=""):
    o = R.obj(R.tc10_object) if R.tc10_object else None
    if o is None:
        R.notrun("TC-10", "TC-10" + tag, "장시간 점유 유지", "SR-08", "본시험 입력 미확정: 대상 반사면 정의 없음(시험 설계 4.3·12절)")
        return
    # 점유 확정 이후 60초: 확정 시각은 시행마다 다르므로 확정 후 충분한 시점(5.0 s)부터 60초를 관찰
    _hold_trials(R, "TC-10", "hold60" + tag, o["h_cm"], R.n(R.reps["TC-10"], long_run=True), ((0.0, 0.0),), 5.0, 60.0, det=det,
                 desc="같은 자세 60초 유지(점유 확정 후 5.0 s부터 60 s 관찰)", surface=surface_label(o))


# =====================================================================
#  TC-07 (임계값 경계, Δ 직접 주입)
# =====================================================================
def _inject(R, tc, cond, det_cfg, start_mode, delta, hold=3.0):
    det = OccupancyDetector(det_cfg)
    if start_mode is not None:
        det.mode = start_mode
    period = R.cfg.sensor.period_s
    t = 0.0
    steps = int(round(hold / period))
    for _ in range(steps + 1):
        det.decide(round(t, 6), delta, t_req=round(t, 6))
        t += period
    return det.output


def tc07(R, tag="", det=None):
    d = det or R.dc()
    on, off, mid = d.delta_on_cm, d.delta_off_cm, d.delta_mid_cm
    rows = [("07a", UNOCC, on - 1, UNOCC), ("07a", UNOCC, on, OCC), ("07a", UNOCC, on + 1, OCC),
            ("07b", OCC, off + 1, OCC), ("07b", OCC, off, UNOCC), ("07b", OCC, off - 1, UNOCC),
            ("07d", None, mid - 1.5, UNOCC), ("07d", None, mid, OCC), ("07d", None, mid + 1.5, OCC)]
    for sub, start, delta, exp in rows:
        got = _inject(R, "TC-07", sub, d, start, delta)
        R.check("TC-07", f"{sub}{tag}", f"{'전원 꺼짐(최초 판정)' if start is None else start}에서 Δ={delta:g} cm 주입, 3초 관찰", "SR-05", exp, got, got == exp)
    seq_in = [on - 1, on, on - 1, off]
    det_ = OccupancyDetector(d)
    det_.mode = UNOCC
    outs, t = [], 0.0
    for dv in seq_in:
        for _ in range(int(round(3.0 / R.cfg.sensor.period_s))):
            det_.decide(round(t, 6), dv, t_req=round(t, 6)); t += R.cfg.sensor.period_s
        outs.append(det_.output)
    exp = [UNOCC, OCC, OCC, UNOCC]
    R.check("TC-07", f"seq{tag}", f"연속 전이 Δ {' → '.join(f'{x:g}' for x in seq_in)} cm", "SR-05", " → ".join(exp), " → ".join(outs), outs == exp)


def tc07c(R, levels, default_targets):
    tg = levels["TC07c_targets"]
    if tg is None:
        R.notrun("TC-07", "07c", "임계값 ±50% 민감도(원시 거리 통합)", "SR-05", "본시험 입력 미확정: 시험 설계 11.2절에 07c의 대상(높이)이 적혀 있지 않음")
        return
    n = R.n(R.reps["TC-07c_level"])
    pairs = levels.get("TC07c_threshold_pairs") or (("−50%", 5.0, 2.5), ("기준", 10.0, 5.0), ("+50%", 15.0, 7.5))
    for lab, on, off in pairs:
        for name, kind, h in tg:
            outs, _, truth = R.static_outs("TC-07", f"07c-{lab}-{name}", kind, h, n, det=R.dc(delta_on_cm=on, delta_off_cm=off, temp_comp=R.comp_base))
            c = ev.rates(outs, truth)
            dm = (on + off) / 2
            R.record("TC-07", f"07c-{lab}-{name}", f"Δ_on={on:g}, Δ_off={off:g} cm(초기 구간 기준 {dm:g} cm), {name}", "SR-05", f"기록(정답 {truth})",
                     f"정답 {c['correct']}, 오류 {c['error']}, UNKNOWN {c['unknown']}", "임계값 민감도(기록). Δ_on·Δ_off 동시 변경 조합", n=n)


# =====================================================================
#  TC-08, TC-09
# =====================================================================
def tc08(R, tag="", det=None):
    n = R.n(R.reps["TC-08"])
    T1 = R.cfg.evaluation.T_first_s
    for sub, kind, h in (("08a", "occupant", None), ("08b", "empty", 0.0)):
        if sub == "08a":
            o = R.obj(R.tc08_object) if R.tc08_object else None
            if o is None:
                R.notrun("TC-08", "08a", "착석 상태 전원 인가", "SR-07(a)/13", "본시험 입력 미확정: 대상 반사면 정의 없음")
                continue
            h, surf = o["h_cm"], surface_label(o)
        else:
            surf = "빈 좌석"
        outs, trs, truth = R.static_outs("TC-08", sub + tag, kind, h, n, det=det)
        fails, ft = 0, []
        for j, tr in enumerate(trs):
            f = ev.first_valid_time(tr["out_log"])
            rq, rx = req_of(tr, f)
            R.trials[len(R.trials) - len(trs) + j].update(first_valid_decision_t_rx=f, t_req_of_deciding_sample=rq, t_rx_of_deciding_sample=rx)
            wrong = any(v not in (truth, UNK) for tt, v in tr["out_log"])
            ok = f is not None and f <= T1 + 1e-9 and not wrong and ev.output_at(tr["out_log"], 4.9) == truth
            fails += not ok
            ft.append(f if f is not None else float("nan"))
        R.all_trials_rows("TC-08", sub + tag, f"전원 인가(t = 0, SIL 모델) 후 최초 유효 판정 ≤ {T1} s이고 정답", "SR-07(a)", fails, len(trs),
                          "모든 시행에서 최초 유효 판정 ≤ T_first이고 정답", surf,
                          detail=f"최초 유효 판정(수신·처리 시각) {np.nanmin(ft):.3f}–{np.nanmax(ft):.3f} s",
                          note="" if R.stage != "main" else "t = 0 전원 인가 SIL 모델(D8). 차량 시동·센서 전원 관계는 후속 검토")


def _transition(R, tc, cond, seg_fn, new_truth, n, det, surface):
    ev_cfg = R.cfg.evaluation
    rts, fails = [], 0
    for i in range(1, n + 1):
        sd = seed_for(R.base, R.prefix, tc, cond, i)
        tg = round(5.0 + float(np.random.default_rng(sd).uniform(0, R.cfg.sensor.period_s)), 4)   # 사건 시각 위상
        scn = Scenario(f"{tc}-{cond}", seg_fn(tg), 10.0, R.T_base)
        tr = R.run(tc, cond, scn, i, det, seed=sd)
        rt = ev.response_time(tr["out_log"], tg, new_truth, ev_cfg.hold_s, ev_cfg.response_limit_s)
        fails += rt is None
        t_out = None if rt is None else round(tg + rt, 6)
        row = next((r for r in tr["rows"] if t_out is not None and r["t_rx"] is not None and abs(r["t_rx"] - t_out) < 1e-6), None)
        rts.append(rt)
        R.trial_row(tc, cond, i, tr, t_gt=tg, new_truth=new_truth, t_new_output=t_out, response_s=rt,
                    t_req_of_deciding_sample=None if row is None else row["t_req"], t_rx_of_deciding_sample=None if row is None else row["t_rx"],
                    deadline_exceeded=rt is None)
    ok_rt = [x for x in rts if x is not None]
    R.all_trials_rows(tc, cond, f"사건 후 {ev_cfg.response_limit_s:g}초 이내 새 정답, {ev_cfg.hold_s:g}초 유지", "SR-07(b)", fails, n,
                      "모든 시행의 응답 시간 ≤ 3초(기한 초과 0회, 분모 포함)", surface,
                      detail=(f"응답 {min(ok_rt):.3f}–{max(ok_rt):.3f} s" if ok_rt else "응답 없음"))


def tc09(R, tag="", det=None):
    n = R.n(R.reps["TC-09"])
    o = R.obj(R.tc09_object) if R.tc09_object else None
    if o is None:
        for c, d in (("09a", "착석 사건"), ("09b", "이석 사건")):
            R.notrun("TC-09", c, d, "SR-07(b)", "본시험 입력 미확정: 대상 반사면 정의 없음(시험 설계 4.3·12절)")
        return
    h, surf = o["h_cm"], surface_label(o)
    det = det or R.dc(temp_comp=R.comp_base)
    _transition(R, "TC-09", "09a" + tag, lambda tg: (Segment(0.0, "empty"), Segment(tg, "occupant", h)), OCC, n, det, surf)
    _transition(R, "TC-09", "09b" + tag, lambda tg: (Segment(0.0, "occupant", h), Segment(tg, "empty")), UNOCC, n, det, surf)


# =====================================================================
#  TC-11 (온도)
# =====================================================================
def tc11(R):
    """온도 0·20·50 °C × 보정 무·유. 대상은 빈 좌석·R2(TC-02b 대응)·R0(TC-04a 대응). 구성·대상별로 따로 판정하고 합치지 않음(D3·D5)."""
    temps = (0.0, 20.0, 50.0)
    o = R.obj("O-B")
    for comp in (False, True):
        for T in temps:
            tag = f"-T{T:g}-{'comp' if comp else 'nocomp'}"
            sub = ("11b" if comp else "11a") + tag
            cl = f"T={T:g}°C, 보정 {'유' if comp else '무'}"
            # 대상 시험과 같은 횟수·기준 (TC-01, TC-02b, TC-04a)
            outs, _, truth = R.static_outs("TC-11", f"{sub}/TC-01", "empty", 0.0, R.n(R.reps["TC-01"]), T, comp)
            R.rate_rows("TC-11", f"{sub}/TC-01", f"빈 좌석, {cl}", truth, "empty", outs, "빈 좌석", sr="SR-09")
            if o is None:
                R.notrun("TC-11", f"{sub}/TC-02b", "O-B 착석(온도)", "SR-09", "본시험 입력 미확정: O-B 반사면 정의 없음")
            else:
                outs, _, truth = R.static_outs("TC-11", f"{sub}/TC-02b", "occupant", o["h_cm"], R.n(R.reps["TC-02"]), T, comp)
                R.rate_rows("TC-11", f"{sub}/TC-02b", (f"R2 착석(TC-02b 대응), {cl}" if R.vl else f"O-B 착석, {cl}"), truth, "occupant", outs,
                            surface_label(o), sr="SR-09", note=R.vl.strip() and "가상 반사면 대체 조건")
            outs, _, truth = R.static_outs("TC-11", f"{sub}/TC-04a", "cargo", R.cfg.geometry.R0_cm, R.n(R.reps["TC-04"]), T, comp)
            R.rate_rows("TC-11", f"{sub}/TC-04a", f"낮은 화물 R0, {cl}", truth, "cargo", outs, "R0(가정)", sr="SR-09")
    if R.stage == "main":
        R.record("TC-11", "coverage", "TC-11이 실제로 다룬 조건(SR-09 전체 충족 판정 안 함)", "SR-09",
                 "SR-09 전체 충족 판정은 하지 않음(D3)",
                 "다룬 조건: 온도 0·20·50 °C, 보정 무·유, 대상 빈 좌석·R2·R0(각 300회), 고정 σ=1 cm·p_loss=0·편향 0, 온도 입력 오차 U(-2,+2) °C(가정). "
                 "다루지 않은 조건: 0–50 °C 사이 다른 온도, 다른 대상(R1·R3·실제 O-A/B/C), 잡음·손실·편향과 온도의 조합, 습도·온도 변화 중 시험, 온도 센서 실제 오차 특성",
                 "구성·온도·대상별로 따로 판정함(합산 없음). 제한된 대상 결과만으로 SR-09 전체 충족을 선언하지 않음. 보정 채택 여부는 본시험 후 결정", "-")


def tc12(R):
    R.notrun("TC-12", "TC-12", "소형 대상 O-S 기록(참고)", "없음(참고)", "미실행(D1, O-S): O-S 치수 없음(시험 설계 4.3, CPD 7.6.1은 평가 대상만 제시). 합격 판정 대상이 아님")


# =====================================================================
#  TC-13, 14, 15 (고장 주입)
# =====================================================================
def recovery_info(tr):
    e = tr["events"]
    entry = [t for t, k, _ in e if k == "unknown_entry"]
    first = [t for t, k, _ in e if k == "recovery_first_valid" and entry and t > entry[0]]
    conf = [t for t, k, _ in e if k == "valid_decision" and entry and t > entry[0]]
    return entry, first, conf


def tc13(R, tag="", det=None):
    M, T_rec = R.cfg.detector.M, R.cfg.evaluation.T_recover_s
    det = det or R.dc(temp_comp=R.comp_base)
    n_noisy = R.n(R.reps["TC-13_noisy"])
    for sub, kind, hname in (("13a", "occupant", R.tc13_object), ("13b", "empty", None)):
        if kind == "occupant":
            o = R.obj(hname) if hname else None
            if o is None:
                R.notrun("TC-13", "13a", "점유 상태에서 에코 연속 제거", "SR-10/13", "본시험 입력 미확정: 대상 반사면 정의 없음")
                continue
            h, surf = o["h_cm"], surface_label(o)
        else:
            h, surf = 0.0, "빈 좌석"
        truth = OCC if kind == "occupant" else UNOCC
        for n_drop in (M - 1, M, M + 1):
            f = Faults(drop_echo=frozenset(range(30, 30 + n_drop)))
            scn = static(f"TC-13-{sub}-{n_drop}", kind, h, duration=7.0, T_air=R.T_base, faults=f)
            for mode, n in (("det", 1), ("noisy", n_noisy)):
                cond = f"{sub}-drop{n_drop}-{mode}{tag}"
                bad = 0
                recs = []
                for i in range(1, n + 1):
                    tr = R.run("TC-13", cond, scn, i, det, sigma=0.0 if mode == "det" else None, p_loss=0.0 if mode == "det" else None,
                               log_samples=True)
                    entry, first, conf = recovery_info(tr)
                    wrong = any(v not in (truth, UNK) for _, v in tr["out_log"])
                    final = ev.output_at(tr["out_log"], 6.9)
                    rt = conf[0] - first[0] if (entry and first and conf) else None
                    if n_drop < M:
                        ok = not entry and not wrong and final == truth
                    else:
                        ok = bool(entry) and rt is not None and rt <= T_rec + 1e-9 and not wrong and final == truth
                    bad += not ok
                    if rt is not None:
                        recs.append(rt)
                    rq_f, rx_f = req_of(tr, first[0] if first else None)
                    rq_c, rx_c = req_of(tr, conf[0] if conf else None)
                    R.trial_row("TC-13", cond, i, tr, truth=truth, unknown_entered=bool(entry), recovery_s=rt, wrong_valid_output=wrong,
                                final_output=final, ok=ok, recovery_first_valid_t_req=rq_f, recovery_first_valid_t_rx=rx_f,
                                valid_decision_t_req=rq_c, valid_decision_t_rx=rx_c)
                exp = ("이전 상태 유지(UNKNOWN 없음)" if n_drop < M else f"UNKNOWN 후 복구 ≤ {T_rec:g} s, 정답 복귀") + (", 점유에서 UNOCCUPIED 없음" if kind == "occupant" else "")
                det_s = f"복구 {min(recs):.3f}–{max(recs):.3f} s" if recs else "복구 없음"
                if mode == "det":
                    R.check("TC-13", cond, f"{sub} 에코 {n_drop}회 연속 제거(결정적)", "SR-10/13", exp, f"{'일치' if not bad else '불일치'}; {det_s}", bad == 0, surface=surf)
                else:
                    R.all_trials_rows("TC-13", cond, f"{sub} 에코 {n_drop}회 연속 제거(잡음 포함)", "SR-10/13", bad, n, exp, surf, detail=det_s)


def tc14(R, tag="", det=None):
    M = R.cfg.detector.M
    det = det or R.dc(temp_comp=R.comp_base)
    for sub, kind, hname in (("occ", "occupant", R.tc14_object), ("empty", "empty", None)):
        if kind == "occupant":
            o = R.obj(hname) if hname else None
            if o is None:
                R.notrun("TC-14", "occ", "점유 상태에서 범위 밖 거리 치환", "SR-11", "본시험 입력 미확정: 대상 반사면 정의 없음")
                continue
            h, surf = o["h_cm"], surface_label(o)
        else:
            h, surf = 0.0, "빈 좌석"
        truth = OCC if kind == "occupant" else UNOCC
        for val in (1.0, 401.0):
            for cnt, role in ((M, "시험"), (M - 1, "경계 확인(문서 밖 추가)")):
                subs = tuple((30 + j, val) for j in range(cnt))
                scn = static(f"TC-14-{sub}-{val}-{cnt}", kind, h, duration=3.0 + 4.0, T_air=R.T_base, faults=Faults(substitute_cm=subs))
                cond = f"{sub}-{val:g}cm-x{cnt}{tag}"
                tr = R.run("TC-14", cond, scn, 1, det, sigma=0.0, p_loss=0.0)
                entry, _, _ = recovery_info(tr)
                inval = sum(1 for r in tr["rows"] if r["cause"] == "substitute" and r["d_med_cm"] is None)
                wrong = any(v not in (truth, UNK) for _, v in tr["out_log"])
                final = ev.output_at(tr["out_log"], 6.9)
                ok = (bool(entry) if cnt >= M else not entry) and not wrong and inval == cnt and final == truth
                R.trial_row("TC-14", cond, 1, tr, truth=truth, substituted=cnt, invalid_by_range=inval, unknown_entered=bool(entry), final_output=final, ok=ok)
                exp = "무효 처리, " + ("M회 이상 → UNKNOWN 후 복구" if cnt >= M else "상태 유지(UNKNOWN 없음)")
                R.check("TC-14", cond, f"{sub} {val:g} cm로 {cnt}회 치환({role})", "SR-11", exp,
                        f"무효 {inval}/{cnt}, UNKNOWN {'진입' if entry else '없음'}, 최종 {final}", ok, surface=surf)


def tc15(R, tag="", det=None, n_extra=0):
    o = R.obj(R.tc15_object) if R.tc15_object else None
    if o is None:
        R.notrun("TC-15", "TC-15", "갱신 중단과 복구", "SR-12/13", "본시험 입력 미확정: 대상 반사면 정의 없음")
        return
    Ts, per, T_rec = R.cfg.detector.T_stale_s, R.cfg.sensor.period_s, R.cfg.evaluation.T_recover_s
    det = det or R.dc(temp_comp=R.comp_base)
    scn = static("TC-15", "occupant", o["h_cm"], duration=8.0, T_air=R.T_base, faults=Faults(stall=((3.0, 5.0),)))
    for mode, n in (("det", 1), ("noisy-참고", n_extra)):
        bad, lat, rec = 0, [], []
        for i in range(1, n + 1):
            tr = R.run("TC-15", f"stall2s-{mode}{tag}", scn, i, det, sigma=0.0 if mode == "det" else None, p_loss=0.0 if mode == "det" else None)
            last_valid = max(r["t_rx"] for r in tr["rows"] if r["t_rx"] is not None and r["t_rx"] < 3.0 and r["status"] == "echo")
            entry, first, conf = recovery_info(tr)
            lt = entry[0] - last_valid if entry else None
            rt = conf[0] - first[0] if (first and conf) else None
            ok = (lt is not None and lt <= Ts + per + 1e-9 and rt is not None and rt <= T_rec + 1e-9 and ev.output_at(tr["out_log"], 7.9) == OCC)
            bad += not ok
            lat.append(lt); rec.append(rt)
            rq_f, rx_f = req_of(tr, first[0] if first else None)
            rq_c, rx_c = req_of(tr, conf[0] if conf else None)
            R.trial_row("TC-15", f"stall2s-{mode}{tag}", i, tr, truth=OCC, last_valid_rx=last_valid, unknown_entry_t=entry[0] if entry else None,
                        to_unknown_s=lt, recovery_first_valid_t=first[0] if first else None, valid_decision_t=conf[0] if conf else None,
                        recovery_s=rt, ok=ok, recovery_first_valid_t_req=rq_f, recovery_first_valid_t_rx=rx_f,
                        valid_decision_t_req=rq_c, valid_decision_t_rx=rx_c)
        if n == 0:
            continue
        fl = [x for x in lat if x is not None]; fr = [x for x in rec if x is not None]
        d = f"UNKNOWN 전환 {min(fl):.3f}–{max(fl):.3f} s(기한 {Ts + per:g}), 복구 {min(fr):.3f}–{max(fr):.3f} s(기한 {T_rec:g})" if fl and fr else "전환 또는 복구 없음"
        if mode == "det":
            R.check("TC-15", f"stall2s-det{tag}", "결과 전달 2초 중단 후 재개(결정적, 반복 1)", "SR-12/13",
                    f"마지막 유효 샘플부터 ≤ {Ts + per:g} s에 UNKNOWN, 복구 첫 유효 샘플부터 ≤ {T_rec:g} s", d, bad == 0, surface=surface_label(o))
        else:
            R.all_trials_rows("TC-15", f"stall2s-noisy{tag}", "결과 전달 2초 중단(잡음 포함, 계획 외 참고)", "SR-12", bad, n, "전환·복구 기한 충족", surface_label(o), sens=True, detail=d,
                              note="시험 설계 11.2절은 반복 1회만 요구함. 사전점검에서 T_db 영향 확인용")


# =====================================================================
#  TC-16
# =====================================================================
def tc16(R):
    p = R.cfg.sensor.period_s
    R.check("TC-16", "16a", "설정값 검사: 측정 요청 주기", "SR-06", "> 0.060 s", f"{p:.3f} s", p > 0.060)
    allint = [x for v in R.req_intervals.values() for x in v]
    if not allint:
        R.notrun("TC-16", "16b", "TC-01·TC-02 로그 간격 분석", "SR-06", "TC-01·TC-02 로그가 없어 간격 분석 불가")
    else:
        mi = min(allint)
        R.check("TC-16", "16b", f"TC-01·TC-02 로그의 측정 요청 최소 간격({'+'.join(R.req_intervals)} 시행 로그)", "SR-06", "모든 간격 > 0.060 s", f"최소 {mi:.3f} s", mi > 0.060)


# =====================================================================
#  추가 시험 P-08-R0 (예비시험 이후 추가: 높은 온도에서 낮은 화물)
# =====================================================================
def p08_r0(R, n=10):
    """낮은 화물 R0를 0·20·50 °C에서 온도 보정 유·무로 비교. 잡음 없는 계산값과 무작위 시행을 따로 기록. 합격 판정 없음."""
    G, D, S = R.cfg.geometry, R.cfg.detector, R.cfg.sensor
    rows = []
    for comp in (False, True):
        for T in (0.0, 20.0, 50.0):
            c_true = speed_of_sound(T)
            d_true = G.H_s_cm - G.R0_cm
            c_used = speed_of_sound(T) if comp else D.c_fixed_mps          # 계산값은 온도 입력이 정확하다고 둠
            delta_calc = D.d_empty_cm - d_true * c_used / c_true
            cond = f"R0-T{T:g}-{'comp' if comp else 'nocomp'}"
            dc = R.dc(temp_comp=comp)
            scn = static(f"P08R0-{cond}", "cargo", G.R0_cm, duration=5.0, T_air=T)
            trd = R.run("P-08-R0", cond + "/noiseless", scn, 0, dc, sigma=0.0, p_loss=0.0)
            o_det = ev.output_at(trd["out_log"], R.cfg.evaluation.t_eval_s)
            dmeds = [r["delta_cm"] for r in trd["rows"] if r["delta_cm"] is not None]
            outs, firsts = [], []
            for i in range(1, n + 1):
                tr = R.run("P-08-R0", cond + "/random", scn, i, dc, log_samples=(i == 1))
                o = ev.output_at(tr["out_log"], R.cfg.evaluation.t_eval_s)
                outs.append(o)
                R.trial_row("P-08-R0", cond + "/random", i, tr, truth=UNOCC, out_eval=o, T_air=T, comp=comp, T_input_C=tr["T_input_C"])
            cnt = {k: outs.count(k) for k in (OCC, UNOCC, UNK)}
            rows.append({"stage": R.stage, "T_C": T, "temp_comp": comp, "truth": UNOCC,
                         "delta_calc_noiseless_cm": round(delta_calc, 3),
                         "delta_sim_noiseless_cm": round(float(np.median(dmeds)), 3) if dmeds else None,
                         "T_input_noiseless_run_C": None if trd["T_input_C"] is None else round(trd["T_input_C"], 3),
                         "noiseless_output_at_t_eval": o_det,
                         "random_n": n, "random_OCC": cnt[OCC], "random_UNOCC": cnt[UNOCC], "random_UNKNOWN": cnt[UNK],
                         "delta_on_cm": D.delta_on_cm, "delta_mid_cm": D.delta_mid_cm,
                         "calc_exceeds_delta_on": delta_calc >= D.delta_on_cm, "calc_exceeds_delta_mid": delta_calc >= D.delta_mid_cm})
            R.record("P-08-R0", cond, f"R0 낮은 화물, T={T:g}°C, 보정 {'유' if comp else '무'}", "SR-04/09",
                     f"기록(정답 {UNOCC})", f"잡음 없는 계산 Δ {delta_calc:.2f} cm, 잡음 없는 시행 출력 {o_det}; 무작위 {n}회: OCC {cnt[OCC]}, UNOCC {cnt[UNOCC]}, UNK {cnt[UNK]}",
                     "추가 시험. 합격 판정 없음. 온도 입력 오차 ±2 °C는 가정" if comp else "추가 시험. 합격 판정 없음", "R0(가정)", n)
    return rows
