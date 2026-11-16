"""정확 이항 단측 95% 상한과 조건별 판정 (시험 설계 9.4절).

표준 라이브러리만 사용함. 상한 p_U는 P(X <= k | n, p_U) = 0.05 의 해(Clopper-Pearson 단측)임.
오류 0회이면 (1 - p_U)^n = 0.05 와 같음.
"""
import math

CONF = 0.95
S_OK = "목표 충족(통계 확인)"
S_OBS = "관측 충족(통계 미확인)"
S_FAIL = "불합격"


def binom_cdf(k, n, p):
    if p <= 0:
        return 1.0
    if p >= 1:
        return 1.0 if k >= n else 0.0
    lp, lq = math.log(p), math.log1p(-p)
    return min(1.0, sum(math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * lp + (n - i) * lq)
                        for i in range(0, k + 1)))


def upper_bound(k, n, conf=CONF):
    """오류 k회/시행 n회의 단측 정확 이항 상한."""
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


def min_n_zero_error(p, conf=CONF):
    """오류 0회로 상한이 p 이하가 되는 최소 시행 수."""
    return math.ceil(math.log(1 - conf) / math.log(1 - p) - 1e-12)


def judge_rate(k, n, target):
    """관측 비율과 단측 95% 상한을 목표와 비교 (9.4절)."""
    obs = k / n
    ub = upper_bound(k, n)
    if obs > target + 1e-12:
        status = S_FAIL
    elif ub <= target + 1e-12:
        status = S_OK
    else:
        status = S_OBS
    return obs, ub, status
