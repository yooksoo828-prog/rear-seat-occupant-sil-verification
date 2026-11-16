"""예비시험 P-01~P-08 실행기 (5단계 문서 v0.4.1, 10절).

실행:  python3 run_prelim.py [결과폴더]
예비시험은 구현과 시험 환경의 문제를 찾는 단계이며, 결과를 본시험의 통계적
성능 입증으로 쓰지 않음.
"""
import csv, json, os, platform, sys, zlib
from dataclasses import replace

import numpy as np

from sil.config import PrelimConfig, speed_of_sound
from sil.scenario import Scenario, Segment, Faults, static, OCC, UNOCC, UNK
from sil.simulate import run_trial
from sil.detector import OccupancyDetector, INIT, UNKNOWN
from sil import evaluate as ev

CFG = PrelimConfig()
G, S, D, E = CFG.geometry, CFG.sensor, CFG.detector, CFG.evaluation
OUT = sys.argv[1] if len(sys.argv) > 1 else "results"
RESULTS = []          # 시험별 기대/실제/일치/원인
TRIAL_ROWS, OUTLOG_ROWS, EVENT_ROWS = [], [], []


def seed_for(test, case, i):
    return (E.base_seed * 1000 + zlib.crc32(f"{test}/{case}".encode()) % 997) * 100 + i


def log_trial(test, case, i, tr):
    for r in tr["rows"]:
        TRIAL_ROWS.append({"test": test, "case": case, "trial": i, "seed": tr["seed"], **r})
    for t, v in tr["out_log"]:
        OUTLOG_ROWS.append({"test": test, "case": case, "trial": i, "seed": tr["seed"], "t": t, "output": v})
    for t, k, d in tr["events"]:
        EVENT_ROWS.append({"test": test, "case": case, "trial": i, "seed": tr["seed"], "t": t, "event": k, "detail": d})


def record(test, case, expected, actual, match, cause, note=""):
    RESULTS.append({"test": test, "case": case, "expected": expected, "actual": actual,
                    "match": match, "cause": cause, "note": note})


def trials(test, case, scn, n, det_cfg=None, sigma=None, p_loss=None, bias=None, det_first=True):
    """결정적 1회(잡음·손실 0) + 무작위 n회."""
    out = []
    if det_first:
        tr = run_trial(scn, CFG, seed_for(test, case, 0), det_cfg, sigma=0.0, p_loss=0.0, bias=bias)
        log_trial(test, case + "/det", 0, tr)
        out.append(("det", tr))
    for i in range(1, n + 1):
        tr = run_trial(scn, CFG, seed_for(test, case, i), det_cfg, sigma, p_loss, bias)
        log_trial(test, case + "/rand", i, tr)
        out.append(("rand", tr))
    return out


def summarize_outputs(trs, t_eval):
    outs = [ev.output_at(tr["out_log"], t_eval) for _, tr in trs]
    return {k: outs.count(k) for k in (OCC, UNOCC, UNK)}


def fmt(c):
    return f"OCC {c[OCC]}, UNOCC {c[UNOCC]}, UNK {c[UNK]}"


# ---------------- P-01 기본 동작 ----------------
def p01():
    cases = [("empty", "empty", 0.0, UNOCC), ("R1", "occupant", G.R1_cm, OCC),
             ("R2", "occupant", G.R2_cm, OCC), ("R3", "occupant", G.R3_cm, OCC)]
    for name, kind, h, truth in cases:
        scn = static(f"P01-{name}", kind, h, duration=5.0)
        trs = trials("P-01", name, scn, E.n_random)
        det_out = ev.output_at(trs[0][1]["out_log"], E.t_eval_s)
        record("P-01", f"{name} 결정적", truth, det_out, det_out == truth,
               "-" if det_out == truth else "확인 필요")
        cnt = summarize_outputs(trs[1:], E.t_eval_s)
        ok = cnt[truth] == E.n_random
        record("P-01", f"{name} 무작위 {E.n_random}회(σ=1 cm)", f"{truth} {E.n_random}회", fmt(cnt), ok,
               "-" if ok else "확인 필요")
        # 로그 완전성: 모든 요청이 기록되었는가
        n_req = int(round(scn.duration_s / S.period_s)) + 1
        complete = all(len(tr["rows"]) == n_req for _, tr in trs)
        record("P-01", f"{name} 로그 완전성", f"요청 {n_req}건 모두 기록",
               "모두 기록" if complete else "누락 있음", complete, "-" if complete else "구현 오류")
        # 지표 계산 점검: rates()와 손 계산(직접 세기) 비교
        outs = [ev.output_at(tr["out_log"], E.t_eval_s) for _, tr in trs[1:]]
        r = ev.rates(outs, truth)
        hand = (sum(1 for o in outs if o == truth), sum(1 for o in outs if o not in (truth, UNK)),
                sum(1 for o in outs if o == UNK))
        same = (r["correct"], r["error"], r["unknown"]) == hand and r["n"] == len(outs)
        record("P-01", f"{name} 지표 계산 점검", f"손 계산 {hand}", f"함수 {(r['correct'], r['error'], r['unknown'])}",
               same, "-" if same else "구현 오류")
    # SR-06 측정 요청 간격
    scn = static("P01-interval", "empty", duration=5.0)
    tr = run_trial(scn, CFG, seed_for("P-01", "interval", 0))
    mi = ev.min_request_interval(tr["req_times"])
    record("P-01", "측정 요청 최소 간격(SR-06)", "> 0.060 s", f"{mi:.3f} s", mi > 0.060, "-")


# ---------------- P-02 같은 거리 입력의 가방 ----------------
def p02():
    scn = static("P02-a", "cargo", G.R0_cm, duration=5.0)
    trs = trials("P-02", "a-R0", scn, E.n_random)
    cnt = summarize_outputs(trs, E.t_eval_s)
    record("P-02", "(a) R0 화물(결정적+무작위 11회)", f"UNOCC 11회", fmt(cnt), cnt[UNOCC] == 11,
           "-" if cnt[UNOCC] == 11 else "확인 필요")
    # (b-1) 같은 정지 거리 이력: 같은 시드로 화물과 점유 반사면을 비교
    for h, label in ((G.R1_cm, "R1"), (G.R2_cm, "R2")):
        cargo = static(f"P02-b1-cargo-{label}", "cargo", h, duration=5.0)
        occ = static(f"P02-b1-occ-{label}", "occupant", h, duration=5.0)
        same_in, same_out, cargo_outs = 0, 0, []
        for i in range(0, E.n_random + 1):
            sg, sp = (0.0, 0.0) if i == 0 else (None, None)
            sd = seed_for("P-02", f"b1-{label}", i)
            a = run_trial(cargo, CFG, sd, sigma=sg, p_loss=sp)
            b = run_trial(occ, CFG, sd, sigma=sg, p_loss=sp)
            log_trial("P-02", f"b1-{label}/cargo", i, a)
            log_trial("P-02", f"b1-{label}/occupant", i, b)
            same_in += [r["d_conv_cm"] for r in a["rows"]] == [r["d_conv_cm"] for r in b["rows"]]
            same_out += a["out_log"] == b["out_log"]
            cargo_outs.append(ev.output_at(a["out_log"], E.t_eval_s))
        n = E.n_random + 1
        c = {k: cargo_outs.count(k) for k in (OCC, UNOCC, UNK)}
        record("P-02", f"(b-1) 화물 윗면 = {label} 높이, 같은 정지 거리 이력 {n}회",
               "요구(SR-04): UNOCC / 예상: 사람과 출력 동일(구분 불가)",
               f"입력 동일 {same_in}/{n}, 출력 동일 {same_out}/{n}; 화물 출력 {fmt(c)}",
               False if c[UNOCC] < n else True, "알고리즘 특성(거리 입력만으로 구분 불가)",
               "SR-04 기준은 바꾸지 않고 불일치를 그대로 기록")
    # (b-2) 점유 반사면에만 움직임 가정: 진폭 1 cm, 0.25 Hz [프로젝트 가정]
    amp, hz = 1.0, 0.25
    cargo = static("P02-b2-cargo", "cargo", G.R1_cm, duration=5.0)
    occ = static("P02-b2-occ", "occupant", G.R1_cm, duration=5.0, motion=(amp, hz))
    diff_out, cargo_outs, occ_outs = 0, [], []
    for i in range(0, E.n_random + 1):
        sg = 0.0 if i == 0 else None
        sd = seed_for("P-02", "b2", i)
        a = run_trial(cargo, CFG, sd, sigma=sg, p_loss=sg)
        b = run_trial(occ, CFG, sd, sigma=sg, p_loss=sg)
        log_trial("P-02", "b2/cargo", i, a)
        log_trial("P-02", "b2/occupant-motion", i, b)
        oa, ob = ev.output_at(a["out_log"], E.t_eval_s), ev.output_at(b["out_log"], E.t_eval_s)
        cargo_outs.append(oa); occ_outs.append(ob)
        diff_out += oa != ob
    n = E.n_random + 1
    ca = {k: cargo_outs.count(k) for k in (OCC, UNOCC, UNK)}
    cb = {k: occ_outs.count(k) for k in (OCC, UNOCC, UNK)}
    record("P-02", f"(b-2) 사람만 움직임 가정(±{amp} cm, {hz} Hz), 화물 정지 {n}회",
           "출력 차이 유무 기록(현재 알고리즘은 시간 변동을 쓰지 않음)",
           f"판정 시점 출력이 다른 시행 {diff_out}/{n}; 화물 {fmt(ca)}; 사람 {fmt(cb)}",
           "기록", "알고리즘 특성(시간 변동 미사용)", "움직임 크기는 근거 없는 가정")


# ---------------- P-03 임계값 경계·초기 히스테리시스 ----------------
def run_delta_sequence(det_cfg, start_mode, deltas, hold=3.0):
    """필터 뒤 Δ 직접 주입. 입력마다 독립 초기화하지 않는 연속 전이용."""
    det = OccupancyDetector(det_cfg)
    if start_mode is not None:
        det.mode = start_mode
    t, outs = 0.0, []
    for d in deltas:
        t_end = t + hold
        while t < t_end - 1e-9:
            det.decide(round(t, 6), d)
            t = round(t + S.period_s, 6)
        outs.append(det.output)
    return outs


def p03():
    for tdb in (0.0, 0.5):
        dc = replace(D, T_db_s=tdb)
        tag = f"T_db={tdb}"
        checks = [(UNOCC, 9.0, UNOCC), (UNOCC, 10.0, OCC), (UNOCC, 11.0, OCC),
                  (OCC, 6.0, OCC), (OCC, 5.0, UNOCC), (OCC, 4.0, UNOCC),
                  (None, 6.0, UNOCC), (None, 7.5, OCC), (None, 9.0, OCC)]
        for start, d, exp in checks:
            got = run_delta_sequence(dc, start, [d])[0]
            st = "최초 판정" if start is None else start
            record("P-03", f"{tag} {st}에서 Δ={d} cm", exp, got, got == exp, "-" if got == exp else "확인 필요")
        seq = run_delta_sequence(dc, UNOCC, [9.0, 10.0, 9.0, 5.0])
        exp = [UNOCC, OCC, OCC, UNOCC]
        record("P-03", f"{tag} 연속 전이 9→10→9→5 cm", " → ".join(exp), " → ".join(seq), seq == exp,
               "-" if seq == exp else "확인 필요")


# ---------------- P-04 초기화와 최초 판정 ----------------
def p04():
    for name, kind, h, truth in (("R2", "occupant", G.R2_cm, OCC), ("empty", "empty", 0.0, UNOCC)):
        scn = static(f"P04-{name}", kind, h, duration=5.0)
        trs = trials("P-04", name, scn, E.n_random)
        fvt, wrong_after = [], 0
        for _, tr in trs:
            f = ev.first_valid_time(tr["out_log"])
            fvt.append(f)
            wrong_after += any(v not in (truth,) for tt, v in tr["out_log"] if f is not None and tt >= f)
        ok_t = all(f is not None and f <= E.T_first_s for f in fvt)
        record("P-04", f"{name} 최초 유효 판정 시각({len(trs)}회)", f"모두 ≤ {E.T_first_s} s, 이전은 UNKNOWN",
               f"{min(fvt):.4f}–{max(fvt):.4f} s", ok_t, "-" if ok_t else "확인 필요")
        record("P-04", f"{name} 최초 판정 이후 출력", f"계속 {truth}", f"정답 외 출력 시행 {wrong_after}/{len(trs)}",
               wrong_after == 0, "-" if wrong_after == 0 else "확인 필요")


# ---------------- P-05 에코 없음과 복구 ----------------
def recovery_info(tr):
    ev_ = tr["events"]
    entry = [t for t, k, _ in ev_ if k == "unknown_entry"]
    first = [t for t, k, _ in ev_ if k == "recovery_first_valid" and entry and t > entry[0]]
    conf = [t for t, k, _ in ev_ if k == "valid_decision" and entry and t > entry[0]]
    return entry, first, conf


def p05():
    start = 30  # t = 3.0 s 요청부터
    for name, kind, h, truth in (("R2", "occupant", G.R2_cm, OCC), ("empty", "empty", 0.0, UNOCC)):
        for n_drop in (D.M - 1, D.M, D.M + 1):
            f = Faults(drop_echo=frozenset(range(start, start + n_drop)))
            scn = static(f"P05-{name}-{n_drop}", kind, h, duration=7.0, faults=f)
            trs = trials("P-05", f"{name}-drop{n_drop}", scn, E.n_random)
            n = len(trs)
            n_entry, rec_ok, wrong, final_ok, rec_t = 0, 0, 0, 0, []
            for _, tr in trs:
                entry, first, conf = recovery_info(tr)
                n_entry += bool(entry)
                if entry and first and conf:
                    rt = conf[0] - first[0]
                    rec_t.append(rt)
                    rec_ok += rt <= E.T_recover_s + 1e-9
                wrong += any(v not in (truth, UNK) for tt, v in tr["out_log"])
                final_ok += ev.output_at(tr["out_log"], 6.9) == truth
            if n_drop < D.M:
                ok = n_entry == 0 and wrong == 0 and final_ok == n
                record("P-05", f"{name} 에코 {n_drop}회 연속 제거({n}회)", "UNKNOWN 진입 없음, 이전 상태 유지",
                       f"UNKNOWN 진입 {n_entry}/{n}, 정답 외 유효 출력 {wrong}/{n}", ok, "-" if ok else "확인 필요")
            else:
                ok = n_entry == n and rec_ok == n and wrong == 0 and final_ok == n
                rt = f"{min(rec_t):.3f}–{max(rec_t):.3f} s" if rec_t else "복구 없음"
                record("P-05", f"{name} 에코 {n_drop}회 연속 제거({n}회)",
                       f"UNKNOWN 진입, 복구 ≤ {E.T_recover_s} s, 점유에서 UNOCC 없음",
                       f"진입 {n_entry}/{n}, 복구 시간 {rt}, 정답 외 유효 출력 {wrong}/{n}, 최종 정답 {final_ok}/{n}",
                       ok, "-" if ok else "확인 필요")


# ---------------- P-06 갱신 중단·범위 밖 값 ----------------
def p06():
    f = Faults(stall=((3.0, 5.0),))
    scn = static("P06-stall", "occupant", G.R2_cm, duration=8.0, faults=f)
    trs = trials("P-06", "stall-R2", scn, E.n_random)
    n = len(trs)
    ok_e, ok_r, finals, lat, rec = 0, 0, 0, [], []
    for _, tr in trs:
        rx = [r["t_rx"] for r in tr["rows"] if r["t_rx"] is not None and r["t_rx"] < 3.0 and r["status"] == "echo"]
        last_valid = max(rx)
        entry, first, conf = recovery_info(tr)
        if entry:
            lat.append(entry[0] - last_valid)
            ok_e += entry[0] - last_valid <= D.T_stale_s + S.period_s + 1e-9
        if first and conf:
            rec.append(conf[0] - first[0])
            ok_r += conf[0] - first[0] <= E.T_recover_s + 1e-9
        finals += ev.output_at(tr["out_log"], 7.9) == OCC
    ok = ok_e == n and ok_r == n and finals == n
    record("P-06", f"R2 결과 전달 2 s 중단({n}회)",
           f"마지막 유효 샘플부터 ≤ {D.T_stale_s + S.period_s:.1f} s 내 UNKNOWN, 복구 ≤ {E.T_recover_s} s",
           f"UNKNOWN 전환 {min(lat):.3f}–{max(lat):.3f} s, 복구 {min(rec):.3f}–{max(rec):.3f} s, 최종 정답 {finals}/{n}",
           ok, "-" if ok else "확인 필요")
    for name, kind, h, truth in (("R2", "occupant", G.R2_cm, OCC), ("empty", "empty", 0.0, UNOCC)):
        for val in (1.0, 401.0):
            for cnt in (D.M - 1, D.M):
                sub = tuple((30 + j, val) for j in range(cnt))
                scn = static(f"P06-sub-{name}", kind, h, duration=7.0, faults=Faults(substitute_cm=sub))
                tr = run_trial(scn, CFG, seed_for("P-06", f"sub-{name}-{val}-{cnt}", 0), sigma=0.0, p_loss=0.0)
                log_trial("P-06", f"sub-{name}-{val}cm-x{cnt}/det", 0, tr)
                entry, first, conf = recovery_info(tr)
                inval = sum(1 for r in tr["rows"] if r["cause"] == "substitute" and r["d_med_cm"] is None)
                wrong = any(v not in (truth, UNK) for tt, v in tr["out_log"])
                if cnt < D.M:
                    ok = not entry and not wrong
                    exp, act = "무효 처리, 상태 유지", f"UNKNOWN 진입 {'있음' if entry else '없음'}"
                else:
                    ok = bool(entry) and not wrong and ev.output_at(tr["out_log"], 6.9) == truth
                    exp, act = "무효 처리, UNKNOWN 후 복구", f"UNKNOWN 진입 {'있음' if entry else '없음'}, 최종 {ev.output_at(tr['out_log'], 6.9)}"
                record("P-06", f"{name} 값 {val:g} cm로 {cnt}회 치환(결정적)", exp, act, ok, "-" if ok else "확인 필요")


# ---------------- P-07 전체 응답 시간 ----------------
def p07():
    for tdb in (0.0, 0.5):
        dc = replace(D, T_db_s=tdb)
        for name, segs_fn, new in (
            ("착석(빈 좌석→R1)", lambda tg: (Segment(0.0, "empty"), Segment(tg, "occupant", G.R1_cm)), OCC),
            ("이석(R1→빈 좌석)", lambda tg: (Segment(0.0, "occupant", G.R1_cm), Segment(tg, "empty")), UNOCC)):
            rts, fails = [], 0
            for i in range(0, E.n_random + 1):
                sd = seed_for("P-07", f"{name}-{tdb}", i)
                # 사건 시각 위상: 결정적 시행은 요청 시각과 일치(5.0 s), 무작위 시행은 5.0 + U(0, 0.1) s
                tg = 5.0 if i == 0 else round(5.0 + float(np.random.default_rng(sd).uniform(0, S.period_s)), 4)
                scn = Scenario(f"P07-{name}", segs_fn(tg), 10.0)
                tr = run_trial(scn, CFG, sd, dc, sigma=0.0 if i == 0 else None, p_loss=0.0 if i == 0 else None)
                log_trial("P-07", f"{name}-Tdb{tdb}/{'det' if i == 0 else 'rand'}", i, tr)
                rt = ev.response_time(tr["out_log"], tg, new, E.hold_s, E.response_limit_s)
                if rt is None:
                    fails += 1
                else:
                    rts.append(rt)
            exp_lo, exp_hi = 0.2 + tdb, 0.3 + tdb
            ok = fails == 0 and all(exp_lo - 0.01 <= r <= exp_hi + 0.01 for r in rts)
            n_extra = sum(1 for r in rts if exp_hi + 0.01 < r <= exp_hi + S.period_s + 0.01)
            if ok:
                cause = "-"
            elif fails == 0 and n_extra == sum(1 for r in rts if r > exp_hi + 0.01):
                cause = (f"문서 모호함: T_db를 후보 수신 시각부터의 시간으로 재면 에코 수신 시각의 흔들림(수십 µs) 때문에 "
                         f"0.5 s에 조금 못 미쳐 한 주기(0.1 s)를 더 기다림. 해당 {n_extra}/{len(rts)}회 (events.csv)")
            else:
                cause = "확인 필요"
            record("P-07", f"T_db={tdb} {name} 11회",
                   f"계산 예상 약 {exp_lo:.1f}–{exp_hi:.1f} s(+에코 수신 지연), 목표 ≤ 3 s",
                   f"{min(rts):.3f}–{max(rts):.3f} s, 기한 초과 {fails}회" if rts else f"기한 초과 {fails}회",
                   ok, cause)


# ---------------- P-08 민감도 (한 요인씩) ----------------
def p08():
    rows = []
    base = dict(T=20.0, comp=False, sigma=1.0, p=0.0)
    conds = []
    for T in (0.0, 20.0, 50.0):
        for comp in (False, True):
            conds.append(("①온도·보정", dict(base, T=T, comp=comp)))
    for sg in (0.5, 1.0, 2.0):
        conds.append(("②잡음", dict(base, sigma=sg)))
    for p in (0.0, 0.1, 0.3, 0.5):
        conds.append(("③반사 손실", dict(base, p=p)))
    seen = {}
    for group, c in conds:
        key = (c["T"], c["comp"], c["sigma"], c["p"])
        cid = seen.setdefault(key, f"S{len(seen) + 1:02d}")
        for name, kind, h, truth in (("R1", "occupant", G.R1_cm, OCC), ("empty", "empty", 0.0, UNOCC)):
            dc = replace(D, temp_comp=c["comp"])
            scn = static(f"P08-{cid}-{name}", kind, h, duration=5.0, T_air=c["T"])
            outs, entries, never_valid = [], 0, 0
            for i in range(1, E.n_random + 1):
                tr = run_trial(scn, CFG, seed_for("P-08", f"{cid}-{name}", i), dc, sigma=c["sigma"], p_loss=c["p"])
                if (key, name) not in [(r["key"], r["target"]) for r in rows]:
                    log_trial("P-08", f"{cid}-{name}", i, tr)
                outs.append(ev.output_at(tr["out_log"], E.t_eval_s))
                entries += any(k == "unknown_entry" for _, k, _ in tr["events"])
                f = ev.first_valid_time(tr["out_log"])
                never_valid += f is None or f > E.t_eval_s
            cnt = {k: outs.count(k) for k in (OCC, UNOCC, UNK)}
            d_meas_det = (G.H_s_cm - h) * (D.c_fixed_mps if not c["comp"] else speed_of_sound(c["T"])) / speed_of_sound(c["T"])
            rows.append({"group": group, "cond_id": cid, "key": key, "T_C": c["T"], "temp_comp": c["comp"],
                         "sigma_cm": c["sigma"], "p_loss": c["p"], "target": name, "truth": truth,
                         "OCC": cnt[OCC], "UNOCC": cnt[UNOCC], "UNKNOWN": cnt[UNK],
                         "trials_with_unknown_entry": entries,
                         "trials_no_valid_by_t_eval": never_valid,
                         "delta_noiseless_cm": round(D.d_empty_cm - d_meas_det, 2)})
    # 기록만 함 (합격 판정 없음)
    for r in rows:
        bad = r["UNOCC" if r["truth"] == OCC else "OCC"]
        record("P-08", f"{r['group']} {r['cond_id']} T={r['T_C']:g}°C 보정={'유' if r['temp_comp'] else '무'} "
               f"σ={r['sigma_cm']:g} p_loss={r['p_loss']:g} {r['target']}",
               f"기록(정답 {r['truth']})", f"OCC {r['OCC']}, UNOCC {r['UNOCC']}, UNK {r['UNKNOWN']}; "
               f"UNKNOWN 진입 시행 {r['trials_with_unknown_entry']}/10; t_eval까지 최초 판정 없음 "
               f"{r['trials_no_valid_by_t_eval']}/10; 잡음 없는 Δ {r['delta_noiseless_cm']} cm",
               "기록", ("알고리즘 특성: 초기화·복구가 연속 유효 샘플 k개를 요구하여 손실이 잦으면 UNKNOWN이 유지됨"
                        " (손실 확률 자체는 모델 가정)") if r["UNKNOWN"] else ("모델 가정 민감도" if bad else "-"))
    return rows


def write_csv(path, rows):
    if not rows:
        return
    keys = list(rows[0].keys())
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def main():
    os.makedirs(OUT, exist_ok=True)
    # 결정적 시험부터: P-03(경계·전이) → P-04(초기화) → P-05·P-06(고장·복구) → 무작위·민감도
    p03(); p04(); p05(); p06(); p01(); p02(); p07(); p08_rows = p08()
    with open(os.path.join(OUT, "config.json"), "w", encoding="utf-8") as f:
        json.dump({"config": CFG.to_dict(),
                   "environment": {"python": platform.python_version(), "numpy": np.__version__,
                                   "rng": "numpy.random.PCG64 via SeedSequence(seed).spawn",
                                   "seed_rule": "(base_seed*1000 + crc32(test/case) % 997)*100 + trial"}},
                  f, ensure_ascii=False, indent=2)
    write_csv(os.path.join(OUT, "results.csv"), RESULTS)
    write_csv(os.path.join(OUT, "p08_sensitivity.csv"), [{k: v for k, v in r.items() if k != "key"} for r in p08_rows])
    write_csv(os.path.join(OUT, "trial_samples.csv"), TRIAL_ROWS)
    write_csv(os.path.join(OUT, "output_log.csv"), OUTLOG_ROWS)
    write_csv(os.path.join(OUT, "events.csv"), EVENT_ROWS)
    n_ok = sum(1 for r in RESULTS if r["match"] is True)
    n_ng = sum(1 for r in RESULTS if r["match"] is False)
    print(f"항목 {len(RESULTS)}개: 일치 {n_ok}, 불일치 {n_ng}, 기록 {len(RESULTS) - n_ok - n_ng}")
    for r in RESULTS:
        if r["match"] is False:
            print("불일치:", r["test"], r["case"], "|", r["actual"], "|", r["cause"])


if __name__ == "__main__":
    main()
