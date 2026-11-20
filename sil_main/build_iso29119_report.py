#!/usr/bin/env python3
"""ISO/IEC/IEEE 29119-3 감사 보고서 생성기 (뒷좌석 승객 감지 SIL, 기준선 v1.0).

  python3 build_iso29119_report.py [--date YYYY-MM-DD] [--selftest-result "문구"]

입력(읽기 전용): results_main/ 의 config.json, summary.csv, trace_SR_TC_result.csv,
                 baseline_verification.csv, tc11_side_by_side.csv, coverage_TC11.csv,
                 trials.csv, events.csv, output_log.csv, baseline/baseline_v1.0.json
출력: results_main/ISO29119_Audit_Report.md

시험 결과 파일은 읽기만 하며 수정하지 않는다. 판정 기준·합격선은 이 스크립트에서 바꾸지 않고
기록된 값을 그대로 옮기며, 상한 95 %와 판정은 표준 라이브러리만으로 다시 계산해 기록값과 대조한다.
"""
import collections
import csv
import datetime
import hashlib
import json
import math
import re
import sys
import zlib
from pathlib import Path

# ----------------------------------------------------------------------------------------------
# 경로·상수
# ----------------------------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent                      # sil_main/
RES = ROOT / "results_main"
BASELINE = ROOT / "baseline" / "baseline_v1.0.json"
OUT = RES / "ISO29119_Audit_Report.md"

DOC_ID = "ISO29119-SIL-RSPD-v1.0"
EXPECTED_SHA = "79f21ce910853ee7358d97c031a7553258a9fb2151bdcdaca17db3c1ea205f6d"
EXPECTED_ROWS = 152
EXPECTED_VERIF = 87
# 요청서에 기재된 상태별 행 수(생성 시 실제 집계와 대조)
EXPECTED_STATUS = {
    "목표 충족(통계 확인)": 49, "일치": 27, "기준 충족(전 시행)": 12, "불합격": 3, "미실행": 4,
    "기록(합격 판정 없음)": 44, "가정 기반 민감도 기록": 13,
}
STATUS_ORDER = ["목표 충족(통계 확인)", "관측 충족(통계 미확인)", "기준 충족(전 시행)", "일치",
                "기록(합격 판정 없음)", "가정 기반 민감도 기록", "미실행", "불합격"]
S_OK, S_OBS, S_FAIL = "목표 충족(통계 확인)", "관측 충족(통계 미확인)", "불합격"
EXCLUDED_DIRS = ["results_precheck", "results_p08r0", "results_status_before_baseline"]

TOL = 1e-12


# ----------------------------------------------------------------------------------------------
# 입출력·서식 도우미
# ----------------------------------------------------------------------------------------------
def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def count_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return max(sum(1 for _ in csv.reader(f)) - 1, 0)


def esc(s):
    return str(s).replace("|", "\\|").replace("\r", "").replace("\n", " <br> ")


def table(headers, rows):
    out = ["| " + " | ".join(esc(h) for h in headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(esc(c) for c in r) + " |")
    return "\n".join(out)


def pct(v, empty="—"):
    """0.009936 → 0.994%, 1.0 → 100%, 0.05 → 5%."""
    if v is None or str(v).strip() == "":
        return empty
    try:
        x = float(v) * 100
    except ValueError:
        return str(v)
    s = f"{x:.3f}".rstrip("0").rstrip(".")
    return s + "%"


def blank(v, empty="—"):
    return empty if v is None or str(v).strip() == "" else str(v)


def code(s):
    return f"`{s}`"


# ----------------------------------------------------------------------------------------------
# 정확 이항 단측 95 % 상한 (main_lib/stats.py 와 같은 정의, 독립 재계산용)
# ----------------------------------------------------------------------------------------------
def binom_cdf(k, n, p):
    if p <= 0:
        return 1.0
    if p >= 1:
        return 1.0 if k >= n else 0.0
    lp, lq = math.log(p), math.log1p(-p)
    s = sum(math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * lp + (n - i) * lq)
            for i in range(0, k + 1))
    return min(1.0, s)


def upper_bound(k, n, conf=0.95):
    if k >= n:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if binom_cdf(k, n, mid) > 1 - conf:
            lo = mid
        else:
            hi = mid
    return hi


def judge_rate(k, n, target):
    obs = k / n
    ub = upper_bound(k, n)
    if obs > target + TOL:
        return obs, ub, S_FAIL
    if ub <= target + TOL:
        return obs, ub, S_OK
    return obs, ub, S_OBS


def min_n_zero_error(p, conf=0.95):
    return math.ceil(math.log(1 - conf) / math.log(1 - p) - 1e-12)


def speed_of_sound(T_C):
    """sil/config.py 의 온도 모델 c(T) = 331.4 + 0.6 T (m/s)."""
    return 331.4 + 0.6 * T_C


# ----------------------------------------------------------------------------------------------
# 입력 읽기
# ----------------------------------------------------------------------------------------------
def load():
    d = {}
    d["config_doc"] = read_json(RES / "config.json")
    d["cfg"] = d["config_doc"]["config"]
    d["env"] = d["config_doc"]["environment"]
    d["baseline"] = read_json(BASELINE)
    d["summary"] = read_csv(RES / "summary.csv")
    d["trace"] = read_csv(RES / "trace_SR_TC_result.csv")
    d["verif"] = read_csv(RES / "baseline_verification.csv")
    d["tc11"] = read_csv(RES / "tc11_side_by_side.csv")
    d["cov"] = read_csv(RES / "coverage_TC11.csv")
    d["trials"] = read_csv(RES / "trials.csv")
    return d


# ----------------------------------------------------------------------------------------------
# 무결성 점검 (보고서 3.1절에 그대로 기록)
# ----------------------------------------------------------------------------------------------
def run_checks(d):
    checks = []

    def add(name, ok, detail=""):
        checks.append((name, bool(ok), detail))

    sha_file = sha256(BASELINE)
    sha_copy = sha256(RES / "baseline_v1.0.json") if (RES / "baseline_v1.0.json").exists() else None
    sha_cfg = d["cfg"].get("_baseline_sha256")
    add("기준선 파일 SHA-256이 확정값과 같음", sha_file == EXPECTED_SHA, sha_file)
    add("config.json 의 기록 SHA-256이 기준선 파일과 같음", sha_cfg == sha_file, str(sha_cfg))
    add("results_main/baseline_v1.0.json 사본이 기준선 파일과 바이트 단위로 같음", sha_copy == sha_file,
        "사본 없음" if sha_copy is None else sha_copy)

    ver = d["verif"]
    n_match = sum(1 for r in ver if r["일치"] == "일치")
    add(f"기준선·코드 값 비교 {EXPECTED_VERIF}개 항목 전부 일치", len(ver) == EXPECTED_VERIF and n_match == len(ver),
        f"{n_match}/{len(ver)} 일치")

    summ = d["summary"]
    add(f"summary.csv 결과 행 {EXPECTED_ROWS}개", len(summ) == EXPECTED_ROWS, f"{len(summ)}행")

    cnt = collections.Counter(r["status"] for r in summ)
    mism = {k: (cnt.get(k, 0), v) for k, v in EXPECTED_STATUS.items() if cnt.get(k, 0) != v}
    unknown = [k for k in cnt if k not in STATUS_ORDER]
    add("상태별 행 수가 요청서 기재값과 같음", not mism and not unknown and sum(cnt.values()) == EXPECTED_ROWS,
        "차이 없음" if not mism else f"불일치 {mism}, 미정의 라벨 {unknown}")

    # 비율 행: 상한 95 %와 판정을 독립 재계산
    # 상태가 '가정 기반 민감도 기록'인 비율 행은 목표 열 값이 있어도 합격 판정을 하지 않는 행이므로 수치(관측·상한)만 대조하고,
    # 판정을 하는 행(목표 충족/관측 충족/불합격)은 판정 라벨까지 대조한다.
    bad, n_rate, n_judged, n_sens = [], 0, 0, 0
    for i, r in enumerate(summ, 1):
        if r["kind"] == "rate" and r["target"].strip():
            n_rate += 1
            k, n, tg = int(r["k"]), int(r["n"]), float(r["target"])
            obs, ub, st = judge_rate(k, n, tg)
            bad_num = abs(ub - float(r["upper95"])) > 2e-6 or abs(obs - float(r["observed"])) > 2e-6
            if r["status"] == "가정 기반 민감도 기록":
                n_sens += 1
                bad_st = False
            else:
                n_judged += 1
                bad_st = st != r["status"]
            if bad_num or bad_st:
                bad.append(f"데이터 행 {i}:{r['cond_id']}")
    add(f"목표가 있는 비율 행 {n_rate}개의 관측·상한 95 % 재계산 대조, 판정 행 {n_judged}개의 판정 라벨 대조 "
        f"(판정 없는 민감도 행 {n_sens}개는 수치만)", n_rate > 0 and not bad,
        "전부 일치" if not bad else "불일치 " + ", ".join(bad))

    # trials.csv 로 k, n 다시 세기
    by_cond = collections.defaultdict(list)
    for t in d["trials"]:
        by_cond[(t["tc"], t["cond"])].append(t["result"])
    bad2, n2 = [], 0
    for i, r in enumerate(summ, 1):
        if r["kind"] == "rate":
            conds = [(r["tc"], r["cond_id"]), (r["tc"], r["cond_id"] + "/cargo")]
            res = next((by_cond[c] for c in conds if c in by_cond), None)
            key = "UNKNOWN" if r["metric"] == "미확정률" else "오류"
            n2 += 1
            if res is None or len(res) != int(r["n"]) or sum(1 for x in res if x == key) != int(r["k"]):
                bad2.append(f"데이터 행 {i}:{r['cond_id']}")
    add(f"비율 행 {n2}개의 k·n을 trials.csv 시행 기록에서 다시 센 값과 비교", n2 > 0 and not bad2,
        "전부 일치" if not bad2 else "불일치 " + ", ".join(bad2))

    # 시드 규칙 재계산
    base = int(d["cfg"]["seed"]["base_seed"])
    n_seed = sum(
        1 for t in d["trials"]
        if any(base * 2 ** 64 + zlib.crc32(f"{t['tc']}/{c}".encode()) * 2 ** 20 + int(t["trial"]) == int(t["seed"])
               for c in {t["cond"], t["cond"].split("/")[0]}))
    add("시행별 시드를 CRC32 규칙으로 다시 계산한 값과 비교", n_seed == len(d["trials"]), f"{n_seed}/{len(d['trials'])}행 일치")

    # 추적성 행 수 ↔ summary
    tc_cnt = collections.Counter(r["tc"] for r in summ)
    badt = [f"{r['SR']}/{r['TC']}" for r in d["trace"] if int(r["결과 행 수"]) != tc_cnt.get(r["TC"], -1)]
    add("추적성 표의 TC별 결과 행 수가 summary.csv 와 같음", not badt, "전부 일치" if not badt else "불일치 " + ", ".join(badt))

    # TC-11 나란히 보기 ↔ summary
    sd = {(r["cond_id"], r["metric"]): r for r in summ if r["tc"] == "TC-11"}
    badc = []
    for r in d["tc11"]:
        tgt = {"빈 좌석": "TC-01", "R2(TC-02b 대응)": "TC-02b", "R0(TC-04a 대응)": "TC-04a"}[r["대상"]]
        for comp, tag, kcol in (("nocomp", "a", "보정 없음 k/n"), ("comp", "b", "보정 있음 k/n")):
            row = sd.get((f"11{tag}-T{r['온도(°C)']}-{comp}/{tgt}", r["지표"]))
            if row is None or f"{row['k']}/{row['n']}" != r[kcol]:
                badc.append(f"{r['대상']}/{r['지표']}/{r['온도(°C)']}/{comp}")
    add(f"tc11_side_by_side.csv {len(d['tc11'])}행의 k/n이 summary.csv 와 같음", not badc,
        "전부 일치" if not badc else "불일치 " + ", ".join(badc))
    return checks


# ----------------------------------------------------------------------------------------------
# 이상 보고서(불합격 행에서 생성)
# ----------------------------------------------------------------------------------------------
def tc11_pair(d, target, metric, temp):
    for r in d["tc11"]:
        if r["대상"] == target and r["지표"] == metric and r["온도(°C)"] == str(temp):
            return r
    raise KeyError((target, metric, temp))


def build_incidents(d):
    """summary.csv 의 불합격 행마다 INC 항목을 만든다. 서술은 (TC, 조건) 별로 정해 둔 것만 사용한다."""
    cfg = d["cfg"]
    det = cfg["detector"]
    fails = [(i, r) for i, r in enumerate(d["summary"], 1) if r["status"] == S_FAIL]
    expected_keys = [("TC-04", "04b-1"), ("TC-04", "04b-2"), ("TC-11", "11a-T50-nocomp/TC-04a")]
    got_keys = [(r["tc"], r["cond_id"]) for _, r in fails]
    if got_keys != expected_keys:
        raise SystemExit(f"불합격 행이 예상과 다름: {got_keys} (예상 {expected_keys}) — 이상 보고서 서술을 점검할 것")

    records = {(r["cond_id"], r["metric"]): r for r in d["summary"] if r["tc"] == "TC-04" and r["kind"] == "record"}
    same_hist = records[("04b-1", "기록")]
    no_motion = records[("04b-2", "기록")]
    ok_comp = next(r for r in d["summary"] if r["cond_id"] == "11b-T50-comp/TC-04a" and r["metric"] == "오검출률")
    pair = tc11_pair(d, "R0(TC-04a 대응)", "오검출률", 50)

    # TC-11 50 °C 보정 없음의 R0 환산 거리(잡음 없는 계산, 참고)
    c50 = speed_of_sound(50.0)
    c_fix = det["c_fixed_mps"]
    h_s, r0, d_empty = cfg["geometry"]["H_s_cm"], cfg["geometry"]["R0_cm"], det["d_empty_cm"]
    d_true = h_s - r0
    d_app = d_true * c_fix / c50
    delta_r0 = d_empty - d_app
    delta_empty = d_empty - d_empty * c_fix / c50

    inc = []
    for idx, (row_no, r) in enumerate(fails, 1):
        inc.append({"id": f"INC-{idx:02d}", "row": row_no, "r": r})

    inc[0].update({
        "title": "정지 화물이 점유 대상과 같은 높이(R1 = 20 cm)일 때 100 % 오검출",
        "cond": "TC-04 / 04b-1 — 점유 대상과 같은 정지 거리 이력의 화물(윗면 R1 = 20 cm)",
        "exp": "UNOCCUPIED (화물은 사람이 아님)",
        "analysis": [
            f"센서는 센서 바로 아래 한 점까지의 거리만 측정하는 단일점 거리 센서이고, 판단 프로그램의 입력은 거리 이력뿐임"
            f"(중앙값 필터 M = {det['M']}, 점유 판정 Δ_on = {det['delta_on_cm']:g} cm, 해제 Δ_off = {det['delta_off_cm']:g} cm).",
            f"04b-1은 화물 윗면을 점유 대상(R1)과 같은 높이에 두고 **같은 시드 = 같은 거리 이력**을 사용하므로 두 경우의 입력이 같음. "
            f"기록 행: 기대 \"{same_hist['expected']}\", 실제 \"{same_hist['actual']}\" (비고: {same_hist['note']}).",
            "입력이 같으면 출력도 같을 수밖에 없으므로 화물을 점유와 구분하는 것은 이 센서 구성·알고리즘의 **구조적(architectural) 한계**이며, "
            "구현 오류(software bug)가 아님. 따라서 코드 수정이 아니라 한계로 기록함.",
        ],
        "policy": "D6: 오검출 목표(≤ 5 %)를 같은 거리의 가방 조건에도 유지함. 임계값·목표를 사후에 바꾸지 않고 불합격을 그대로 기록함"
                  "(시험 설계 11.2절 — '목표를 바꾸지 않으면 불합격도 그대로 기록').",
        "followup": "시스템 수준에서 단일점 거리 센서만으로 화물·인체를 구분할 수 없음을 한계로 인정할지, 추가 센서·특징량을 도입할지 검토. "
                    "SIL 한계(7단계)로 보고. GitHub Issue 로 추적.",
    })
    inc[1].update({
        "title": "정지 화물(R1) 대 움직이는 점유 대상(±1.0 cm, 0.25 Hz) 조건에서 100 % 오검출",
        "cond": "TC-04 / 04b-2 — 화물 정지(윗면 R1 = 20 cm) / 점유 대상 움직임(±1.0 cm, 0.25 Hz 가정)",
        "exp": "UNOCCUPIED (화물은 사람이 아님)",
        "analysis": [
            "점유 대상에만 미세 움직임을 주어 시간 변동으로 구분 가능한지 보는 조건임. "
            f"기록 행: 기대 \"{no_motion['expected']}\", 실제 \"{no_motion['actual']}\" (비고: {no_motion['note']}).",
            "정지 화물의 평균 높이가 R1과 같아 거리 수준만 보는 현재 알고리즘은 화물을 OCCUPIED 로 판정함. "
            "움직임(시간 변동)은 판단에 사용되지 않으므로 움직임 유무가 출력에 영향을 주지 않음.",
            "움직임 진폭·주파수(1.0 cm, 0.25 Hz)는 예비시험 P-02 값을 승계한 근거 없는 가정이며(D7), 이 가정이 실제 인체 거동을 대표한다는 주장이 아님.",
        ],
        "policy": "D6(목표 유지)·D7(움직임 가정 승계): 합격선을 사후에 완화하지 않고 불합격을 그대로 기록함.",
        "followup": "INC-01 과 같은 근본 원인. 시간 변동 특징을 쓰는 알고리즘 변경은 기준선 버전을 올리고 변경 전후를 기록해야 함(run_main.py 지침). "
                    "GitHub Issue 로 INC-01 과 함께 추적.",
    })
    inc[2].update({
        "title": "50 °C·보정 없음에서 낮은 화물 R0(5 cm) 100 % 오검출 — 음속 변화에 의한 ToF 단축",
        "cond": "TC-11 / 11a-T50-nocomp/TC-04a — 낮은 화물 R0(5 cm), T = 50 °C, 온도 보정 없음 (SR-09)",
        "exp": "UNOCCUPIED (R0 낮은 화물은 점유 아님)",
        "analysis": [
            f"음속은 c(T) = 331.4 + 0.6·T (m/s)이므로 50 °C에서 {c50:.1f} m/s, 보정 없는 거리 환산은 고정 음속 {c_fix:g} m/s를 사용함. "
            f"실제 ToF가 짧아져 환산 거리가 d × {c_fix:g}/{c50:.1f} = {c_fix / c50:.4f} 배로 짧게 계산됨.",
            f"R0 윗면까지 실제 거리 {d_true:g} cm → 환산 {d_app:.2f} cm, d_empty = {d_empty:g} cm 대비 Δ ≈ {delta_r0:.2f} cm ≥ Δ_on = {det['delta_on_cm']:g} cm → OCCUPIED. "
            f"(잡음 없는 단순 계산; 빈 좌석은 Δ ≈ {delta_empty:.2f} cm로 임계값 미만이어서 TC-01 은 영향 없음. "
            f"추가 시험 P-08-R0 의 잡음 없는 계산값 10.63 cm(`main_lib/decisions.py` D3 근거)와 같은 값임.)",
            f"같은 조건에서 보정을 켜면(11b-T50-comp/TC-04a) 오류 {ok_comp['k']}/{ok_comp['n']}, 단측 95 % 상한 {pct(ok_comp['upper95'])} ≤ 목표 {pct(ok_comp['target'])} → {ok_comp['status']}. "
            f"보정 없음은 {pair['보정 없음 k/n']}(상한 {pct(pair['보정 없음 상한95'])}, {pair['보정 없음 판정']}), 보정 있음은 {pair['보정 있음 k/n']}(상한 {pct(pair['보정 있음 상한95'])}, {pair['보정 있음 판정']}). "
            f"(온도 입력 오차 U(−{cfg['environment']['temp_input_err_C']:g}, +{cfg['environment']['temp_input_err_C']:g}) °C는 가정.)",
        ],
        "policy": "D3: 50 °C R0 오검출도 그대로 기록함. 보정 채택 여부는 본시험 이후 결정하며, 이 결과만으로 SR-09 전체 충족을 선언하지 않음.",
        "followup": "온도 보정의 요구사항 채택은 2026-11-13 김*수 결정으로 v1.1 기본 구성에 채택됨(Notion TP-01 PR-2 참조; 다른 팀원의 동의는 김*수가 전달한 기록이며 원본 미첨부). v1.0 기준선과 결과는 바뀌지 않으며, v1.1에서 보정을 반영해 다시 확인하기 전까지 SR-09 전체 충족 선언 보류. GitHub Issue 로 추적.",
    })
    return inc


# ----------------------------------------------------------------------------------------------
# 보고서 본문
# ----------------------------------------------------------------------------------------------
def build_report(d, checks, inc, report_date, selftest_result):
    cfg, env, summ = d["cfg"], d["env"], d["summary"]
    L = []
    w = L.append
    sha_file = sha256(BASELINE)
    cnt = collections.Counter(r["status"] for r in summ)
    kind_cnt = collections.Counter(r["kind"] for r in summ)
    by_tc_raw = {}
    for i, r in enumerate(summ, 1):
        by_tc_raw.setdefault(r["tc"], []).append((i, r))
    by_tc = collections.OrderedDict(sorted(by_tc_raw.items()))
    all_ok = all(ok for _, ok, _ in checks)

    # ------------------------------------------------------------------ 제목·Document Control
    w("# 뒷좌석 승객 감지 SIL 검증 — ISO/IEC/IEEE 29119-3 감사 보고서")
    w("")
    w("> 이 문서는 `sil_main/build_iso29119_report.py`가 `sil_main/results_main/`의 기록 파일을 읽어 자동 생성한다. "
      "시험 결과·합격 기준은 바꾸지 않고 옮겨 적었으며, 직접 고치지 말고 스크립트로 다시 생성할 것.")
    w("")
    w("## Document Control Block (문서 관리 정보)")
    w("")
    dec = dict(cfg["decided"])
    # 기준선 파일(baseline_v1.0.json)은 SHA-256으로 고정되어 있어 고칠 수 없으므로, 보고서에 옮길 때만 이름 가운데 글자를 가린다.
    dec["by"] = re.sub(r"\(([가-힣])([가-힣]+)([가-힣])\)", lambda m: "(" + m.group(1) + "*" * len(m.group(2)) + m.group(3) + ")", dec["by"])
    w(table(["항목", "내용"], [
        ["Document ID", code(DOC_ID)],
        ["문서명", "뒷좌석 승객 감지(Rear-Seat Occupant Detection) SIL 본시험 — Test Documentation (Test Plan · Test Design/Procedure · Test Execution Log/Incident Report · Test Completion Report)"],
        ["적용 표준", "ISO/IEC/IEEE 29119-3 (Test Documentation) 문서 구성을 적용함. **표준 적합성(conformance)은 아직 주장하지 않음** — 선언·outcome 체크리스트·점검표는 팀 검토·합의 전이다."],
        ["29119 적합성 문서", "`docs/29119/` — `00_conformance_declaration.md`(29119-2 프로세스 선언), `02_conformance_declaration_29119-3.md`(문서 선언), `01_outcome_checklist.md`(41개 outcome), `03_29119-3_conformance_check.md`(Annex A 점검표), 산출물 TP-01~IR-03"],
        ["시험 수준", "SIL (Software-in-the-Loop), 시험 케이스 TC-01 ~ TC-16"],
        ["기준선 파일", code("sil_main/baseline/baseline_v1.0.json") + f" (version {cfg['version']}, confirmed = {str(cfg['confirmed']).lower()})"],
        ["기준선 SHA-256", code(sha_file)],
        ["SHA-256 대조", "확정값 `" + EXPECTED_SHA + "` 와 " + ("일치" if sha_file == EXPECTED_SHA else "**불일치**")
         + "; `results_main/config.json`·`results_main/baseline_v1.0.json` 사본과도 대조함(3.1절)"],
        ["확정일 / 승인자", f"{dec['date']} / {dec['by']} (결정 D1~D8, 1.5절)"],
        ["실행 환경 (config.json 기록)", f"Python {env['python']}, NumPy {env['numpy']}"],
        ["난수 생성기 (RNG)", env["rng"]],
        ["시드 규칙", f"{code(env['seed_rule'])}, base_seed = {cfg['seed']['base_seed']}"],
        ["명령", code(cfg["_command"])],
        ["본 보고서 생성일", report_date],
        ["생성 스크립트", code("sil_main/build_iso29119_report.py") + " (표준 라이브러리만 사용)"],
        ["집계에서 제외한 결과 폴더",
         "`results_precheck/`(기준선 확정 전 사전점검, 판정 아님), `results_p08r0/`(추가 시험 P-08-R0, 판정 없음), "
         "`results_status_before_baseline/`(기준선 확정 전 상태 기록, 모든 TC 미실행·보존용) — **이 보고서의 어떤 수치에도 포함하지 않음**"],
        ["불변 규칙", "`sil_prelim/` 및 `sil_main/results_*` 결과 파일은 수정하지 않음. 본시험을 다시 실행하거나 합격선·목표를 바꾸지 않음."],
    ]))
    w("")

    # ------------------------------------------------------------------ Chapter 1
    w("## Chapter 1. Test Plan (테스트 계획서)")
    w("")
    w("### 1.1 Scope (시험 범위)")
    w("")
    w(f"- 대상 시험 케이스: **TC-01 ~ TC-16**. 본시험 결과 표(`summary.csv`)는 조건·검사 단위로 **{len(summ)}행**이며, 행 종류는 "
      + ", ".join(f"{k} {v}" for k, v in sorted(kind_cnt.items())) + "개임.")
    w("- 시험 대상(Test Item): 점유 판단 소프트웨어(`sil/detector.py`)와 센서 모델(`sil/sensor_model.py`)을 포함한 SIL 패키지. 사용 설정값은 아래 표.")
    w("- 판정 단위: 조건(cond_id)×검사 지표(metric). 같은 조건에서 미검출·오검출·미확정 등 지표별로 한 행씩 기록함.")
    w("")
    w(table(["TC", "결과 행 수", "관련 SR(행 기준)"],
            [[tc, len(rs), ", ".join(sorted({r["sr"] for _, r in rs}))] for tc, rs in by_tc.items()]))
    w("")
    det, sen, ev, env_c = cfg["detector"], cfg["sensor"], cfg["evaluation"], cfg["environment"]
    w("**시험 대상 설정값 (기준선 v1.0)**")
    w("")
    w(table(["구분", "항목", "값"], [
        ["기하", "H_s (센서 높이)", f"{cfg['geometry']['H_s_cm']:g} cm"],
        ["기하", "빈 좌석 / R0 / R1 / R2 / R3 높이", f"{cfg['geometry']['empty_seat_h_cm']:g} / {cfg['geometry']['R0_cm']:g} / {cfg['geometry']['R1_cm']:g} / {cfg['geometry']['R2_cm']:g} / {cfg['geometry']['R3_cm']:g} cm (가상 반사면, D1)"],
        ["판단", "d_empty (빈 좌석 기준 거리)", f"{det['d_empty_cm']:g} cm 고정 (D4)"],
        ["판단", "Δ_on / Δ_off", f"{det['delta_on_cm']:g} cm / {det['delta_off_cm']:g} cm"],
        ["판단", "k (필터 길이) / M", f"{det['k']} / {det['M']}"],
        ["판단", "T_stale / T_db", f"{det['T_stale_s']:g} s / {det['T_db_s']:g} s (db_basis = {det['db_basis']}, D2)"],
        ["판단", "유효 범위 / 고정 음속", f"{det['valid_min_cm']:g}–{det['valid_max_cm']:g} cm / {det['c_fixed_mps']:g} m/s"],
        ["센서", "주기 / T_to", f"{sen['period_s']:g} s / {sen['T_to_s']:g} s"],
        ["센서", "σ / 손실률 / 편향 (기준 수준)", f"{sen['sigma_cm']:g} cm / {sen['p_loss']:g} / {sen['bias_cm']:g} cm"],
        ["환경", "기준 온도 / 보정 / 온도 입력 오차", f"{env_c['T_base_C']:g} °C / {'있음' if env_c['temp_comp_base'] else '없음'} / U(−{env_c['temp_input_err_C']:g}, +{env_c['temp_input_err_C']:g}) °C (가정)"],
        ["평가", "t_eval / T_first / T_recover / 응답 한도", f"{ev['t_eval_s']:g} s / {ev['T_first_s']:g} s / {ev['T_recover_s']:g} s / {ev['response_limit_s']:g} s"],
        ["평가", "사건 위상", ev["event_phase"]],
    ]))
    w("")
    w("### 1.2 Test Items and Repetitions (시행 횟수)")
    w("")
    reps = cfg["repetitions"]
    w(table(["항목", "시행 수"], [[k, v] for k, v in reps.items() if not k.startswith("_")]))
    w("")
    w(f"> 기준선 기록: {reps['_state']}")
    w("")

    w("### 1.3 Exclusions and Model Limitations (제외 범위와 모델 한계)")
    w("")
    w("1. **가상 반사면 대체 (D1)**: O-A/O-B/O-C의 반사면 높이 근거가 없어(시험 설계 4.3·12절 TBR) 프로젝트 가정 반사면 "
      f"`R0~R3 = {cfg['geometry']['R0_cm']:g}/{cfg['geometry']['R1_cm']:g}/{cfg['geometry']['R2_cm']:g}/{cfg['geometry']['R3_cm']:g} cm`로 대체함. "
      "TC-02a=R1, TC-02b=R2, TC-03=R3 는 **'가상 반사면 대체 조건'**이며 실제 더미·인체·가방의 치수가 아니고 O-A/O-B/O-C 원 조건의 결과가 아님(결과 표 `surface` 열에 표시).")
    w("2. **미실행**: O-A·O-B·O-C 원 조건, **TC-12(O-S)** 는 입력(치수) 부재로 실행하지 않음(4.2절).")
    w("3. **단일점 높이 센서 한계**: 센서 바로 아래 **한 점의 높이만** 모델링함. 착석 위치 분포(off-axis)는 모델에 없음"
      f"(기준선 `seating_position_distribution`: \"{cfg['seating_position_distribution']}\"). "
      "같은 거리 이력을 갖는 화물과 사람은 거리 입력만으로 구분할 수 없음(INC-01·INC-02).")
    w("4. **d_empty 고정 (D4)**: 100 cm 고정이며 초기 빈 좌석 실측 보정은 모델에 없음.")
    w("5. **전원·시동 (D8)**: TC-08은 t = 0 전원 인가 SIL 모델이며 차량 시동과 센서 전원의 관계는 모델에 없음.")
    w("6. **온도 보정 (D3)**: 보정의 요구사항 채택은 본시험 이후 결정으로 기준선에 기록함(2026-11-11). 이후 2026-11-13 김*수 결정(Notion TP-01 PR-2 참조)으로 v1.1 기본 구성에 채택함. 이 결정은 v1.0 기준선·결과를 바꾸지 않음. TC-11은 빈 좌석·R2·R0, 0·20·50 °C, 보정 유·무만 다루며 SR-09 전체 충족 선언은 하지 않음(4.3절).")
    w("7. **가정 의존 값**: 온도 입력 오차 ±2 °C, TC-04b-2 움직임(1.0 cm, 0.25 Hz, D7), 05a·05b 동일 입력 모델(D7)은 근거 없는 가정이며 별도 검증으로 집계하지 않음.")
    w("8. SIL 결과는 사용한 **모델과 입력 분포에 대한 결과**이며 실제 센서 성능을 입증하지 않음.")
    w("")

    w("### 1.4 Pass/Fail Criteria (통계적 합격·불합격 기준)")
    w("")
    tg = cfg["targets"]
    w(table(["지표", "목표(D6)"], [
        ["미검출률 (miss rate)", f"≤ {pct(tg['miss_rate'])}"], ["오검출률 (false alarm rate)", f"≤ {pct(tg['false_alarm_rate'])}"],
        ["미확정률 (UNKNOWN rate)", f"≤ {pct(tg['unknown_rate'])}"], ["응답 시간", f"≤ {tg['response_s']:g} s 및 정답 유지"],
        ["출력 뒤집힘(flip)", f"{tg['flips']}회"]]))
    w("")
    w("**판정 방법**: 오류율은 독립 시행 수 기준이며 UNKNOWN은 분모에 포함하고 미확정률로 따로 계산함. 신뢰수준 95 %의 **단측 정확 이항 상한(Clopper-Pearson)** "
      "p_U 는 `P(X ≤ k | n, p_U) = 0.05` 의 해이며, k = 0 이면 `(1 − p_U)^n = 0.05` 임(시험 설계 9.4절, D5/D6).")
    w("")
    w("```")
    w("관측 비율 k/n > 목표                → 불합격")
    w("관측 비율 ≤ 목표 이고 상한95 ≤ 목표  → 목표 충족(통계 확인)")
    w("관측 비율 ≤ 목표 이고 상한95 > 목표  → 관측 충족(통계 미확인)")
    w("```")
    w("")
    w(f"오류 0건으로 상한 95 %가 목표 이하가 되는 최소 시행 수: 목표 1 % → **{min_n_zero_error(0.01)}회**, 목표 5 % → **{min_n_zero_error(0.05)}회**.")
    w("")
    w("**상한 95 % 계산표 (이 스크립트가 독립 계산)**")
    w("")
    rows = []
    for k in range(0, 5):
        rows.append([k] + [pct(upper_bound(k, n)) for n in (300, 60)])
    w(table(["오류 k", "n = 300 상한95", "n = 60 상한95"], rows))
    w("")
    w("**n = 60 일 때 판정이 갈리는 조건 (`관측 충족(통계 미확인)`의 조건부 인정 기준)**")
    w("")
    rows = []
    for tname, t in (("오검출률(목표 5 %)", 0.05), ("미검출률·미확정률(목표 1 %)", 0.01)):
        for n in (60, 300):
            seg = collections.OrderedDict()
            for k in range(0, n + 1):
                st = judge_rate(k, n, t)[2]
                seg.setdefault(st, []).append(k)
                if k > 8 and st == S_FAIL:
                    break
            desc = []
            for st, ks in seg.items():
                if st == S_FAIL:
                    desc.append(f"{st}: k ≥ {ks[0]}")
                else:
                    desc.append(f"{st}: k = {ks[0]}" + (f"~{ks[-1]}" if len(ks) > 1 else ""))
            rows.append([tname, n, "; ".join(desc)])
    w(table(["목표", "n", "k 에 따른 판정"], rows))
    w("")
    w("> `n = 60` 에서 오검출 목표 5 %는 k = 0 이면 상한 95 %가 4.87 % 로 목표 이하라 *통계 확인*, k = 1~3 이면 관측 비율은 목표 이하이나 상한이 목표를 넘어 "
      "*관측 충족(통계 미확인)*, k ≥ 4 이면 *불합격*임. 목표 1 %는 n = 60 에서 k = 0 이어도 상한이 4.87 % 라 *통계 미확인*에 그침(최소 299회 필요). "
      f"**이 보고서의 {EXPECTED_ROWS}개 결과 중 `관측 충족(통계 미확인)` 행은 {cnt.get('관측 충족(통계 미확인)', 0)}개**임.")
    w("")
    w("**상태 라벨 정의**")
    w("")
    defs = {
        "목표 충족(통계 확인)": "비율 조건. 관측 비율 ≤ 목표 이고 단측 95 % 정확 이항 상한 ≤ 목표.",
        "관측 충족(통계 미확인)": "비율 조건. 관측 비율 ≤ 목표이나 상한이 목표를 넘음(시행 수 부족). 합격이 아니라 **조건부 인정**이며 시행 수를 늘려야 통계 확인 가능. n = 60 의 판정 구간은 위 표.",
        "기준 충족(전 시행)": "모든 시행이 기준을 만족해야 하는 조건(응답 시간, 뒤집힘, 최초 판정, 복구). 미충족 시행 수와 단측 95 % 상한을 함께 기록.",
        "일치": "결정적 시험의 기대 출력과 실제 출력이 같음(`불일치`는 실패로 기록).",
        "기록(합격 판정 없음)": "참고 시험·보조 기록. 합격·불합격을 판정하지 않음.",
        "가정 기반 민감도 기록": "가정한 민감도 수준(σ, 손실률, 편향, 기울임 등)에서의 결과 기록. 합격 판정 없음. 비율 행은 `목표` 열 값이 있어도 판정하지 않으며(관측·상한 수치만 기록), 예: TC-05 손실률·편향 수준.",
        "미실행": "기준선 입력이 없는 항목. 사유를 함께 기록. 합격 판정 대상이 아님.",
        "불합격": "비율 조건에서 관측 비율 > 목표, 또는 전 시행 조건에서 미충족 시행이 있음. 목표를 바꾸지 않고 그대로 기록(D6).",
    }
    w(table(["상태 라벨", "정의", "본 보고서 행 수"], [[s, defs[s], cnt.get(s, 0)] for s in STATUS_ORDER]))
    w("")

    w("### 1.5 Baseline Decisions D1–D8 (기준선 결정 항목)")
    w("")
    w(f"확정일 {dec['date']}, 확정자 {dec['by']}. 원문 요지는 `baseline_v1.0.json` 의 `decisions` 를 그대로 옮김.")
    w("")
    w(table(["ID", "결정 내용"], [[k, v] for k, v in cfg["decisions"].items()]))
    w("")

    # ------------------------------------------------------------------ Chapter 2
    w("## Chapter 2. Test Design, Procedure & Traceability (테스트 설계·절차 및 요구사항 추적성 명세)")
    w("")
    w("### 2.1 Test Procedure (검증 절차)")
    w("")
    w("모든 명령은 `sil_main/` 폴더에서 실행하며 `../sil_prelim/` 이 옆에 있어야 한다(Python 3.10+, numpy).")
    w("")
    groups = collections.Counter(r["항목"].split(".")[0] if "." in r["항목"][:30] else "기타" for r in d["verif"])
    w(table(["단계", "명령 / 활동", "산출물", "성격"], [
        ["1", code("python3 run_main.py status"), "`results_status_before_baseline/`", "기준선 확정 전 상태 기록(모든 TC 미실행). 판정 아님"],
        ["2", code("python3 run_main.py precheck") + " / " + code("python3 run_main.py additional"),
         "`results_precheck/`(T_db 비교 등), `results_p08r0/`(P-08-R0)", "사전점검·추가 시험. **판정 아님, 본시험 집계 제외**"],
        ["3", code("python3 selftest.py"), "콘솔 출력", "통계 수치(9.4절), 예비시험 5개 파일 바이트 재현, 사전점검·본시험 2회 실행 동일성, 집계 재계산, 기준선 SHA-256·87항목 확인(복사본에서 실행, `results_main/` 불변)"],
        ["4", "기준선 확정(D1~D8)", "`baseline/baseline_v1.0.json`", f"{dec['date']} {dec['by']} 확정. SHA-256 `{sha_file[:16]}…`"],
        ["5", "실행 시작 시 기준선·코드 값 비교", "`results_main/baseline_verification.csv`", f"{len(d['verif'])}개 항목 비교, 하나라도 다르면 실행 중단. 결과: {sum(1 for r in d['verif'] if r['일치'] == '일치')}/{len(d['verif'])} 일치"],
        ["6", code(cfg["_command"]), "`results_main/` (`summary.csv`, `trials.csv`, `trial_samples.csv.gz`, `output_log.csv`, `events.csv` 등)",
         "본시험. 실행 순서: 결정적 시험(TC-07, 13, 14, 15, 08) → 무작위 시험(TC-01~06, 07c, 09, 10, 11, 12) → TC-16(로그 간격은 앞선 로그 사용)"],
        ["7", "집계·추적성", "`summary.csv`, `trace_SR_TC_result.csv`, `tc11_side_by_side.csv`, `coverage_TC11.csv`, `report.md`", "결과를 본 뒤 반복 횟수·합격 기준을 바꾸지 않음"],
        ["8", code("python3 build_iso29119_report.py"), "`results_main/ISO29119_Audit_Report.md`", "본 문서 생성(읽기 전용 입력)"],
    ]))
    w("")
    w("> 설정·구현을 바꿔야 하면 변경 사유와 전후를 기록하고 baseline 버전을 올린다(`sil_main/README.md`).")
    w("")
    w("**기준선·코드 값 비교 항목 87개의 구성**")
    w("")
    w(table(["항목 그룹(점 앞 접두)", "개수"], [[k, v] for k, v in groups.items()]))
    w("")
    w("전체 항목 표는 Appendix B.")
    w("")
    w("### 2.2 Deterministic Seed Rule (결정적 시드 규칙)")
    w("")
    w("```")
    w("seed = base_seed * 2**64 + crc32('<접두>/<TC>/<조건>') * 2**20 + 시행 번호")
    w(f"base_seed = {cfg['seed']['base_seed']}   (본시험 접두 없음, 사전점검 접두 'PRE/')")
    w("```")
    w("")
    w("- 조건마다 독립이며 시행 수 제한은 2**20 임(예비시험 규칙은 시행 100회 이상에서 이웃 조건과 겹칠 수 있어 바꿈).")
    w(f"- 난수 생성기: {env['rng']}. 잡음·손실 난수는 서로 독립임.")
    ex = d["trials"][0]
    ex_seed = int(cfg["seed"]["base_seed"]) * 2 ** 64 + zlib.crc32(f"{ex['tc']}/{ex['cond'].split('/')[0]}".encode()) * 2 ** 20 + int(ex["trial"])
    w(f"- 재계산 예: `{ex['tc']}/{ex['cond'].split('/')[0]}` 시행 {ex['trial']} → crc32 = {zlib.crc32((ex['tc'] + '/' + ex['cond'].split('/')[0]).encode())}, "
      f"seed = {ex_seed} ({'`trials.csv` 기록과 일치' if ex_seed == int(ex['seed']) else '**불일치**'}). 전 시행 재계산 결과는 3.1절.")
    w("")
    w("### 2.3 Requirements Traceability Matrix (요구사항 추적성 행렬)")
    w("")
    w("`trace_SR_TC_result.csv` 전체. 검증 방법 약어: T = Test(시험), A = Analysis(분석), I = Inspection(검사). 행 수는 TC 단위 집계이므로 한 TC가 여러 SR에 연결되면 SR 간에 같은 행이 중복 집계됨.")
    w("")
    w(table(["SR", "검증", "예비시험", "TC", "결과 행 수", "상태 집계"],
            [[r["SR"], r["검증"], r["예비시험"], r["TC"], r["결과 행 수"], r["상태 집계"]] for r in d["trace"]]))
    w("")
    sr_map = collections.OrderedDict()
    for r in d["trace"]:
        sr_map.setdefault(r["SR"], []).append(r)
    rows = []
    for sr, rs in sr_map.items():
        labs = set()
        for r in rs:
            for part in r["상태 집계"].split(";"):
                labs.add(part.strip().rpartition(" ")[0])
        flags = []
        if S_FAIL in labs:
            flags.append("불합격 포함")
        if "미실행" in labs:
            flags.append("미실행 포함")
        if sr == "SR-09":
            flags.append("부분 커버(전체 충족 선언 보류, D3)")
        rows.append([sr, ", ".join(r["TC"] for r in rs), "; ".join(flags) if flags else "—"])
    w("**SR별 요약 (표시 사항만)**")
    w("")
    w(table(["SR", "연결 TC", "주의 표시"], rows))
    w("")

    # ------------------------------------------------------------------ Chapter 3
    w("## Chapter 3. Test Execution Log & Incident Report (테스트 실행 로그 및 이상 보고서)")
    w("")
    w("### 3.1 Integrity Check Summary (무결성 점검 요약)")
    w("")
    n_ver = sum(1 for r in d["verif"] if r["일치"] == "일치")
    w(f"- 실행 전 기준선↔코드 값 비교: **{n_ver}/{len(d['verif'])}개 항목 일치**(`baseline_verification.csv`).")
    w(f"- 이 보고서 생성 시 수행한 점검: {'전부 통과' if all_ok else '**실패 항목 있음**'}.")
    w("")
    w(table(["점검", "결과", "세부"], [[n, "통과" if ok else "**실패**", det_] for n, ok, det_ in checks]))
    w("")
    w(f"- `selftest.py` 실행 기록: {selftest_result if selftest_result else '이 보고서에 기록하지 않음(스크립트 옵션 `--selftest-result` 미지정). CI(`.github/workflows/verify.yml`) 또는 로컬 실행으로 확인'}.")
    w("")
    w("### 3.2 Test Execution Log — Raw Log Manifest (원시 로그 목록)")
    w("")
    tr_cnt = collections.Counter(t["tc"] for t in d["trials"])
    mani = []
    for f, desc in (("trials.csv", "시행별 정답·출력·결과, 첫 유효 판정 시각, 사건 시각, 응답 시간, 요청·수신 시각, 뒤집힘, 복구 시간, 시드"),
                    ("output_log.csv", "출력이 바뀐 시각 기록"),
                    ("events.csv", "UNKNOWN 진입·복구 등 사건 기록")):
        mani.append([f, desc, count_rows(RES / f), sha256(RES / f), "Git 추적"])
    mani.append(["trial_samples.csv.gz", "측정 로그: 측정 요청·수신 시각, 상태·원인, 참 거리, 잡음, 펄스 폭, 환산 거리, 중앙값, Δ, 출력, 정답, 시드",
                 "— (압축 해제 약 100 MB 규모)", "— (gzip 헤더 시각이 실행마다 달라 해시를 기록하지 않음; 압축 해제 내용 기준으로 재현성 확인)",
                 "**Git 미추적(`.gitignore`의 `*.csv.gz`)** — 로컬 보존 필요, `run_main.py main` 으로 재생성 가능"])
    for f, desc in (("summary.csv", "조건·검사 단위 결과표(152행)"), ("trace_SR_TC_result.csv", "SR→TC→결과 상태 집계"),
                    ("baseline_verification.csv", "기준선·코드 값 비교(87개 항목)"), ("tc11_side_by_side.csv", "TC-11 온도·보정 구성별 나란히 보기"),
                    ("coverage_TC11.csv", "TC-11이 실제로 다룬 조건"), ("config.json", "사용한 설정, Python·numpy 버전, RNG, 시드 규칙"),
                    ("report.md", "시험별 결과표 읽기용 사본"), ("baseline_v1.0.json", "실행에 쓴 기준선 사본")):
        p = RES / f
        mani.append([f, desc, count_rows(p) if f.endswith(".csv") else "—", sha256(p), "Git 추적"])
    w(table(["파일 (`results_main/`)", "내용", "데이터 행 수", "SHA-256", "형상 관리"], mani))
    w("")
    w("**시행 기록 수 (trials.csv)**")
    w("")
    w(table(["TC", "시행 행 수"], [[tc, n] for tc, n in sorted(tr_cnt.items())] + [["합계", sum(tr_cnt.values())]]))
    w("")

    w("### 3.3 Test Incident Report (이상 보고서)")
    w("")
    w(f"`summary.csv` 에서 상태가 `불합격`인 **{len(inc)}개 행**을 분리해 기록한다. 세 건 모두 **합격선·목표·임계값을 사후에 바꾸지 않고** 그대로 기록했으며(D6), "
      "시행 수·시드·입력은 기준선 v1.0 그대로임. 상태는 모두 *Open*(후속 검토 필요)이다.")
    w("")
    w(table(["ID", "TC / 조건", "SR", "지표", "k / n", "관측", "상한95", "목표", "상태", "summary.csv 데이터 행"],
            [[i["id"], f"{i['r']['tc']} / {i['r']['cond_id']}", i["r"]["sr"], i["r"]["metric"], f"{i['r']['k']}/{i['r']['n']}",
              pct(i["r"]["observed"]), pct(i["r"]["upper95"]), f"≤ {pct(i['r']['target'])}", i["r"]["status"], i["row"]] for i in inc]))
    w("")
    for i in inc:
        r = i["r"]
        w(f"#### {i['id']} — {i['title']}")
        w("")
        w(table(["항목", "내용"], [
            ["Incident ID", i["id"]],
            ["시험 항목 / 조건", i["cond"]],
            ["관련 SR", r["sr"]],
            ["반사면 표시", blank(r["surface"])],
            ["기대 결과", i["exp"]],
            ["실제 결과", f"{r['actual']} → **오류 {r['k']}/{r['n']} = {pct(r['observed'])}** (단측 95 % 상한 {pct(r['upper95'])}, 목표 ≤ {pct(r['target'])})"],
            ["판정", r["status"]],
            ["원시 기록", f"`trials.csv` (tc = {r['tc']}, cond = {('04b-' + r['cond_id'][-1] + '/cargo') if r['tc'] == 'TC-04' else r['cond_id']}), `summary.csv` 데이터 행 {i['row']}"],
            ["기준선 정책", i["policy"]],
            ["상태", "Open — 후속 조치 필요"],
            ["후속 조치", i["followup"]],
        ]))
        w("")
        w("**원인 분석**")
        w("")
        for a in i["analysis"]:
            w(f"- {a}")
        w("")

    # ------------------------------------------------------------------ Chapter 4
    w("## Chapter 4. Test Completion Report (테스트 완료 보고서)")
    w("")
    w("### 4.1 Overall Status Distribution (전체 상태 분포)")
    w("")
    w(table(["상태", "행 수", "비율"], [[s, cnt.get(s, 0), f"{cnt.get(s, 0) / len(summ) * 100:.1f}%"] for s in STATUS_ORDER]
            + [["합계", sum(cnt.values()), "100.0%"]]))
    w("")
    kinds = sorted(kind_cnt)
    km = collections.defaultdict(collections.Counter)
    for r in summ:
        km[r["status"]][r["kind"]] += 1
    w("**상태 × 행 종류**")
    w("")
    w(table(["상태"] + kinds, [[s] + [km[s].get(k, 0) or "" for k in kinds] for s in STATUS_ORDER if cnt.get(s, 0)]))
    w("")
    tcs = list(by_tc)
    stc = collections.defaultdict(collections.Counter)
    for r in summ:
        stc[r["tc"]][r["status"]] += 1
    used = [s for s in STATUS_ORDER if cnt.get(s, 0)]
    w("**TC × 상태**")
    w("")
    w(table(["TC"] + used + ["합계"], [[tc] + [stc[tc].get(s, 0) or "" for s in used] + [len(by_tc[tc])] for tc in tcs]))
    w("")

    w("### 4.2 Not-Run Items (미실행 항목)")
    w("")
    nr = [(i, r) for i, r in enumerate(summ, 1) if r["status"] == "미실행"]
    w(table(["summary.csv 데이터 행", "TC", "조건", "SR", "사유(비고 원문)"],
            [[i, r["tc"], r["condition"], r["sr"], r["note"]] for i, r in nr]))
    w("")
    w("O-A·O-B·O-C 원 조건은 가상 반사면 대체 조건(TC-02a=R1, TC-02b=R2, TC-03=R3)의 결과로 갈음하지 않으며, "
      "미실행 4개 항목은 합격 판정 대상이 아님(D1).")
    w("")

    w("### 4.3 SR-09 Coverage Reservation (SR-09 전체 충족 선언 보류, D3)")
    w("")
    w("**SR-09 전체 충족(0–50 °C에서 SR-01~04·14 충족) 선언을 하지 않는다.** 근거:")
    w("")
    w("- TC-11은 **빈 좌석·R2·R0**, **0·20·50 °C**, **보정 무·유** 18개 조합(각 300회)만 다룸(아래 커버 조건표). 다른 대상·온도·조합은 다루지 않음.")
    w("- 50 °C·보정 없음에서 R0 오검출이 **300/300**이므로 보정 없는 구성은 SR-09 를 충족하지 못했음(INC-03). 보정 있음은 같은 조건에서 0/300임. 보정의 요구사항 채택은 기준선 시점(2026-11-11)에는 미결이었으며 2026-11-13 김*수 결정(Notion TP-01 PR-2 참조)으로 v1.1 기본 구성에 채택됨(D3, 후속 검토 1번). v1.1에서 다시 확인하기 전까지 SR-09 전체 충족 선언은 보류함.")
    w("- 결정 D3: \"TC-11 커버 조건 표시, SR-09 전체 충족 선언 금지\".")
    w("")
    w("**TC-11 커버 조건 (`coverage_TC11.csv`)**")
    w("")
    w(table(list(d["cov"][0].keys()), [list(r.values()) for r in d["cov"]]))
    w("")
    w("### 4.4 TC-11 Side-by-Side (온도·보정 나란히 보기)")
    w("")
    w("`tc11_side_by_side.csv` 전체. 대상별로 합산하지 않고 각각 집계함(D5). 상한95는 단측 95 % 정확 이항 상한.")
    w("")
    rows = []
    for r in d["tc11"]:
        rows.append([r["대상"], r["지표"], r["온도(°C)"], r["보정 없음 k/n"], pct(r["보정 없음 관측"]), pct(r["보정 없음 상한95"]), r["보정 없음 판정"],
                     r["보정 있음 k/n"], pct(r["보정 있음 관측"]), pct(r["보정 있음 상한95"]), r["보정 있음 판정"]])
    w(table(["대상", "지표", "온도(°C)", "보정 없음 k/n", "관측", "상한95", "판정", "보정 있음 k/n", "관측", "상한95", "판정"], rows))
    w("")

    w("### 4.5 Follow-up Items (후속 검토 5건, `baseline_v1.0.json`의 `follow_up_items`)")
    w("")
    fmap = {
        "온도 보정의 요구사항 채택": "D3 / INC-03 (2026-11-13 김*수 결정으로 v1.1 채택, TP-01 PR-2 참조)",
        "초기 빈 좌석 실측 보정(d_empty)": "D4",
        "O-A/O-B/O-C/O-S 대상 치수 확보": "D1 (TC-12 미실행 포함)",
        "차량 시동과 센서 전원의 관계": "D8 (TC-08)",
        "착석 위치 분포": "D1 (단일점 높이 모델 한계)",
    }
    fu = d["baseline"]["follow_up_items"]
    w(table(["#", "후속 검토 항목", "관련 결정/이상"], [[n, f, fmap.get(f, "—")] for n, f in enumerate(fu, 1)]))
    w("")

    w("### 4.6 Completion Summary (완료 요약)")
    w("")
    w(f"- 계획된 시험 케이스 TC-01 ~ TC-16 중 결과 행 {len(summ)}개를 기록함. 미실행 {cnt.get('미실행', 0)}개(O-A/O-B/O-C 원 조건, TC-12), "
      f"불합격 {cnt.get(S_FAIL, 0)}개(INC-01~03).")
    w(f"- 통계 확인 목표 충족 {cnt.get(S_OK, 0)}개, 결정적 시험 일치 {cnt.get('일치', 0)}개, 전 시행 기준 충족 {cnt.get('기준 충족(전 시행)', 0)}개.")
    w(f"- 합격 판정 없는 기록 {cnt.get('기록(합격 판정 없음)', 0)}개와 가정 기반 민감도 기록 {cnt.get('가정 기반 민감도 기록', 0)}개는 합격 건수에 포함하지 않음.")
    w("- 계획 대비 편차: 기준선·목표·시행 수 변경 없음. 입력 부재로 인한 미실행만 있음.")
    w("- **SR-09 는 부분 커버이며 전체 충족을 선언하지 않음**(4.3절). 이 보고서는 시스템 전체의 합격을 선언하지 않으며, 결과는 SIL 모델·입력 분포에 한정됨.")
    w("- 잔여 위험·후속: INC-01~03 과 4.5절 후속 검토 5건을 GitHub Issue 로 추적함.")
    w("")

    # ------------------------------------------------------------------ Appendix
    w("## Appendix A. Full Results by TC (summary.csv 전체 152행)")
    w("")
    w("행 번호(`#`)는 `summary.csv` 데이터 행 순번(1부터)이다. 상태 라벨은 원문 그대로이며 `불합격` 행은 비고 앞에 해당 INC 번호를 붙였다.")
    w("")
    inc_by_row = {i["row"]: i["id"] for i in inc}
    for tc, rs in by_tc.items():
        w(f"### {tc} ({len(rs)}행)")
        w("")
        rows = []
        for n, r in rs:
            note = r["note"]
            if n in inc_by_row:
                note = f"[{inc_by_row[n]}] " + note.strip()
            ea = ""
            if r["expected"] or r["actual"]:
                ea = f"기대: {blank(r['expected'])} / 실제: {blank(r['actual'])}"
            rows.append([n, r["cond_id"], r["condition"], r["sr"], r["kind"], blank(r["metric"]), blank(r["n"]), blank(r["k"]),
                         pct(r["observed"]), pct(r["upper95"]), pct(r["target"]), r["status"], ea, blank(r["surface"]), blank(note)])
        w(table(["#", "조건 ID", "조건", "SR", "종류", "지표", "n", "k", "관측", "상한95", "목표", "상태", "기대 / 실제", "반사면", "비고"], rows))
        w("")

    w("## Appendix B. Baseline vs Code Verification (baseline_verification.csv 전체 87항목)")
    w("")
    w(table(["#", "항목", "기준선 v1.0", "코드 값", "코드 위치", "일치"],
            [[n, r["항목"], r["기준선 v1.0"], r["코드 값"], r["코드 위치"], r["일치"]] for n, r in enumerate(d["verif"], 1)]))
    w("")
    w("---")
    w(f"*End of document — {DOC_ID}*")
    w("")
    return "\n".join(L), all_ok


# ----------------------------------------------------------------------------------------------
def main(argv):
    report_date = datetime.date.today().isoformat()
    selftest_result = ""
    it = iter(argv)
    for a in it:
        if a == "--date":
            report_date = datetime.date.fromisoformat(next(it)).isoformat()
        elif a == "--selftest-result":
            selftest_result = next(it)
        else:
            raise SystemExit(__doc__)
    d = load()
    checks = run_checks(d)
    inc = build_incidents(d)
    text, ok = build_report(d, checks, inc, report_date, selftest_result)
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"작성: {OUT} ({len(text.splitlines())}줄)")
    for name, c_ok, detail in checks:
        print(("통과" if c_ok else "실패"), "-", name, "|", detail)
    if not ok:
        print("무결성 점검 실패 항목이 있음", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
