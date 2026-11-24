# HIL

> **이전 문서** — 원본: Notion "HIL"(문서 목록 데이터베이스, 마지막 수정 2026-11-11). Notion에서 2026-11-24에 내보내 같은 날 이 저장소로 옮김.
> 이전 시 바꾼 것: 파일 이름 정리, 비공개 Notion 링크 제거(근거 출처는 제목만 남김), 논문·데이터시트에서 가져온 그림은 저작권 때문에 생략(캡션만 유지). 본문 내용은 바꾸지 않음.
> 팀원 실명은 원본에 없었다. 이 문서의 수치·해석은 Notion 시점(2026-11-11)의 것이며 이후 결정(2026-11-13 등)은 `docs/29119/`의 문서가 기준이다.


V모델 순서: 41
근거 출처: Short & Pont (2005) Hardware in the loop simulation of embedded automotive control systems, Isermann, Schaffnit & Sinsel (1998) Hardware-in-the-loop simulation for the design and testing of engine-control systems, Bullock et al. (2004) Hardware-in-the-loop simulation, Nguyen et al. (2020) Hardware-in-the-loop assessment methods (European Guide to Power System Testing, ch. 4), Lee, Huang & Lan (2018) HIL test case specification for verification of software safety requirements in the context of ISO 26262, ISO 26262-4:2018 Product development at the system level (ISO 카탈로그 페이지), ISO 26262-6:2018 Product development at the software level (ISO 카탈로그 페이지), Zhu 외(2025) High-Fidelity Ultrasonic Radar In-the-Loop Accelerated Test for Automatic Parking Systems, Ma et al. (2023) Research on the autonomous parking strategy based on the ultrasonic echo simulator
단계: 4 검증 방법론
마지막 수정일: 2026년 11월 11일 오후 1:28
상태: 검토 완료

<aside>
📌

HIL(Hardware-in-the-Loop)의 정의와 구성, 장점과 한계, ISO 26262과의 관계, 초음파 센서에 적용된 HIL 사례를 학교 구독 DB의 논문(IEEE Xplore, ScienceDirect, Springer) 기준으로 정리한 문서임. 그림은 원문 PDF에서 발췌한 뒤 용량을 줄인 흑백 이미지임. 참고문헌은 문서 하단에 APA 7판 형식으로 정리함. (2026-11-07, 초안)

</aside>

## 1. HIL이란

> [그림 생략] 그림. Short와 Pont(2005)의 Fig. 1, HIL 시뮬레이션의 원리 — 논문·데이터시트의 그림이라 저작권 때문에 저장소에 올리지 않음. 원문은 해당 출처를 참조.

그림. Short와 Pont(2005)의 Fig. 1, HIL 시뮬레이션의 원리

Short와 Pont(2005)는 HIL 시뮬레이션의 원리를 시험 대상 임베디드 시스템의 출력이 표본화되어 시뮬레이션의 입력으로 들어가고, 동적 모델이 계산되며(보통 실시간), 그 출력이 다시 시험 대상 시스템에 입력되어 루프가 닫히는 것으로 설명하였음(p. 226). 이들은 안전이 중요한 시스템은 자연 환경에서 충분히 시험하는 것이 부적절하거나 비윤리적이거나 불가능한 경우가 많다고 보았고, 환경을 HIL로 대신하면 안전을 해치지 않고 초기 평가를 할 수 있다고 하였음.

Isermann 외(1998)는 HIL을 실물 부품을 실시간으로 시뮬레이션되는 부품과 함께 운전하는 것으로 특징지었음. 제어 하드웨어와 소프트웨어는 양산 제품과 같은 실물이고, 액추에이터, 프로세스, 센서는 시뮬레이션일 수도 실물일 수도 있다고 하였음(Sec. 2.1). 같은 절에서 이들은 제어 시제품 제작(control prototyping), HIL, 프로세스까지 시뮬레이션으로 두는 제어 시뮬레이션을 구분하였음(Fig. 2). Nguyen 외(2020)는 전력 계통 분야의 장에서 HIL을 실제 하드웨어를 실시간 시뮬레이터에 연결하는 것으로 설명하고, 오류가 나기 쉽거나 불완전한 모델을 실물로 바꿀 수 있다고 하였음(p. 52).

이들 자료를 종합하면, HIL은 시험 대상의 일부를 실물 하드웨어로 두고 나머지 동작 환경을 주로 실시간 시뮬레이션으로 구현하여, 실물과 모델이 입력과 출력을 주고받는 폐루프 시험 방식으로 정리할 수 있음. 엔진 제어, 자동차 임베디드 제어, 전력 계통의 사례는 적용 분야가 달라도 이러한 연결 원리를 공통으로 보여 줌.

## 2. HIL 시스템의 구성

> [그림 생략] 그림. Isermann 외(1998)의 Fig. 3, 액추에이터·프로세스·센서를 실물 또는 시뮬레이션으로 구성하는 HIL의 혼합 구조 — 논문·데이터시트의 그림이라 저작권 때문에 저장소에 올리지 않음. 원문은 해당 출처를 참조.

그림. Isermann 외(1998)의 Fig. 3, 액추에이터·프로세스·센서를 실물 또는 시뮬레이션으로 구성하는 HIL의 혼합 구조

Isermann 외(1998)는 HIL에서 제어 장치는 실물로 두고 액추에이터, 프로세스, 센서를 실물로 둘지 시뮬레이션으로 둘지에 따라 구조가 달라진다고 하였음(Sec. 2.1, Fig. 3, Table 1). 센서를 실물로 두고 프로세스를 시뮬레이션하는 경우에는 센서가 받을 물리적 입력이 없으므로 이를 인위적으로 만들어 주어야 하며 상당한 노력이 든다고 하였음.

Short와 Pont(2005)의 시험대는 표준 PC에 병렬 포트 입출력을 붙인 구성이었고, 가상 센서·액추에이터 인터페이스에 동특성, 정확도, 잡음 모델을 넣어 1 ms마다 갱신하였음. Bullock 외(2004)는 교통 신호 제어기를 대상으로 제어기 인터페이스 장치, 소프트웨어 인터페이스 모듈, 미시적 교통 시뮬레이션 엔진으로 HIL을 구성하였음(Sec. 4, pp. 76–78). Nguyen 외(2020)는 일반적인 HIL 구성을 실시간 시뮬레이터, 시험 대상 하드웨어, 전력 인터페이스(PHIL에만 해당)로 보였고, 제어기 HIL(CHIL)은 A/D와 D/A 변환 또는 디지털 인터페이스로 연결한다고 하였음(pp. 52–53).

이들 구성을 종합하면, HIL은 실시간 시뮬레이터, 시험 대상 실물 하드웨어, 둘 사이의 인터페이스를 중심으로 이해할 수 있음. 인터페이스의 형태는 시험 대상과 주고받는 신호에 따라 달라짐. 제어기 HIL(CHIL)은 아날로그·디지털 신호나 통신 인터페이스로 연결하고, 전력 HIL(PHIL)은 실제 전력을 주고받기 위한 전력 인터페이스를 포함함(Nguyen et al., 2020).

## 3. HIL의 장점

Isermann 외(1998)는 HIL의 장점으로 일곱 가지를 들었음. 실제 프로세스 없이 설계와 시험을 할 수 있어 프로세스 현장을 실험실로 옮기는 효과가 있고, 극단적인 환경 조건을 실험실에서 시험할 수 있다고 하였음. 액추에이터, 센서, 컴퓨터의 고장이 미치는 영향을 시험할 수 있고, 극단적이거나 위험한 조건을 다룰 수 있으며, 실험을 재현할 수 있다고 하였음. 서로 다른 사람-기계 인터페이스와 훈련에 쓸 수 있고, 비용과 개발 시간을 줄인다고도 하였음(Sec. 2.1).

Nguyen 외(2020)는 시뮬레이션이 빠르고 유연하며 장비를 망가뜨릴 위험이 없는 반면 실제 하드웨어 시험은 시간과 투자가 더 들고 구성 변경이 어렵지만 실제 거동을 잡아낸다고 하였음(p. 51). HIL은 결함이 있거나 극단적인 조건에서 확장 가능한 시험을 할 수 있다고 하였음(p. 52). Short와 Pont(2005)의 안전 관련 동기는 1절에 적은 바와 같음. 이 장점들은 저자들이 서술한 것이며, 비용이나 기간을 수치로 비교한 결과는 읽은 자료에서 확인되지 않았음.

## 4. ISO 26262과 HIL

ISO 26262-4:2018은 모페드(moped)를 제외한 양산 도로차량의 안전 관련 전기·전자 시스템에 대한 시스템 수준 제품 개발을 다루는 규격으로, 범위에 아이템 통합 및 시험과 안전 타당성 확인(safety validation)이 들어 있음. ISO 26262-6:2018은 소프트웨어 수준 제품 개발을 다룸. 두 규격 모두 2018년 12월에 발행된 2판이며 ISO 카탈로그에는 개정 예정으로 표시되어 있음(International Organization for Standardization [ISO], 2018a, 2018b). 규격 원문(2판, 2018-12)은 사용자가 제공한 4부와 6부 PDF로 읽었으며, 아래 조항 번호와 쪽수는 이 PDF의 인쇄된 쪽 번호 기준임.

ISO 26262-6:2018은 임베디드 소프트웨어 시험(11절)에서 소프트웨어 안전 요구사항을 대상 환경에서 충족하는지 검증하려면 Table 13의 시험 환경에서 시험해야 한다고 규정함(11.4.1, p. 29). Table 13은 HIL을 ASIL A–D 모두 '++'(해당 ASIL에 강력 권고), ECU 네트워크 환경도 A–D 모두 '++'로 적었고, 차량은 A·B에서 '+'(권고), C·D에서 '++'로 적었음. '++'와 '+'의 뜻은 4.3절에 정의되어 있음(p. 3). 같은 절의 Table 14는 시험 방법으로 요구사항 기반 시험(A–D '++')과 고장 주입 시험(A–C '+', D '++')을, Table 15는 시험 사례 도출 방법을 나열함(11.4.2, 11.4.3, p. 29).

소프트웨어 유닛 시험(9.4.5, p. 23)과 소프트웨어 통합 시험(10.4.7, pp. 27–28)에 대해서는, 시험 환경이 대상 환경을 고려하여 목적 달성에 적합해야 하고, 대상 환경에서 시험하지 않으면 소스·목적 코드의 차이와 시험 환경·대상 환경의 차이를 분석하여 이후 단계의 대상 환경 시험에서 추가 시험을 정해야 한다고 규정함. 두 조항의 NOTE는 시험 환경의 예로 모델 인 더 루프, 소프트웨어 인 더 루프, 프로세서 인 더 루프, 하드웨어 인 더 루프를 들었음. 부속서 B.3.5(정보 제공용, p. 39)는 HIL로 폐루프 제어기를 시험하려면 환경을 모사하는 플랜트 모델이 필요하다고 하면서, 검증에 쓰는 모델의 적합성 근거가 없으면 관련 결과의 타당성이 의심스러울 수 있고 부적절한 플랜트 모델은 잘못된 시험 결과로 이어질 수 있다고 하였음(ISO, 2018b).

ISO 26262-4:2018의 텍스트에서는 'hardware-in-the-loop'라는 표현이 검색되지 않았음. 시스템 아키텍처 설계의 검증 방법 Table 2는 시뮬레이션과 시스템 시제품 제작 및 차량 시험을 각각 ASIL A·B에서 '+', C·D에서 '++'로 적었음(6.4.9.2, p. 14). 하드웨어-소프트웨어 통합 시험(7.4.2)에서는 양산 의도의 하드웨어와 소프트웨어를 쓰는 것이 바람직하다고 하였고(NOTE, p. 17), Table 4에 요구사항 기반 시험, 고장 주입 시험, 백투백 시험을, Table 5에 백투백 시험과 성능 시험을 나열하면서 성능 시험은 작업 스케줄링, 타이밍 등을 검증할 수 있다고 주석을 달았음(p. 18). 안전 목표에 대한 타당성 확인은 차량 수준의 대표적인 맥락에서 수행해야 한다고 규정함(8.4.1.1, p. 25)(ISO, 2018a).

Lee 외(2018)는 2011년판(1판)을 기준으로 ASIL C와 D에서 소프트웨어 안전 요구사항 검증에 HiL이 강력 권고(highly recommended)된다고 인용하고(ISO 26262-6:2011, Clause 11.4.2), 소프트웨어 안전 요구사항의 시험은 대상 하드웨어에서 수행해야 한다고 인용하였음(Clause 11.4.3). 이들은 HiL이 ECU 소프트웨어 시험의 표준 요소가 되었고 특히 고장 주입에 편리하다고 하였으며, 규격이 시험 사례를 도출하는 방법은 자세히 주지 않는다고 보고 2단계 작업 흐름을 제안하였음. 2018년판에서는 HIL이 11.4.1의 Table 13에 있고 ASIL A–D 모두 '++'이며, 11.4.2와 11.4.3은 각각 시험 방법(Table 14)과 시험 사례 도출 방법(Table 15)에 해당함. 따라서 Lee 외가 인용한 조항 번호와 ASIL 범위는 2018년판과 다름. 2011년판 원문은 확인하지 않았으므로 Lee 외의 인용이 2011년판과 일치하는지, 2011년판에 Table 15에 해당하는 표가 있었는지는 확인되지 않았고, 이 문서는 2018년판 원문을 기준으로 삼음.

> [그림 생략] 그림. Lee 외(2018)의 Fig. 7, 신호 수준 HiL 플랫폼의 시스템 구조 — 논문·데이터시트의 그림이라 저작권 때문에 저장소에 올리지 않음. 원문은 해당 출처를 참조.

그림. Lee 외(2018)의 Fig. 7, 신호 수준 HiL 플랫폼의 시스템 구조

Lee 외(2018)의 시험 플랫폼은 Opal-RT 실시간 시뮬레이터에 제어 보드를 연결하고, MATLAB/Simulink의 가상 요소(영구자석 동기 전동기 등)와 CAN 또는 하드와이어로 주고받는 구성이었음. 12 V 미만의 약한 신호만 다루고 고전압 전력은 시뮬레이션하므로 스스로 신호 수준(signal-level) HiL이라 불렀음. 이 문서는 HIL이 쓰이는 맥락을 정리한 것이며 ISO 26262이 본 프로젝트에 적용되는지는 판단하지 않음.

## 5. HIL의 한계

Bullock 외(2004)는 교통 신호 제어기를 연결한 실시간 HIL의 요건으로 시뮬레이션 시간과 실제 시간의 동기화, 일정한 스텝 간격, 각 스텝의 계산 기한 준수를 제시하였음. 모델 계산과 인터페이스의 입출력 처리는 정해진 한 주기 P 안에 완료되어야 함. 즉, 계산이 빨리 끝나더라도 시뮬레이션의 시간 진행은 실제 하드웨어의 시간과 맞추어야 하며, 처리가 주기를 초과하면 이 논문에서 다루는 실시간 HIL의 조건을 충족할 수 없음(Sec. 6, pp. 79–80, Fig. 3). 같은 논문은 HIL이 계산의 정확성과 시험 대상 장비와의 상호작용 시점 모두에 정확성이 달린 실시간 시스템이라고 하였음(Sec. 10, p. 86).

Isermann 외(1998)는 빠른 프로세스를 실시간으로 시뮬레이션하는 데 한계가 있다고 하였고, 그 요인으로 알고리즘의 병렬화, 적분 방법, 강성(stiffness)을 들었음. 이 논문이 제시한 제어기 샘플링 주기는 1–10 ms, 프로세스 시뮬레이션 주기는 0.5–10 ms였음. 이 수치는 엔진 제어 사례의 것이며 초음파 센서에 그대로 적용할 수는 없음. Short와 Pont(2005)는 어떤 변수를 시뮬레이션하는지, 동적 모델과 계산의 정확도가 어떠한지를 검증하는 것이 필수적이며 시점이 매우 중요하다고 하였고, 아날로그 신호는 시험 대상 시스템보다 높은 분해능으로 표본화해야 한다고 하였음(Sec. II.E, p. 227). Nguyen 외(2020)는 HIL의 과제로 실시간 요건을 만족하는 인터페이스를 꼽고, 지연과 안정성을 평가해야 하며 하드웨어와 시뮬레이션의 인터페이스와 시간 지연 때문에 HIL 실험은 안정성과 정확도에 민감하다고 하였음(p. 53).

센서 HIL 시험대에서는 Zhu 외(2025)가 장시간 시험에서 시험대에 열이 쌓이는 것을 문제로 적었고(p. 17060), 여러 레이더 사이의 신호 간섭은 시뮬레이션하지 못하는 한계도 밝혔음. 이 자료들에서 HIL의 구축 비용이나 기간을 수치로 제시한 것은 확인되지 않았음.

## 6. 초음파 센서에 적용된 HIL

> [그림 생략] 그림. Zhu 외(2025)의 Fig. 5, 초음파 레이더 인 더 루프 시험대의 구조 (1/2) — 논문·데이터시트의 그림이라 저작권 때문에 저장소에 올리지 않음. 원문은 해당 출처를 참조.

그림. Zhu 외(2025)의 Fig. 5, 초음파 레이더 인 더 루프 시험대의 구조 (1/2)

> [그림 생략] 그림. 위 그림의 이어지는 아래쪽 (2/2) — 논문·데이터시트의 그림이라 저작권 때문에 저장소에 올리지 않음. 원문은 해당 출처를 참조.

그림. 위 그림의 이어지는 아래쪽 (2/2)

Zhu 외(2025)는 자동 주차 시스템용 초음파 레이더의 고충실도 인 더 루프 시험대를 만들고 검증하였음. 서론에서 이들은 자신들이 검토한 기존 모델 인 더 루프(MIL) 모델이 실외 조건에서 실제 초음파 성능을 충분히 예측하지 못하였다고 설명하였음. 또한 데이터 기반 모델의 비용과, 가우시안 잡음을 추가하는 방식만으로 시뮬레이션과 실제의 차이를 충분히 줄이기 어려운 점을 연구의 문제로 제시하였음. 저자들은 기존 초음파 HIL 연구가 에코 시뮬레이션에 집중하면서 대기의 영향을 충분히 반영하지 못하였다고 보았음(pp. 17055–17056). 이는 저자들이 검토한 기존 모델과 구현에 관한 문제 제기이며, MIL이나 HIL에서 기상 영향을 모델링할 수 없다는 뜻은 아님. 이들의 모델은 온도, 습도, 기압이 음속과 감쇠에 미치는 영향을 포함함.

시험대의 구조는 시나리오 소프트웨어가 이상적인 거리를 계산하고, 레이더 모델이 기상 조건에 맞게 보정하여 CAN으로 에코 시뮬레이터에 보내는 것이었음. 에코 시뮬레이터(FPGA 디지털 지연선, DAC, 증폭기)가 트랜스듀서를 구동하면 무반향실 안의 실제 레이더가 에코를 받고, ECU가 거리를 계산해 주차 알고리즘에 보내며 차량 동역학 모델이 갱신됨(Fig. 5, p. 17059). 하드웨어는 PXIe-8880과 프로브 쌍 6개씩을 가진 무반향실 2개였음. 검증에서 탐지 거리 모델의 오차율은 세 가지 기상 조건에서 4.20%, 2.84%, 6.13%였고, 가장 가까운 탐지 거리는 링잉 때문에 0.22 m였음(pp. 17058–17061). 5개 조건의 충실도 지표 E_s와 관련하여 기존 정리에는 시뮬레이션 소프트웨어 0.604%, HIL 시험대 4.388%의 향상 수치가 기록되어 있음. 다만 이 수치는 지표의 정의, 비교 기준, 값의 증가·감소가 의미하는 바, 상대 변화율(%)과 퍼센트포인트 차이의 구분을 원문 수식·표와 추가 대조할 필요가 있음. 따라서 현재는 추가 확인이 필요한 수치로 보존하며, HIL의 일반적인 정확도 향상률이나 본 프로젝트의 예상 성능으로 해석하지 않음.

> [그림 생략] 그림. Ma 외(2023)의 Fig. 5, 단선(One Wire) 입출력 에코 시뮬레이터 — 논문·데이터시트의 그림이라 저작권 때문에 저장소에 올리지 않음. 원문은 해당 출처를 참조.

그림. Ma 외(2023)의 Fig. 5, 단선(One Wire) 입출력 에코 시뮬레이터

Ma 외(2023)는 초음파 에코 시뮬레이터에 기반한 자동 주차 HIL 가상 시뮬레이션 시스템을 다루었으나, 논문의 중심은 주차 경로 계획이고 HIL에 관한 서술은 많지 않음. 플랫폼은 프로브 12개, 트랜스듀서 12개, DSI3 유닛으로 구성되고, 프로브와 트랜스듀서 전용 프로브를 밀봉 링으로 잇는다고 하였음. 40–58 kHz의 디지털 초음파 송수신 칩 E524.03을 쓰며, 프로세서가 CAN으로 설정 거리를 받고 제어기의 발파 명령을 받으면 거리에 해당하는 시간만큼 지연한 뒤 에코로 응답하였음. 프로브와 트랜스듀서를 거치지 않고 제어기에 직접(DSI3) 연결할 수도 있다고 하였음(pp. 1390–1391). 정량적인 정확도는 논문에서 확인되지 않았고, 초록은 가상 장면에서 정확한 장애물 정보를 얻어 주차 과제를 완수했다고만 적었음.

두 논문 모두 차량 밖의 물체를 감지하는 주차용 초음파 센서가 대상이며, 읽은 범위에서 차실 안의 점유 감지나 HC-SR04 같은 저가 모듈을 HIL로 시험한 사례는 확인되지 않았음.

## 7. 결론

HIL은 일부를 실물로 두고 나머지를 실시간 모델로 대신하여 루프를 닫는 시험 방식임(Isermann et al., 1998; Short & Pont, 2005). 장점으로는 실제 프로세스 없이 시험하고 극단적이거나 위험한 조건과 고장을 재현할 수 있다는 점이 제시되었고(Isermann et al., 1998; Nguyen et al., 2020), 한계로는 실시간 요건, 인터페이스 지연, 모델의 정확도와 시점이 확인되었음(Bullock et al., 2004; Nguyen et al., 2020; Short & Pont, 2005). 자동차에서는 ECU 소프트웨어 시험에 쓰임(Lee et al., 2018). ISO 26262-6:2018은 임베디드 소프트웨어의 시험 환경으로 HIL을 ASIL A–D 모두 '++'로 적었고(Table 13), 대상 환경이 아닌 곳에서 시험하면 차이를 분석하여 대상 환경에서의 추가 시험을 정하도록 규정함(9.4.5, 10.4.7)(ISO, 2018b).

초음파 HIL의 구성은 시험 대상과 신호를 입력하는 위치에 따라 달라짐. 실제 초음파 센서의 음향 응답까지 시험하는 Zhu 외(2025)의 구성에서는 트랜스듀서와 에코 시뮬레이터가 센서에 입력할 음향 에코를 생성하였음. Ma 외(2023)는 프로브·트랜스듀서를 이용한 구성과 함께, 이를 거치지 않고 DSI3로 제어기에 직접 연결하는 방식도 제시하였음. 따라서 음향 에코를 생성하는 장비가 필요한 구성과 제어기에 전기·통신 신호를 직접 입력하는 구성을 구분해야 함. 두 사례는 초음파 신호를 모사하는 방법과 실물 하드웨어의 연결 위치를 이해하고, 시험하려는 기능에 맞는 HIL 구성을 검토하는 데 활용할 수 있음. 주차용 초음파 센서에서 시뮬레이션과 실제 센서의 충실도 차이는 HIL 시험대를 개발한 동기로 제시되었음(Zhu et al., 2025). 본 프로젝트는 하드웨어 없이 SIL로 검증하기로 하였으므로, 이 문서의 내용은 SIL과 비교하는 4단계 비교표에서 다시 쓰고, 시뮬레이션과 실제 센서의 차이는 7단계 SIL의 한계에서 다시 다룸.

## 참고문헌

Bullock, D., Johnson, B., Wells, R. B., Kyte, M., & Li, Z. (2004). Hardware-in-the-loop simulation. *Transportation Research Part C: Emerging Technologies, 12*(1), 73–89. [https://doi.org/10.1016/j.trc.2002.10.002](https://doi.org/10.1016/j.trc.2002.10.002)

International Organization for Standardization. (2018a). *Road vehicles — Functional safety — Part 4: Product development at the system level* (ISO Standard No. 26262-4:2018, 2nd ed.). [https://www.iso.org/standard/68386.html](https://www.iso.org/standard/68386.html)

International Organization for Standardization. (2018b). *Road vehicles — Functional safety — Part 6: Product development at the software level* (ISO Standard No. 26262-6:2018, 2nd ed.). [https://www.iso.org/standard/68388.html](https://www.iso.org/standard/68388.html)

Isermann, R., Schaffnit, J., & Sinsel, S. (1998). Hardware-in-the-loop simulation for the design and testing of engine-control systems. *IFAC Algorithms and Architectures for Real-Time Control*, Cancun, Mexico.

Lee, C.-S., Huang, Y.-H., & Lan, I.-W. (2018). Hardware-in-the-loop test case specification for verification of software safety requirements in the context of ISO 26262. *2018 International Conference of Electrical and Electronic Technologies for Automotive*. IEEE.

Ma, W., Wang, Q., Wang, Y., Leng, X., Luo, T., & Sun, B. (2023). Research on the autonomous parking strategy based on the ultrasonic echo simulator. *2023 IEEE International Conference on Sensors, Electronics and Computer Engineering (ICSECE)* (pp. 1388–1393). IEEE. [https://doi.org/10.1109/ICSECE58870.2023.10263460](https://doi.org/10.1109/ICSECE58870.2023.10263460)

Nguyen, V. H., Tran, Q. T., Guillo-Sansano, E., Kotsampopoulos, P., Gavriluta, C., Lauss, G., Strasser, T. I., Jensen, T. V., Heussen, K., Gehrke, O., Besanger, Y., Nguyen, T. L., Syed, M. H., Brandl, R., & Arnold, G. (2020). Hardware-in-the-loop assessment methods. In T. I. Strasser, E. C. W. de Jong, & M. Sosnina (Eds.), *European guide to power system testing* (pp. 51–66). Springer. [https://doi.org/10.1007/978-3-030-42274-5_4](https://doi.org/10.1007/978-3-030-42274-5_4)

Short, M., & Pont, M. J. (2005). Hardware in the loop simulation of embedded automotive control systems. *Proceedings of the 8th International IEEE Conference on Intelligent Transportation Systems* (pp. 226–231). IEEE.

Zhu, B., Cao, X., Zhang, P., Zhao, J., Han, J., & Tang, R. (2025). High-fidelity ultrasonic radar in-the-loop accelerated test for automatic parking systems. *IEEE Transactions on Intelligent Transportation Systems, 26*(10), 17055–17067. [https://doi.org/10.1109/TITS.2025.3574505](https://doi.org/10.1109/TITS.2025.3574505)