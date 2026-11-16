"""시나리오 1회(시행 1회) 실행: 센서 모델 → 판단 소프트웨어, 로그 기록."""
import numpy as np

from .sensor_model import generate_samples
from .detector import OccupancyDetector


def run_trial(scn, cfg, seed, det_cfg=None, sigma=None, p_loss=None, bias=None):
    det_cfg = det_cfg or cfg.detector
    samples = generate_samples(scn, cfg.sensor, cfg.geometry, seed, sigma, p_loss, bias)
    # 온도 보정 입력 오차: 시행마다 Uniform(-e, +e)에서 1회 추출하여 고정 [프로젝트 가정]
    T_in = None
    if det_cfg.temp_comp:
        rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(seed).spawn(3)[2]))
        e = cfg.evaluation.temp_input_err_C
        T_in = scn.T_air_C + float(rng.uniform(-e, e))
    det = OccupancyDetector(det_cfg, T_in)
    queue = []
    for s in samples:
        queue.append((s.t_req, 0, "tick", s))          # 감시는 요청 시각에, 같은 시각이면 먼저
        if s.t_rx is not None:
            queue.append((s.t_rx, 1, "rx", s))
    queue.sort(key=lambda x: (x[0], x[1], x[3].idx))
    rows = []
    for t, _, kind, s in queue:
        if kind == "tick":
            det.watchdog(t)
            continue
        r = det.on_sample(t, s.pulse_us)
        rows.append({
            "idx": s.idx, "t_req": s.t_req, "t_rx": s.t_rx, "status": s.status, "cause": s.cause,
            "d_true_cm": round(s.d_true_cm, 4), "noise_cm": round(s.noise_cm, 4),
            "pulse_us": None if s.pulse_us is None else round(s.pulse_us, 3),
            "d_conv_cm": None if r.get("d_conv") is None else round(r["d_conv"], 4),
            "d_med_cm": None if r["d_med"] is None else round(r["d_med"], 4),
            "delta_cm": None if r["delta"] is None else round(r["delta"], 4),
            "output": det.output, "truth": scn.truth(t),
        })
    for s in samples:   # 전달 중단 요청도 기록
        if s.t_rx is None:
            rows.append({"idx": s.idx, "t_req": s.t_req, "t_rx": None, "status": s.status, "cause": s.cause,
                         "d_true_cm": round(s.d_true_cm, 4), "noise_cm": round(s.noise_cm, 4),
                         "pulse_us": None, "d_conv_cm": None, "d_med_cm": None, "delta_cm": None,
                         "output": None, "truth": scn.truth(s.t_req)})
    rows.sort(key=lambda r: r["idx"])
    return {"seed": seed, "T_input_C": T_in, "rows": rows, "out_log": det.log, "events": det.events,
            "req_times": [s.t_req for s in samples]}
