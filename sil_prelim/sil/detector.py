"""점유 판단 소프트웨어 (검증 대상).

문서 대응
  SR-05 거리 구분·히스테리시스(4.4절)   SR-07(a) 초기화·최초 판정
  SR-10 에코 없음  SR-11 범위 밖  SR-12 갱신 중단  SR-13 출력 3값
  7.1절 이상 입력과 복구 규칙
"""
from collections import deque
import statistics

from .config import speed_of_sound
from .scenario import OCC, UNOCC, UNK

INIT, UNKNOWN = "INIT", "UNKNOWN_STATE"


class OccupancyDetector:
    def __init__(self, cfg, T_input_C=None):
        self.cfg = cfg
        self.c = speed_of_sound(T_input_C) if (cfg.temp_comp and T_input_C is not None) else cfg.c_fixed_mps
        self.mode = INIT
        self.filt = deque(maxlen=cfg.k)
        self.consec_invalid = 0
        self.last_valid_t = None
        self.pending = None          # 디바운스 후보 (값, 시작 시각)
        self.log = []                # (t, 출력)
        self.events = []             # (t, 사건, 상세)
        self._out = UNK
        self._emit(0.0, "power_on")

    # ---- 출력 ----
    @property
    def output(self):
        return {INIT: UNK, UNKNOWN: UNK}.get(self.mode, self.mode)

    def _emit(self, t, why):
        if not self.log or self.log[-1][1] != self.output:
            self.log.append((round(t, 6), self.output))
            self.events.append((round(t, 6), "output", f"{self.output} ({why})"))

    def _recovering(self):
        return self.mode in (INIT, UNKNOWN)

    def _enter_unknown(self, t, why):
        self.mode = UNKNOWN
        self.filt.clear()
        self.consec_invalid = 0
        self.pending = None
        self.events.append((round(t, 6), "unknown_entry", why))
        self._emit(t, why)

    # ---- 판정 (필터 뒤 Δ) ----
    def decide(self, t, delta):
        """필터 뒤 Δ로 판정. P-03·TC-07의 직접 주입도 이 함수를 씀."""
        c = self.cfg
        if self._recovering():
            cand = OCC if delta >= c.delta_mid_cm else UNOCC      # 최초 판정 규칙(중간값 이상 점유)
        elif self.mode == UNOCC:
            cand = OCC if delta >= c.delta_on_cm else UNOCC
        else:
            cand = UNOCC if delta <= c.delta_off_cm else OCC
        if not self._recovering() and cand == self.mode:
            self.pending = None
            return
        if self.pending is None or self.pending[0] != cand:
            self.pending = (cand, t)
        if t - self.pending[1] >= c.T_db_s - 1e-9:
            was = self.mode
            self.mode = cand
            self.pending = None
            if was in (INIT, UNKNOWN):
                self.events.append((round(t, 6), "valid_decision", cand))
            self._emit(t, "decision")

    # ---- 샘플 처리 ----
    def on_sample(self, t, pulse_us):
        c = self.cfg
        if pulse_us is None:
            return self._invalid(t, "no_echo")
        d = pulse_us * 1e-6 * self.c / 2 * 100.0
        if not (c.valid_min_cm <= d <= c.valid_max_cm):
            return self._invalid(t, "out_of_range", d)
        self.consec_invalid = 0
        self.last_valid_t = t
        if self._recovering() and len(self.filt) == 0:
            self.events.append((round(t, 6), "recovery_first_valid", ""))
        self.filt.append(d)
        if len(self.filt) < c.k:
            return {"d_conv": d, "valid": True, "d_med": None, "delta": None}
        d_med = statistics.median(self.filt)
        delta = c.d_empty_cm - d_med
        self.decide(t, delta)
        return {"d_conv": d, "valid": True, "d_med": d_med, "delta": delta}

    def _invalid(self, t, reason, d=None):
        self.consec_invalid += 1
        if self._recovering():
            # 복구 도중 무효 입력: 복구용 창과 후보를 다시 초기화 (7.1절)
            if self.filt or self.pending:
                self.events.append((round(t, 6), "recovery_reset", reason))
            self.filt.clear()
            self.pending = None
        elif self.consec_invalid >= self.cfg.M:
            self._enter_unknown(t, f"{reason} x{self.consec_invalid}")
        return {"d_conv": d, "valid": False, "reason": reason, "d_med": None, "delta": None}

    # ---- 갱신 중단 감시 (측정 주기마다 실행) ----
    def watchdog(self, t):
        if self._recovering() or self.last_valid_t is None:
            return
        if t - self.last_valid_t >= self.cfg.T_stale_s - 1e-9:
            self._enter_unknown(t, "stale")
