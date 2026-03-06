import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 설정
st.set_page_config(page_title="V-GEN 제주 시범사업 정산 시뮬레이터", layout="wide")

# 스타일링
st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    .stMetric { border: 1px solid #e1e4e8; padding: 15px; border-radius: 12px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("📑 브이젠(V-GEN) 제주 시범사업 공식 정산 시뮬레이터")
st.info("제주 시범사업 정산 교육 자료 및 시장 예측치를 기반으로 한 표준 단가가 적용되었습니다.")

# --- 사이드바: 입력 섹션 ---
with st.sidebar:
    st.header("1️⃣ 발전소 및 기본 정보")
    cap_mw = st.number_input("설비 용량 (MW)", min_value=0.1, value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간 (시간)", 2.0, 5.5, 3.6, step=0.1)
    fixed_p = st.number_input("기존 고정가격 단가 (원/kWh)", min_value=100, value=180)
    
    st.divider()
    
    st.header("2️⃣ 5대 공식 정산 단가 (원/kWh)")
    st.caption("※ 제주 시범사업 표준 데이터가 기본값으로 입력되어 있습니다.")
    # [PM 결정] 분석된 현실적 단가를 기본값으로 셋팅
    in_cp = st.number_input("용량정산금 (CP)", value=8.0, help="가장 비중이 큰 고정 수익 (예상치)")
    in_map = st.number_input("기대이익정산금 (MAP)", value=2.0, help="출력제어 시 보전 단가")
    in_mep = st.number_input("전력량정산금 (MEP) 증분", value=1.2, help="실시간 시장 정산 차익")
    in_mwp = st.number_input("변동비보전정산금 (MWP)", value=0.1)
    in_imbp = st.number_input("임밸런스 페널티 (IMBP)", value=0.3, help="브이젠 기술력으로 방어 가능한 페널티")
    
    st.divider()
    
    st.header("3️⃣ 수수료 설정 (%)")
    vgen_fee_rate = st.slider("브이젠 수수료율 (%)", 0, 30, 20) / 100
    partner_fee_rate = st.slider("영업 채널 배분율 (%)", 0, 20, 10) / 100

# --- 핵심 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
# 5대 항목 합계 (Gross)
gross_extra_unit = in_mep + in_cp + in_map + in_mwp - in_imbp

# 수익 배분 계산 (Net)
vgen_gross_fee_unit = gross_extra_unit * vgen_fee_rate
owner_net_extra_unit = gross_extra_unit - vgen_gross_fee_unit

# 총액 계산
non_participate_rev = annual_gen * fixed_p
owner_extra_profit_yr = annual_gen * owner_net_extra_unit
final_total_rev_yr = non_participate_rev + owner_extra_profit_yr

# --- 결과 출력 ---
st.subheader("💰 단가 합산 및 수익 비교")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("5대 정산 단가 합계", f"{gross_extra_unit:.2f} 원/kWh", "입찰시장 총 보너스")
with c2:
    st.metric("사업자 순 추가단가", f"{owner_net_extra_unit:.2f} 원/kWh", "수수료 차감 후")
with c3:
    st.metric("참여 시 최종 단가", f"{fixed_p + owner_net_extra_unit:.2f} 원/kWh", f"기존 {fixed_p}원")
with c4:
    st.metric("사업자 연 순증분", f"{owner_extra_profit_yr:,.0f} 원")

st.divider()

# --- 그래프 및 상세 내역 ---
col_l, col_r = st.columns([1.5, 1])

with col_l:
    st.subheader("📊 수익 시나리오 비교 (단가 기준)")
    plot_df = pd.DataFrame({
        "구분": ["미 참여 (기본)", "브이젠 참여 (최종)"],
        "단가 (원/kWh)": [fixed_p, fixed_p + owner_net_extra_unit],
        "색상": ["기존 수익", "브이젠 추가수익"]
    })

    fig = px.bar(
        plot_df, x="단가 (원/kWh)", y="구분", orientation='h',
        text=plot_df["단가 (원/kWh)"].apply(lambda x: f"{x:.2f}원"),
        color="색상",
        color_discrete_map={"기존 수익": "#ADB5BD", "브이젠 추가수익": "#007BFF"}
    )
    # 차이 강조를 위한 축 범위 조정
    fig.update_xaxes(range=[fixed_p * 0.96, (fixed_p + owner_net_extra_unit) * 1.02])
    fig.update_layout(showlegend=False, height=300, margin=dict(l=20, r=20, t=20, b=20), yaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)

    # 상세 배분 현황
    partner_comm_yr = (annual_gen * vgen_gross_fee_unit) * partner_fee_rate
    vgen_net_yr = (annual_gen * vgen_gross_fee_unit) - partner_comm_yr
    st.table(pd.DataFrame({
        "항목": ["발전사업자 추가 순익", "브이젠 운영 순수익", "영업 채널 수수료"],
        "금액": [f"{owner_extra_profit_yr:,.0f} 원", f"{vgen_net_yr:,.0f} 원", f"{partner_comm_yr:,.0f} 원"]
    }))

with col_r:
    st.subheader("📋 5대 정산 항목 구성 (원/kWh)")
    item_df = pd.DataFrame({
        "공식 항목": ["전력량(MEP)", "용량(CP)", "기대이익(MAP)", "변동비(MWP)", "페널티(IMBP)"],
        "단가": [in_mep, in_cp, in_map, in_mwp, -in_imbp]
    })
    st.bar_chart(item_df, x="공식 항목", y="단가", color="#FF7F0E")

st.success(f"✅ **PM의 분석:** 현재 단가 적용 시, 발전사업자는 기존 고정가격 대비 **{ (owner_net_extra_unit/fixed_p)*100 :.1f}%**의 수익 개선 효과를 즉시 누릴 수 있습니다.")
