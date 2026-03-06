import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="브이젠 VPP 공식 정산 시뮬레이터", layout="wide")

# 스타일 설정
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    .stMetric { border: 1px solid #d1d5db; padding: 20px; border-radius: 12px; background-color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚖️ 브이젠(V-GEN) 제주 시범사업 표준 정산 시뮬레이터")
st.caption("전력거래소(KPX) 제주 시범사업 정산 교육 자료의 공식 항목을 준수합니다.")

# --- 사이드바: 입력 섹션 ---
with st.sidebar:
    st.header("📋 발전소 정보")
    cap_mw = st.number_input("설비 용량 (MW)", min_value=0.1, value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간 (시간)", 2.0, 5.5, 3.6, step=0.1)
    fixed_p = st.number_input("기존 고정가격 단가 (원/kWh)", min_value=100, value=180)
    
    st.divider()
    
    st.header("💰 5대 공식 정산 항목 (원/kWh)")
    # 공식 명칭으로 수정 
    in_mep = st.number_input("1. 전력량정산금 (MEP) 증분", value=0.5, step=0.1, help="하루전/실시간 시장 이중정산에 따른 차익")
    in_cp = st.number_input("2. 용량정산금 (CP)", value=5.5, step=0.1, help="공급가능용량 및 실효용량 기반 지급 ")
    in_map = st.number_input("3. 기대이익정산금 (MAP)", value=2.0, step=0.1, help="계통사유 출력제어 시 기대이익 보전")
    in_mwp = st.number_input("4. 변동비보전정산금 (MWP)", value=0.1, step=0.1, help="입찰비용 미회수 시 보전 (재생e는 드물게 발생)")
    in_imbp = st.number_input("5. 임밸런스 페널티 (IMBP) 차감", value=0.3, step=0.1, help="급전지시 미이행 시 부과되는 페널티")
    
    st.divider()
    st.header("🤝 수익 배분")
    vgen_fee_pct = st.slider("브이젠 수수료 (%)", 0, 30, 20) / 100

# --- 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
# 공식 항목 합산: MEP(증분) + CP + MAP + MWP - IMBP
net_extra_unit = in_mep + in_cp + in_map + in_mwp - in_imbp

total_extra_rev = annual_gen * net_extra_unit
owner_net_profit = total_extra_rev * (1 - vgen_fee_pct)

# --- 결과 대시보드 ---
st.subheader("🚀 입찰 시장 참여 기대 수익")
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("연간 추가 순이익", f"{owner_net_profit:,.0f} 원")
with m2:
    st.metric("kWh당 추가 수익 단가", f"{net_extra_unit:.2f} 원")
with m3:
    st.metric("20년 예상 누적 수익", f"{owner_net_profit*20:,.0f} 원")

st.divider()

col_l, col_r = st.columns([1.2, 1])

with col_l:
    st.subheader("📊 항목별 수익 기여도 (원/kWh)")
    # 공식 명칭 데이터프레임
    source_df = pd.DataFrame({
        "공식 정산 항목": ["전력량(MEP)", "용량(CP)", "기대이익(MAP)", "변동비보전(MWP)", "페널티(IMBP)"],
        "단가 (원)": [in_mep, in_cp, in_map, in_mwp, -in_imbp]
    })
    st.bar_chart(source_df, x="공식 정산 항목", y="단가 (원)", color="#004A99")

with col_r:
    st.subheader("💡 KPX 공식 용어 설명")
    st.markdown(f"""
    - **MEP**: 하루전시장과 실시간시장의 가격 편차를 정산합니다. [cite: 9]
    - **CP**: 공급가능용량에 대해 지급하는 고정비 성격의 정산금입니다. 
    - **MAP**: 계통 제약으로 발전하지 못한 부분의 기대수익을 보전합니다. [cite: 25, 28]
    - **MWP**: 입찰 가격보다 시장 가격이 낮아 손실이 날 경우 보전해줍니다. [cite: 19]
    - **IMBP**: 급전지시를 어겼을 때 부과되는 벌금형 정산금입니다. [cite: 29]
    """)

# 하단 안내
st.warning("본 시뮬레이션은 전력거래소 제주 시범사업 정산규칙을 기반으로 하며, 실제 정산 금액은 실시간 계통 상황에 따라 달라질 수 있습니다. ")
