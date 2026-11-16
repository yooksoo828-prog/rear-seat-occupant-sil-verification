"""HC-SR04 센서 모델 (SIL의 물리 측).

출력은 HC-SR04가 실제로 내보내는 정보와 같은 형태인 에코 펄스 폭(µs)이며,
거리 환산은 판단 소프트웨어(detector)가 함.
  - 비행 시간: tof = 2 * (d_true + bias + noise) / c(T)            [문헌 식 c(T), 나머지 프로젝트 가정]
  - 잡음: 유효 샘플마다 N(0, sigma^2), 시간 독립                     [프로젝트 가정]
  - 반사 손실: 샘플마다 확률 p_loss 의 독립 베르누이                  [프로젝트 가정]
  - tof > T_to 이면 타임아웃(에코 없음)
잡음 난수열과 손실 난수열은 서로 독립 (SeedSequence.spawn).
"""
from dataclasses import dataclass
import numpy as np

from .config import speed_of_sound


@dataclass
class Sample:
    idx: int
    t_req: float
    t_rx: float | None        # 판단 소프트웨어가 결과를 받는 시각. 전달 중단이면 None
    pulse_us: float | None    # 에코 펄스 폭. 타임아웃이면 None
    status: str               # 'echo' | 'timeout' | 'stalled'
    cause: str                # 'none' | 'loss' | 'drop_echo' | 'substitute' | 'stall' | 'range'
    d_true_cm: float
    noise_cm: float


def generate_samples(scn, sensor_cfg, geom, seed, sigma=None, p_loss=None, bias=None):
    sigma = sensor_cfg.sigma_cm if sigma is None else sigma
    p_loss = sensor_cfg.p_loss if p_loss is None else p_loss
    bias = sensor_cfg.bias_cm if bias is None else bias
    noise_rng, loss_rng = [np.random.Generator(np.random.PCG64(s))
                           for s in np.random.SeedSequence(seed).spawn(2)]
    c = speed_of_sound(scn.T_air_C)
    period, T_to = sensor_cfg.period_s, sensor_cfg.T_to_s
    subst = dict(scn.faults.substitute_cm)
    n_req = int(round(scn.duration_s / period)) + 1
    out = []
    for i in range(n_req):
        t = round(i * period, 6)
        d_true = scn.true_distance(t, geom.H_s_cm)
        # 난수는 조건과 관계없이 매 요청마다 같은 순서로 뽑아 시드별 재현성을 유지함
        n = float(noise_rng.normal(0.0, sigma)) if sigma > 0 else 0.0
        if scn.loss_schedule:
            lost = bool(loss_rng.random() < scn.p_loss_at(t, p_loss))
        else:
            lost = bool(loss_rng.random() < p_loss) if p_loss > 0 else False
        stalled = any(a <= t < b for a, b in scn.faults.stall)
        if i in subst:
            # 값 치환: 데이터시트 환산식(340 m/s)으로 subst 거리가 되도록 펄스 폭을 만듦
            pulse = 2 * subst[i] / 100.0 / 340.0 * 1e6
            status, cause, tof = "echo", "substitute", pulse * 1e-6
        elif i in scn.faults.drop_echo or lost:
            status, cause, tof, pulse = "timeout", ("drop_echo" if i in scn.faults.drop_echo else "loss"), None, None
        else:
            d_phys = max(d_true + bias + n, 0.0)
            tof = 2 * d_phys / 100.0 / c
            if tof > T_to:
                status, cause, pulse = "timeout", "range", None
                tof = None
            else:
                status, cause, pulse = "echo", "none", tof * 1e6
        if stalled:
            out.append(Sample(i, t, None, None, "stalled", "stall", d_true, n))
            continue
        t_rx = t + (tof if tof is not None else T_to)
        out.append(Sample(i, t, round(t_rx, 6), pulse, status, cause, d_true, n))
    return out
