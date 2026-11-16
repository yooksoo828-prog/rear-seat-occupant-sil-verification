"""평가: 판정 시점 출력, 최초 유효 판정, 응답 시간(9.3절), 뒤집힘, 측정 주기, 비율.

예비시험에서는 통계 판정(신뢰상한)을 하지 않음 (문서 10.1절).
"""
from .scenario import OCC, UNOCC, UNK


def output_at(out_log, t):
    """시각 t(포함)까지 마지막으로 나온 출력. 기한까지 출력이 없으면 UNKNOWN."""
    val = UNK
    for tt, v in out_log:
        if tt <= t + 1e-9:
            val = v
        else:
            break
    return val


def first_valid_time(out_log):
    for tt, v in out_log:
        if v in (OCC, UNOCC):
            return tt
    return None


def response_time(out_log, t_gt, new_truth, hold=1.0, limit=3.0):
    """9.3절: t_gt 이후 limit 이내에 시작해 hold 동안 유지되는 정답 구간의 시작 시각 - t_gt.

    출력이 사건 이전부터 이미 새 정답이면 t_gt를 시작으로 봄. 없으면 None(기한 초과).
    """
    segs = []  # (시작, 끝, 값)
    for i, (tt, v) in enumerate(out_log):
        end = out_log[i + 1][0] if i + 1 < len(out_log) else float("inf")
        segs.append((tt, end, v))
    for a, b, v in segs:
        if v != new_truth or b <= t_gt:
            continue
        start = max(a, t_gt)
        if start - t_gt > limit + 1e-9:
            break
        if b - start >= hold - 1e-9:
            return round(start - t_gt, 6)
    return None


def flips(out_log, t0, t1):
    """[t0, t1] 안에서 출력이 바뀐 횟수."""
    return sum(1 for tt, _ in out_log if t0 < tt <= t1)


def min_request_interval(req_times):
    return min(b - a for a, b in zip(req_times, req_times[1:]))


def rates(outputs, truth):
    n = len(outputs)
    wrong = OCC if truth == UNOCC else UNOCC
    return {
        "n": n,
        "correct": sum(o == truth for o in outputs),
        "error": sum(o == wrong for o in outputs),
        "unknown": sum(o == UNK for o in outputs),
    }
