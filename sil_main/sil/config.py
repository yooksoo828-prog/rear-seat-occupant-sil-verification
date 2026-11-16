"""예비시험 설정 (5단계 문서 v0.4.1, 10.2절 예비시험 설정표).

각 값의 구분은 문서 표기를 따름.
  [문헌] 데이터시트·논문 값, [계산값], [구현 설정(예비)], [프로젝트 가정]
가정값과 구현 설정은 문헌의 권위를 갖지 않음.
"""
from dataclasses import dataclass, asdict, field


@dataclass(frozen=True)
class Geometry:
    H_s_cm: float = 100.0            # 센서 높이 [구현 설정(예비)]
    # 반사면 높이 [프로젝트 가정] - 6세 더미·인체·실제 가방 치수가 아님
    R0_cm: float = 5.0               # 낮은 화물
    R1_cm: float = 20.0
    R2_cm: float = 40.0
    R3_cm: float = 60.0


@dataclass(frozen=True)
class SensorModel:
    c_formula: str = "331.4 + 0.6*T (m/s)"   # 온도 모델 [문헌: Arunglabi et al., 2026이 쓴 식]
    T_air_C: float = 20.0                     # 기준 온도 [프로젝트 가정]
    sigma_cm: float = 1.0                     # 잡음 표준편차, N(0, sigma^2), 시간 독립 [프로젝트 가정]
    p_loss: float = 0.0                       # 샘플별 에코 미수신 확률, 독립 베르누이 [프로젝트 가정]
    bias_cm: float = 0.0                      # 거리 편향 [프로젝트 가정]
    period_s: float = 0.100                   # 측정 요청 주기 [구현 설정(예비)], 하한 60 ms 초과는 [문헌]
    T_to_s: float = 0.030                     # 에코 타임아웃 [구현 설정(예비)], 4 m 왕복 23.5 ms는 [계산값]


@dataclass(frozen=True)
class Detector:
    d_empty_cm: float = 100.0        # 빈 좌석 기준 거리 = H_s [계산값], 예비시험은 H_s 값을 그대로 씀
    delta_on_cm: float = 10.0        # [구현 설정(예비)]
    delta_off_cm: float = 5.0        # [구현 설정(예비)]
    k: int = 5                       # 중앙값 필터 창 [구현 설정(예비)]
    M: int = 5                       # 연속 무효 샘플 수 → UNKNOWN [구현 설정(예비)]
    T_stale_s: float = 1.0           # [구현 설정(예비)]
    T_db_s: float = 0.0              # 디바운스, 0 s / 0.5 s 비교 [구현 설정(예비)]
    valid_min_cm: float = 2.0        # 측정 가능 범위 [문헌: 데이터시트]
    valid_max_cm: float = 400.0
    c_fixed_mps: float = 340.0       # 거리 환산 음속 [문헌: 데이터시트]
    temp_comp: bool = False          # 온도 보정 유무 [프로젝트 선택: 두 구성 비교]
    db_basis: str = "rx"              # 디바운스 시간 기준: 'rx'=후보 첫 수신 시각(예비시험 동작), 'req'=후보 첫 측정 요청 시각 [본시험 전 결정 항목]

    @property
    def delta_mid_cm(self) -> float:  # 초기 히스테리시스 구간 기준 [계산값]
        return (self.delta_on_cm + self.delta_off_cm) / 2.0


@dataclass(frozen=True)
class Evaluation:
    t_eval_s: float = 3.0            # 판정 시점 [구현 설정(예비)]
    T_first_s: float = 1.0           # [구현 설정(예비)]
    T_recover_s: float = 1.0         # [구현 설정(예비)]
    hold_s: float = 1.0              # 응답 확인 구간(평가 규칙) [구현 설정(예비)]
    response_limit_s: float = 3.0    # SR-07(b) [달성 목표(잠정)]
    temp_input_err_C: float = 2.0    # 보정 시 온도 입력 오차 Uniform(-2,+2), 시행마다 1회 추출 [프로젝트 가정]
    n_random: int = 10               # 예비시험 무작위 반복 수 [프로젝트 가정], 통계 판정 안 함
    base_seed: int = 20261111


@dataclass(frozen=True)
class PrelimConfig:
    geometry: Geometry = field(default_factory=Geometry)
    sensor: SensorModel = field(default_factory=SensorModel)
    detector: Detector = field(default_factory=Detector)
    evaluation: Evaluation = field(default_factory=Evaluation)

    def to_dict(self):
        d = asdict(self)
        d["detector"]["delta_mid_cm"] = self.detector.delta_mid_cm
        return d


def speed_of_sound(T_C: float) -> float:
    """온도 모델 c(T) = 331.4 + 0.6T (m/s) [문헌: Arunglabi et al., 2026이 쓴 식]."""
    return 331.4 + 0.6 * T_C
