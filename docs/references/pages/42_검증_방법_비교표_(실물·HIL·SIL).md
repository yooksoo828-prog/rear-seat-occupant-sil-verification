# 검증 방법 비교표 (실물·HIL·SIL)

> **이전 문서** — 원본: Notion "검증 방법 비교표 (실물·HIL·SIL)"(문서 목록 데이터베이스, 마지막 수정 2026-11-11). Notion에서 2026-11-24에 내보내 같은 날 이 저장소로 옮김.
> 이전 시 바꾼 것: 파일 이름 정리, 비공개 Notion 링크 제거(근거 출처는 제목만 남김), 논문·데이터시트에서 가져온 그림은 저작권 때문에 생략(캡션만 유지). 본문 내용은 바꾸지 않음.
> 팀원 실명은 원본에 없었다. 이 문서의 수치·해석은 Notion 시점(2026-11-11)의 것이며 이후 결정(2026-11-13 등)은 `docs/29119/`의 문서가 기준이다.


V모델 순서: 42
근거 출처: Short & Pont (2005) Hardware in the loop simulation of embedded automotive control systems, Isermann, Schaffnit & Sinsel (1998) Hardware-in-the-loop simulation for the design and testing of engine-control systems, Bullock et al. (2004) Hardware-in-the-loop simulation, Nguyen et al. (2020) Hardware-in-the-loop assessment methods (European Guide to Power System Testing, ch. 4), ISO 26262-4:2018 Product development at the system level (ISO 카탈로그 페이지), ISO 26262-6:2018 Product development at the software level (ISO 카탈로그 페이지), Zhu 외(2025) High-Fidelity Ultrasonic Radar In-the-Loop Accelerated Test for Automatic Parking Systems, Ma et al. (2023) Research on the autonomous parking strategy based on the ultrasonic echo simulator, Shylla et al. (2023) Model in loop (MIL), software in loop (SIL) and hardware in loop (HIL) testing in MBD, Kim, D.-J., Kim, Y.-C., Jung, D.-H., & Kim, M.-S. (2024). 차량용 3D 초음파 센서 평가를 위한 SILS에 관한 연구, Fei, Z., Andersson, M., & Tingberg, A. (2024). Correlation of software-in-the-loop simulation with physical testing for autonomous driving, Won, J., Seok, J., Lee, S., & Yoo, J. (2025). 자율주행 차량 시스템 개발을 위한 Software-in-the-Loop Simulation 구현 방법론, Kim, J., & Choi, Y. (2024). SIL검증과 HIL검증 비교를 통한 SIL검증 유효성 증대 방안 연구 (Study on how to increase SIL test effectiveness by comparing SIL test to HIL test), Jeong, S., Kwak, Y., & Lee, W. J. (2016). Software-in-the-loop simulation for early-stage testing of AUTOSAR software component
단계: 4 검증 방법론
마지막 수정일: 2026년 11월 11일 오후 1:29
상태: 초안

<aside>
📌

실물 시험, HIL, SIL을 같은 항목으로 나란히 놓고 비교한 표임. 표의 내용은 지금까지 읽은 논문과 ISO 26262 원문에 직접 서술된 것만 넣었고, SIL 칸은 Shylla 외(2023), Won 외(2025), J. Kim과 Choi(2024), Fei 외(2024) 등 SIL을 직접 다룬 논문과 ISO 26262-6 원문을 근거로 했고, 직접 근거가 없는 칸은 '확인되지 않음'으로 남겼음. SIL 문서(4단계)의 내용과 같은 근거를 써서 정리했음. (2026-11-11, 초안)

</aside>

## 1. 비교표

표의 각 칸에는 근거가 된 자료를 적었음. 자료가 시뮬레이션 일반이나 다른 대상에 대해 쓴 내용을 SIL에 옮겨 적용한 칸은 '(해석)'으로 표시했음. 세 방법의 비용이나 기간을 수치로 비교한 자료는 읽은 범위에서 확인되지 않았음.

| 항목 | 실물 시험 | HIL | SIL |
| --- | --- | --- | --- |
| 실물로 두는 범위 | 시스템 시제품과 차량 단위의 시험이 방법과 환경으로 올라 있음(ISO, 2018a, 6.4.9.2 Table 2; ISO, 2018b, 11.4.1 Table 13). | 제어 하드웨어와 소프트웨어는 양산과 같은 실물이고, 액추에이터, 프로세스, 센서는 실물 또는 시뮬레이션임(Isermann et al., 1998, Sec. 2.1). | MIL 이후 모델에서 생성한 코드를 시뮬레이션 환경에서 가상으로 실행함(Shylla et al., 2023, p. 2, Sec. II.B). 논문의 사례에서는 코드를 시뮬레이션된 PLC 하드웨어에서 실행했음(p. 5, Fig. 4). Won 외는 vECU를 호스트에서 컴파일해 실행하고 하드웨어 모델링은 하지 않는 것으로 정리하였음(Won et al., 2025, p. 970, Table 2). 6부는 SIL을 시험 환경의 예로 열거할 뿐 정의하지 않음(ISO, 2018b, 9.4.5 NOTE 3). |
| 시간 요건 | 읽은 자료에서 확인되지 않음. | 시뮬레이션이 실시간보다 느리면 HIL은 불가능하고, 시뮬레이션과 인터페이스 작업이 한 주기 안에 끝나야 함(Bullock et al., 2004, Sec. 6, pp. 79–80). 지연과 안정성을 평가해야 함(Nguyen et al., 2020, p. 53). | 시뮬레이션 모드의 주기는 보통 100 ms로 설정하며 더 짧은 주기는 불가능할 수 있다고 함(Shylla et al., 2023, p. 5). 사례 한 편의 서술이며 일반화는 확인되지 않음. J. Kim과 Choi는 SIL이 실시간이 아닌 시뮬레이션 시간을 써서 검증 시간을 줄일 수 있다고 하였으나, FMU가 Windows 시간으로 동작하면 PC 상태에 따라 결과가 달랐음(2024, pp. 886, 888). |
| 장점 | 실제 거동을 잡아냄(Nguyen et al., 2020, p. 51). | 실제 프로세스 없이 시험하고, 극단적이거나 위험한 조건과 부품 고장의 영향을 시험하며, 실험을 재현할 수 있음(Isermann et al., 1998, Sec. 2.1). 결함과 극단 조건에서 확장 가능한 시험을 할 수 있음(Nguyen et al., 2020, p. 52). | 가상 모델 시험으로 하드웨어 없이 또는 최소 하드웨어로 검증하고 결함을 일찍 찾을 수 있다고 함(Shylla et al., 2023, pp. 1, 6). 이는 모델 기반 설계의 가상 시험 전반에 대한 서술이고 수치 비교는 없음. ISO 26262-6 부속서는 모델 기반 개발에서 MIL/SIL 시험으로 소프트웨어 유닛을 검증할 수 있다고 함(ISO, 2018b, B.3.3, p. 38). J. Kim과 Choi는 SIL이 HIL보다 이른 시기에 오류를 검증할 수 있고 환경 구축 비용이 저렴하다고 서술했으나 수치 비교는 없음(2024, pp. 885–886). Jeong 외는 실차·HIL과 달리 ECU와 시스템 구성 전에 시험할 수 있다고 했음(2016, pp. 59–60).  |
| 한계 | 시간과 투자가 더 들고 구성을 바꾸기 어려움(Nguyen et al., 2020, p. 51). 안전이 중요한 시스템은 자연 환경에서 충분히 시험하는 것이 부적절하거나 비윤리적이거나 불가능한 경우가 많음(Short & Pont, 2005, p. 226). | 실시간 요건(Bullock et al., 2004), 인터페이스 지연에 따른 안정성과 정확도 민감성(Nguyen et al., 2020, p. 53), 모델 정확도와 시점의 검증 필요(Short & Pont, 2005, p. 227), 센서 HIL 시험대의 장시간 열 축적(Zhu et al., 2025, p. 17060). Zhu 외는 HIL 시험의 비용과 시간이 높다고 초록에 적고 시험 횟수를 줄이는 가속 시험을 제안함(수치 비교는 확인되지 않았음). | 하드웨어의 영향을 받는 성능·신뢰성은 SIL로 시험할 수 없고 vECU는 실제 ECU와 차이가 있을 수 있으며 PC 상태에 따라 결과가 달라질 수 있음(J. Kim & Choi, 2024, pp. 886–887, 890). MIL 대비 SIL은 FMU를 세분할수록 오차가 커짐(Won et al., 2025, pp. 975–976). 센서 모델이 이상적(ideal)이어서 시험장 결과와 맞추려면 보정과 상관 검증이 필요했음(Fei et al., 2024, pp. 2050–2051, 2054). 대상 환경이 아닌 곳에서 시험하면 소스·목적 코드와 환경의 차이를 분석해 대상 환경에서 추가 시험을 정해야 함(ISO, 2018b, 9.4.5, 10.4.7). 검증에 쓰는 모델은 적합성 근거가 없으면 결과의 타당성이 의심스러울 수 있음(ISO, 2018b, 부속서 B.3.5, 정보 제공용). 이 문장은 모델 일반에 대한 것이므로 SIL에 적용하는 것은 해석임. |
| ISO 26262-6 Table 13의 위치 | 차량: ASIL A·B '+', C·D '++'(ISO, 2018b, 11.4.1, p. 29). | HIL: ASIL A–D 모두 '++'(ISO, 2018b, 11.4.1, p. 29). | Table 13에 없음. 9.4.5와 10.4.7의 NOTE에 시험 환경의 예로만 열거됨(ISO, 2018b). |
| 초음파 센서에 적용 | Zhu 외는 현장 운영 시험(FOT)이 비싸고 비효율적이라고 초록에 적었음(Zhu et al., 2025). | 센서를 실물로 두고 프로세스를 시뮬레이션하면 센서가 받을 입력을 인위적으로 만들어야 함(Isermann et al., 1998, Sec. 2.1). 초음파 센서에서는 에코 시뮬레이터가 이 역할을 함(Zhu et al., 2025, p. 17059; Ma et al., 2023, pp. 1390–1391). | 3D 초음파 센서를 라이다 시야각을 바꿔 모사한 SIL 평가 환경이 한 건 있으나 정량 정확도는 초록에 없음(D.-J. Kim et al., 2024, p. 539). 차실 안 점유 감지나 HC-SR04 같은 저가 모듈의 SIL 사례는 공식 자료에서 확인되지 않음. Zhu 외는 충실도 지표에서 시뮬레이션 소프트웨어 모델이 0.604%, HIL 시험대가 4.388% 높였다고 서술함(2025, pp. 17058–17061). 이 '시뮬레이션 소프트웨어'가 SIL인지는 자료에서 확인되지 않으며, 지표의 정의는 따로 검증하지 않았음. |

## 2. 결론

세 방법은 실물로 두는 범위가 다름. 실물 시험은 시스템 시제품이나 차량을 쓰고, HIL은 제어 장치를 실물로 두면서 나머지를 실시간 시뮬레이션으로 대신하며(Isermann et al., 1998), SIL은 모델에서 생성한 코드를 시뮬레이션 환경에서 가상으로 실행하는 것으로 설명되었음(Shylla et al., 2023). 규격 쪽에서는 ISO 26262-6:2018의 Table 13이 HIL, ECU 네트워크 환경, 차량을 시험 환경으로 적었고 SIL은 적지 않았으며, SIL은 NOTE에서 시험 환경의 예로만 나옴(ISO, 2018b). 대상 환경이 아닌 곳에서 시험한 경우 차이를 분석해 대상 환경 시험을 추가하도록 한 조항(9.4.5, 10.4.7)은 SIL의 한계를 정리할 때 근거가 됨. 이 조항을 근거로 SIL만으로 규격이 요구하는 시험을 대신하기 어렵다고 읽는 것은 해석이며, 7단계 SIL의 한계에서 다시 다룸.

초음파 센서에서는 HIL이 에코를 만들어 주는 전용 장비를 요구하는 것으로 확인되었고(Zhu et al., 2025; Ma et al., 2023), SIL 쪽에서는 SIL을 직접 다룬 논문들이 정의·구성·장점·한계를 서술하였으나(Shylla et al., 2023; Won et al., 2025; J. Kim & Choi, 2024; Fei et al., 2024), 대부분 제어기 소프트웨어나 자율주행 시스템을 대상으로 했음. HIL과 결과를 직접 비교한 자료는 상용차 VCU의 379개 시험 항목에서 377개가 일치했다는 한 편이며(J. Kim & Choi, 2024), 센서를 모델로 대신한 시험의 일치율은 아님. 초음파 센서에 적용한 SIL은 3D 초음파 센서를 라이다로 모사한 평가 환경 한 건만 확인되었고 정량 결과는 초록에 없음(D.-J. Kim et al., 2024). 이 표의 SIL 칸은 위 논문들과 규격 서술에 한정됨.

## 참고문헌

Bullock, D., Johnson, B., Wells, R. B., Kyte, M., & Li, Z. (2004). Hardware-in-the-loop simulation. *Transportation Research Part C: Emerging Technologies, 12*(1), 73–89. [https://doi.org/10.1016/j.trc.2002.10.002](https://doi.org/10.1016/j.trc.2002.10.002)

Fei, Z., Andersson, M., & Tingberg, A. (2024). Correlation of software-in-the-loop simulation with physical testing for autonomous driving. *2024 IEEE 27th International Conference on Intelligent Transportation Systems (ITSC)* (pp. 2050–2057). IEEE. [https://doi.org/10.1109/ITSC58415.2024.10919543](https://doi.org/10.1109/ITSC58415.2024.10919543)

International Organization for Standardization. (2018a). *Road vehicles — Functional safety — Part 4: Product development at the system level* (ISO Standard No. 26262-4:2018, 2nd ed.). [https://www.iso.org/standard/68386.html](https://www.iso.org/standard/68386.html)

International Organization for Standardization. (2018b). *Road vehicles — Functional safety — Part 6: Product development at the software level* (ISO Standard No. 26262-6:2018, 2nd ed.). [https://www.iso.org/standard/68388.html](https://www.iso.org/standard/68388.html)

Isermann, R., Schaffnit, J., & Sinsel, S. (1998). Hardware-in-the-loop simulation for the design and testing of engine-control systems. *IFAC Algorithms and Architectures for Real-Time Control*, Cancun, Mexico.

Jeong, S., Kwak, Y., & Lee, W. J. (2016). Software-in-the-loop simulation for early-stage testing of AUTOSAR software component. *2016 Eighth International Conference on Ubiquitous and Future Networks (ICUFN)* (pp. 59–63). IEEE.

Kim, D.-J., Kim, Y.-C., Jung, D.-H., & Kim, M.-S. (2024). 차량용 3D 초음파 센서 평가를 위한 SILS에 관한 연구 [A study on software in loop simulation for evaluation of automotive 3D ultrasonic sensor]. *2024년 한국산학기술학회 춘계 학술발표논문집* (p. 539). 한국산학기술학회.

Kim, J., & Choi, Y. (2024). SIL검증과 HIL검증 비교를 통한 SIL검증 유효성 증대 방안 연구 [Study on how to increase SIL test effectiveness by comparing SIL test to HIL test]. *2024 한국자동차공학회 추계학술대회* (pp. 885–890). 한국자동차공학회.

Ma, W., Wang, Q., Wang, Y., Leng, X., Luo, T., & Sun, B. (2023). Research on the autonomous parking strategy based on the ultrasonic echo simulator. *2023 IEEE International Conference on Sensors, Electronics and Computer Engineering (ICSECE)* (pp. 1388–1393). IEEE. [https://doi.org/10.1109/ICSECE58870.2023.10263460](https://doi.org/10.1109/ICSECE58870.2023.10263460)

Nguyen, V. H., Tran, Q. T., Guillo-Sansano, E., Kotsampopoulos, P., Gavriluta, C., Lauss, G., Strasser, T. I., Jensen, T. V., Heussen, K., Gehrke, O., Besanger, Y., Nguyen, T. L., Syed, M. H., Brandl, R., & Arnold, G. (2020). Hardware-in-the-loop assessment methods. In T. I. Strasser, E. C. W. de Jong, & M. Sosnina (Eds.), *European guide to power system testing* (pp. 51–66). Springer. [https://doi.org/10.1007/978-3-030-42274-5_4](https://doi.org/10.1007/978-3-030-42274-5_4)

Short, M., & Pont, M. J. (2005). Hardware in the loop simulation of embedded automotive control systems. *Proceedings of the 8th International IEEE Conference on Intelligent Transportation Systems* (pp. 226–231). IEEE.

Shylla, D., Jain, A., Shah, P., & Sekhar, R. (2023). Model in loop (MIL), software in loop (SIL) and hardware in loop (HIL) testing in MBD. *2023 4th IEEE Global Conference for Advancement in Technology (GCAT)*. IEEE. [https://doi.org/10.1109/GCAT59970.2023.10353323](https://doi.org/10.1109/GCAT59970.2023.10353323)

Won, J., Seok, J., Lee, S., & Yoo, J. (2025). 자율주행 차량 시스템 개발을 위한 Software-in-the-loop simulation 구현 방법론 [Software-in-the-loop simulation implementation methodology for autonomous vehicle system development]. *한국자동차공학회 논문집, 33*(11), 967–977. [https://doi.org/10.7467/KSAE.2025.33.11.967](https://doi.org/10.7467/KSAE.2025.33.11.967)

Zhu, B., Cao, X., Zhang, P., Zhao, J., Han, J., & Tang, R. (2025). High-fidelity ultrasonic radar in-the-loop accelerated test for automatic parking systems. *IEEE Transactions on Intelligent Transportation Systems, 26*(10), 17055–17067. [https://doi.org/10.1109/TITS.2025.3574505](https://doi.org/10.1109/TITS.2025.3574505)