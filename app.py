import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="V-GEN 제주 시범사업 정산 시뮬레이터", layout="wide")

# 스타일링
st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    .stMetric { border: 1px solid #e1e4e8; padding: 15px; border-radius: 12px; background-color: white; }
    .stAlert { border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📑 브이젠(V-GEN) 제주 시범사업 공식 정산 및 수익 배분 시뮬레이터")
st.info("전력거래소(KPX) 정산 교육 자료의 이중정산체계 및 재생에너지 입찰제도 산식을 적용했습니다.")

# --- 사이드바: 입력 섹션 ---
with st.sidebar:
    st.header("1️⃣ 발전소 및 기본 정보")
    cap_mw = st.number_input("설비 용량 (MW)", min_value=0.1, value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간 (시간)", 2.0, 5.5, 3.6, step=0.1)
    fixed_p = st.number_input("기존 고정가격 단가 (원/kWh)", min_value=100, value=180)
    
    st.divider()
    
    st.header("2️⃣ 5대 공식 정산 단가 (원/kWh)")
    # 교육자료 기반 공식 명칭 및 기본값 세팅
    in_mep = st.number_input("전력량정산금 (MEP) 증분", value=0.5, help="하루전/실시간 시장 가격 편차 정산")
    in_cp = st.number_input("용량정산금 (CP)", value=5.5, help="공급가능용량에 대한 고정비 보상")
    in_map = st.number_input("기대이익정산금 (MAP)", value=2.0, help="출력제어 시 기대이익 보전")
    in_mwp = st.number_input("변동비보전정산금 (MWP)", value=0.1, help="입찰비용 미회수분 보전")
    in_imbp = st.number_input("임밸런스 페널티 (IMBP)", value=0.3, help="급전지시 미이행 시 차감")
    
    st.divider()
    
    st.header("3️⃣ 수수료 및 배분 설정 (%)")
    vgen_fee_rate = st.slider("브이젠 수수료율 (%)", 0, 30, 20) / 100
    partner_fee_rate = st.slider("영업 채널 배분율 (%)", 0, 20, 10, help="브이젠 수수료 중 파트너에게 지급할 비율") / 100

# --- 핵심 계산 로직 ---
# 1. 연간 발전량
annual_gen = cap_mw * 1000 * gen_time * 365

# 2. 미 참여 시 수익 (기존 고정가격 매출)
non_participate_rev = annual_gen * fixed_p

# 3. 입찰 시장 추가 수익 (Gross Alpha)
net_extra_unit = in_mep + in_cp + in_map + in_mwp - in_imbp
total_extra_rev = annual_gen * net_extra_unit

# 4. 수익 배분 (Net)
vgen_gross_fee = total_extra_rev * vgen_fee_rate         # 브이젠 전체 수수료
partner_commission = vgen_gross_fee * partner_fee_rate    # 영업 채널 수수료
vgen_net_profit = vgen_gross_fee - partner_commission    # 브이젠 순수익
owner_extra_profit = total_extra_rev - vgen_gross_fee    # 사업자 추가 순이익

# 5. 최종 총 수익 (기존 수익 + 사업자 추가 순이익)
final_total_rev = non_participate_rev + owner_extra_profit

# --- 결과 출력 ---

# 상단 대시보드
st.subheader("💰 수익 비교 요약")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("미 참여 시 수익 (연)", f"{non_participate_rev:,.0f} 원")
with c2:
    st.metric("브이젠 참여 시 총 수익 (연)", f"{final_total_rev:,.0f} 원", f"+{owner_extra_profit:,.0f} 원")
with c3:
    st.metric("사업자 순증분 (20년)", f"{owner_net_profit * 20 / 100000000:.2f} 억원")

st.divider()

# 메인 분석 영역
col_l, col_r = st.columns([1.5, 1])

with col_l:
    st.subheader("📊 연간 수익 시나리오 비교")
    compare_df = pd.DataFrame({
        "구분": ["미 참여 시 (기본)", "브이젠 참여 (최종)"],
        "연간 매출 (원)": [non_participate_rev, final_total_rev]
    })
    st.bar_chart(compare_df, x="구분", y="연간 매출 (원)", color="#1F77B4")

    st.subheader("💸 수수료 및 배분 상세")
    fee_data = pd.DataFrame({
        "항목": ["발전사업자 추가 순익 (80%*)", "브이젠 운영 순수익", "영업 채널 수수료"],
        "금액 (연간)": [owner_extra_profit, vgen_net_profit, partner_commission]
    })
    st.table(fee_data)
    st.caption("*수수료 설정에 따라 비율은 달라질 수 있습니다.")

with col_r:
    st.subheader("📋 5대 정산 항목별 기여")
    item_df = pd.DataFrame({
        "공식 항목": ["전력량(MEP)", "용량(CP)", "기대이익(MAP)", "변동비(MWP)", "페널티(IMBP)"],
        "단가 (원/kWh)": [in_mep, in_cp, in_map, in_mwp, -in_imbp]
    })
    st.bar_chart(item_df, x="공식 항목", y="단가 (원/kWh)", color="#FF7F0E")
    
    with st.expander("📝 항목별 공식 설명 보기"):
        st.write("**MEP:** 실시간 시장 가격 편차 정산")
        st.write("**CP:** 공급가능용량 기반 고정비 정산")
        st.write("**MAP:** 출력제어 시 기대수익 보전")
        st.write("**MWP:** 입찰비용 미회수분 보전")
        st.write("**IMBP:** 급전지시 미이행 페널티")

st.success(f"✅ **PM 전략:** 미 참여 대비 연간 수익이 **{ (owner_extra_profit/non_participate_rev)*100 :.2f}%** 향상됩니다.")
