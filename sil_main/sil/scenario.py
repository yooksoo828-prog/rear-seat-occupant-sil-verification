"""입력 생성과 정답(ground truth).

정답은 시나리오 정의(대상 종류와 시간 구간)로만 정하며, 센서 출력이나
판단 알고리즘 결과로 정하지 않음 (문서 4.3절).
"""
from dataclasses import dataclass, field
import math

OCC = "OCCUPIED"
UNOCC = "UNOCCUPIED"
UNK = "UNKNOWN"


@dataclass(frozen=True)
class Segment:
    """t_start부터 다음 구간 전까지 좌석 위 대상.

    kind: 'empty' | 'occupant' | 'cargo'
    h_cm: 반사면 높이(방석 기준). empty면 0.
    motion_amp_cm / motion_hz: 움직임 가정(거리 변동) [프로젝트 가정], 0이면 정지.
    """
    t_start: float
    kind: str
    h_cm: float = 0.0
    motion_amp_cm: float = 0.0
    motion_hz: float = 0.0

    @property
    def truth(self) -> str:
        # 점유 대상 착석 구간은 점유, 빈 좌석과 화물은 비점유 (문서 4.3절)
        return OCC if self.kind == "occupant" else UNOCC


@dataclass(frozen=True)
class Faults:
    """고장 주입. 측정 요청 번호(0부터) 기준."""
    drop_echo: frozenset = frozenset()          # 에코 제거(타임아웃)
    substitute_cm: tuple = ()                    # ((요청 번호, 거리 cm), ...) 값 치환
    stall: tuple = ()                            # ((t0, t1), ...) 이 구간 요청의 결과 전달 중단


@dataclass(frozen=True)
class Scenario:
    name: str
    segments: tuple                  # Segment들, t_start 오름차순
    duration_s: float
    T_air_C: float = 20.0
    faults: Faults = field(default_factory=Faults)
    loss_schedule: tuple = ()        # ((t_start, p_loss), ...) 비어 있으면 상수 p_loss 사용(예비시험과 동일)

    def p_loss_at(self, t, default):
        p = default
        for t0, v in self.loss_schedule:
            if t0 <= t + 1e-12:
                p = v
        return p

    def segment_at(self, t: float) -> Segment:
        seg = self.segments[0]
        for s in self.segments:
            if s.t_start <= t + 1e-12:
                seg = s
        return seg

    def truth(self, t: float) -> str:
        return self.segment_at(t).truth

    def target_height(self, t: float) -> float:
        s = self.segment_at(t)
        if s.kind == "empty":
            return 0.0
        h = s.h_cm
        if s.motion_amp_cm:
            h += s.motion_amp_cm * math.sin(2 * math.pi * s.motion_hz * t)
        return h

    def true_distance(self, t: float, H_s: float) -> float:
        return H_s - self.target_height(t)

    def events(self):
        """정답이 바뀌는 시각 목록 (t_gt, 새 정답)."""
        out = []
        for a, b in zip(self.segments, self.segments[1:]):
            if a.truth != b.truth:
                out.append((b.t_start, b.truth))
        return out


def static(name, kind, h=0.0, duration=5.0, T_air=20.0, faults=None, motion=(0.0, 0.0)):
    return Scenario(name, (Segment(0.0, kind, h, motion[0], motion[1]),), duration, T_air,
                    faults or Faults())
