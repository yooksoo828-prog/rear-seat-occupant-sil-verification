"""본시험 코드 자체 점검 (판정 아님).

  python3 selftest.py [sil_prelim 폴더 경로]

1) 정확 이항 상한과 판정 구분이 시험 설계 9.4절의 수치와 같은지
2) 확장한 sil/ 패키지가 예비시험 결과를 그대로 재현하는지(예비시험 코드·결과는 sil_prelim에 보존)
3) 사전점검을 두 번 실행해 결과가 같은지(재현성)
4) summary.csv의 비율 행이 trials.csv에서 다시 센 값과 같은지(집계 코드 점검)
"""
import csv, filecmp, gzip, os, shutil, subprocess, sys, tempfile
from main_lib import stats

HERE = os.path.dirname(os.path.abspath(__file__))
PRELIM = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), "sil_prelim")
ok_all = True


def check(name, cond, detail=""):
    global ok_all
    ok_all &= bool(cond)
    print(("통과" if cond else "실패"), "-", name, detail)


# 1) 통계
doc300 = {0: 0.0099, 1: 0.0157, 2: 0.0208, 3: 0.0256, 4: 0.0303}
doc60 = {0: 0.0487, 1: 0.0766, 2: 0.1012, 3: 0.1242, 4: 0.1461}
for n, tab in ((300, doc300), (60, doc60)):
    for k, v in tab.items():
        ub = stats.upper_bound(k, n)
        check(f"상한 n={n}, k={k}", abs(ub - v) < 6e-4, f"계산 {ub:.4f} / 문서 {v}")
check("최소 시행 수 1% → 299, 5% → 59", (stats.min_n_zero_error(0.01), stats.min_n_zero_error(0.05)) == (299, 59))
exp = {(300, 0): stats.S_OK, (300, 1): stats.S_OBS, (300, 3): stats.S_OBS, (300, 4): stats.S_FAIL,
       (60, 0): stats.S_OK, (60, 3): stats.S_OBS, (60, 4): stats.S_FAIL}
for (n, k), st in exp.items():
    tg = 0.01 if n == 300 else 0.05
    check(f"판정 n={n}, k={k}, 목표 {tg:g}", stats.judge_rate(k, n, tg)[2] == st, stats.judge_rate(k, n, tg)[2])
check("미확정률 60회 0건은 통계 미확인(1% 목표)", stats.judge_rate(0, 60, 0.01)[2] == stats.S_OBS)

# 2) 예비시험 재현
if os.path.isdir(PRELIM):
    tmp = tempfile.mkdtemp()
    shutil.copytree(os.path.join(HERE, "sil"), os.path.join(tmp, "sil"))
    shutil.copy(os.path.join(PRELIM, "run_prelim.py"), tmp)
    subprocess.run([sys.executable, "run_prelim.py", "out"], cwd=tmp, check=True, capture_output=True)
    same = all(filecmp.cmp(os.path.join(tmp, "out", f), os.path.join(PRELIM, "results", f), shallow=False)
               for f in ("results.csv", "trial_samples.csv", "output_log.csv", "events.csv", "p08_sensitivity.csv"))
    check("확장한 sil/ 패키지가 예비시험 결과 5개 파일을 바이트 단위로 재현", same)
    shutil.rmtree(tmp)
else:
    print("건너뜀 - sil_prelim 폴더 없음:", PRELIM)


# 3) 재현성
def read_gz(p):
    return gzip.open(p, "rt", encoding="utf-8").read()


a, b = tempfile.mkdtemp(), tempfile.mkdtemp()
for d in (a, b):
    subprocess.run([sys.executable, "run_main.py", "precheck", d], cwd=HERE, check=True, capture_output=True)
files = ("summary.csv", "trials.csv", "output_log.csv", "events.csv")
check("사전점검 두 번 실행 결과 동일(요약·시행·출력·사건)", all(filecmp.cmp(os.path.join(a, f), os.path.join(b, f), shallow=False) for f in files))
check("측정 로그 동일(압축 해제 내용 비교)", read_gz(os.path.join(a, "trial_samples.csv.gz")) == read_gz(os.path.join(b, "trial_samples.csv.gz")))

# 4) 집계 재계산
summ = list(csv.DictReader(open(os.path.join(a, "summary.csv"), encoding="utf-8")))
trials = list(csv.DictReader(open(os.path.join(a, "trials.csv"), encoding="utf-8")))
bad = 0
n_checked = 0
for r in summ:
    if r["kind"] == "rate" and r["metric"] in ("미검출률", "오검출률", "미확정률"):
        rows = [t for t in trials if t["tc"] == r["tc"] and t["cond"] == r["cond_id"]]
        if not rows:
            continue
        key = "UNKNOWN" if r["metric"] == "미확정률" else "오류"
        k = sum(1 for t in rows if t["result"] == key)
        n_checked += 1
        bad += not (k == int(r["k"]) and len(rows) == int(r["n"]))
check(f"비율 행 {n_checked}개의 k·n이 시행 기록에서 다시 센 값과 같음", bad == 0 and n_checked > 0, f"불일치 {bad}")
# 5) 본시험(기준선 v1.0): 두 번 실행해 결과가 같은지, 집계 재계산, 기준선·코드 값 확인
BASE = os.path.join(HERE, "baseline", "baseline_v1.0.json")
if os.path.exists(BASE):
    import json, hashlib
    # run_main.py main은 results_main에 쓰므로 복사본에서 실행
    root = tempfile.mkdtemp()
    tmp = os.path.join(root, "sil_main")
    os.makedirs(tmp)
    if os.path.isdir(PRELIM):
        shutil.copytree(PRELIM, os.path.join(root, "sil_prelim"))      # run_main.py가 예비시험 움직임 값을 ../sil_prelim에서 읽음
    for d in ("sil", "main_lib", "baseline"):
        shutil.copytree(os.path.join(HERE, d), os.path.join(tmp, d))
    shutil.copy(os.path.join(HERE, "run_main.py"), tmp)
    m1 = os.path.join(tmp, "results_main")
    subprocess.run([sys.executable, "run_main.py", "main"], cwd=tmp, check=True, capture_output=True)
    shutil.copytree(m1, m1 + "_1")
    subprocess.run([sys.executable, "run_main.py", "main"], cwd=tmp, check=True, capture_output=True)
    check("본시험 두 번 실행 결과 동일(요약·시행·출력·사건)",
          all(filecmp.cmp(os.path.join(m1, f), os.path.join(m1 + "_1", f), shallow=False) for f in files))
    check("본시험 측정 로그 동일", read_gz(os.path.join(m1, "trial_samples.csv.gz")) == read_gz(os.path.join(m1 + "_1", "trial_samples.csv.gz")))
    ver = list(csv.DictReader(open(os.path.join(m1, "baseline_verification.csv"), encoding="utf-8")))
    check(f"기준선·코드 값 확인 {len(ver)}개 항목 모두 일치", ver and all(r["일치"] == "일치" for r in ver))
    cfgj = json.load(open(os.path.join(m1, "config.json"), encoding="utf-8"))
    check("config.json의 기준선 sha256이 파일과 같음", cfgj["config"]["_baseline_sha256"] == hashlib.sha256(open(BASE, "rb").read()).hexdigest())
    summ = list(csv.DictReader(open(os.path.join(m1, "summary.csv"), encoding="utf-8")))
    trials = list(csv.DictReader(open(os.path.join(m1, "trials.csv"), encoding="utf-8")))
    bad = n_checked = 0
    for r in summ:
        if r["kind"] == "rate" and r["metric"] in ("미검출률", "오검출률", "미확정률"):
            conds = (r["cond_id"], r["cond_id"] + "/cargo")          # TC-04b는 시행이 '04b-x/cargo' 이름으로 기록됨
            rows = [t for t in trials if t["tc"] == r["tc"] and t["cond"] in conds]
            key = "UNKNOWN" if r["metric"] == "미확정률" else "오류"
            k = sum(1 for t in rows if t["result"] == key)
            n_checked += 1
            bad += not (rows and k == int(r["k"]) and len(rows) == int(r["n"]))
    check(f"본시험 비율 행 {n_checked}개의 k·n이 시행 기록에서 다시 센 값과 같음", bad == 0 and n_checked > 0, f"불일치 {bad}")
    shutil.rmtree(root)

print("\n전체:", "통과" if ok_all else "실패 있음")
sys.exit(0 if ok_all else 1)
