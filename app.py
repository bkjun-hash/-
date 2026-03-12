import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 v2.6", layout="wide")

# --- 1. 정책 데이터 (2026년 3월 기준 실무 로직) ---
region_config = {
    "호남/육지 (준중앙급전 시행 중)": {
        "mep": 1.2, "cp": 11.0, "map": 0.8, "asp": 0.5, "imb": -0.3,
        "desc": "육지형 준중앙급전 (CP 11원 중심)"
    },
    "호남/육지 (입찰제 확대 시나리오)": {
        "mep": 2.5, "cp": 11.0, "map": 1.5, "asp": 0.8, "imb": -0.5,
        "desc": "육지형 재생에너지 입찰제 (전국 확대 시나리오)"
    },
    "제주도 (입찰제 안착)": {
        "mep": 1.2, "cp": 22.0, "map": 2.5, "asp": 1.0, "imb": -0.8,
        "desc": "제주 시범사업 (전국 최대 CP 적용)"
    }
}

# --- 2. 사이드바 구성 (기존 기능 100% 유지) ---
with st.sidebar:
    st.header("📍 1. 지역 선택")
    selected_region = st.selectbox("지역 및 제도 선택", list(region_config.keys()))
    conf = region_config[selected_region]
    
    st.header("🏭 2. 발전소 정보")
    cap_mw = st.number_input("설비 용량 (MW)", value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간", 2.0, 5.5, 3.6)
    fixed_p = st.number_input("현재 고정가격 단가 (원/kWh)", value=180)

    st.header("📊 3. 정산금 상세 설정 (5가지)")
    in_mep = st.number_input("1. 에너지 정산금 (MEP)", value=conf['mep'])
    in_cp = st.number_input("2. 용량 정산금 (CP)", value=conf['cp'])
    in_map = st.number_input("3. 기대이익 보상 (MAP)", value=conf['map'])
    in_asp = st.number_input("4. 부가 서비스 정산금 (ASP)", value=conf['asp'])
    in_imb = st.number_input("5. 임밸런스 페널티 (IMB)", value=conf['imb'])

    st.header("🤝 4. 수익 배분 설정")
    owner_share = st.slider("사업주 배분 비율 (%)", 50, 100, 80)
    vgen_fee_rate = 100 - owner_share
    st.info(f"💡 브이젠 수수료: {vgen_fee_rate}%")

# --- 3. 수익 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
vpp_extra_total_unit = in_mep + in_cp + in_map + in_asp + in_imb
owner_net_extra_unit = vpp_extra_total_unit * (owner_share / 100)
total_unit_vpp = fixed_p + owner_net_extra_unit

total_rev_base = annual_gen * fixed_p
total_rev_vpp = annual_gen * total_unit_vpp
net_profit_increase = total_rev_vpp - total_rev_base

# --- 4. 메인 화면 UI ---
st.title("📑 V-GEN VPP 수익 분석 대시보드")
st.markdown(f"**적용 모델:** {selected_region} | **수익 배분:** 사업주 {owner_share}% : 브이젠 {vgen_fee_rate}%")

# [핵심 지표 대시보드]
st.markdown("### 💰 연간 총 수익 및 증대 효과")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("기존 총 수익 (매전)", f"{total_rev_base/10000:,.0f} 만원")
with c2:
    st.metric("VPP 참여 총 수익", f"{total_rev_vpp/10000:,.0f} 만원", f"+{net_profit_increase/10000:,.0f} 만원")
with c3:
    st.metric("최종 정산 단가", f"{total_unit_vpp:.2f} 원", f"+{owner_net_extra_unit:.2f} 원")

st.divider()

# [워터폴 차트 및 상세 항목 설명]
col_left, col_right = st.columns([1.5, 1])

with col_left:
    st.subheader("📈 정산 단가 구성 분석")
    fig_wf = go.Figure(go.Waterfall(
        x = ["고정단가", "CP(용량)", "MEP(에너지)", "기타(MAP+ASP)", "페널티(IMB)", "수수료차감", "최종단가"],
        measure = ["relative", "relative", "relative", "relative", "relative", "relative", "total"],
        y = [fixed_p, in_cp, in_mep, in_map + in_asp, in_imb, -(vpp_extra_total_unit * (vgen_fee_rate/100)), 0],
        text = [f"{fixed_p}", f"+{in_cp}", f"+{in_mep}", f"+{in_map+in_asp}", f"{in_imb}", f"-{(vpp_extra_total_unit * (vgen_fee_rate/100)):.1f}", f"{total_unit_vpp:.1f}"],
        textposition = "outside"
    ))
    st.plotly_chart(fig_wf, use_container_width=True)

with col_right:
    st.subheader("📋 정산금 항목별 상세 의미")
    with st.expander("1. 에너지 정산금 (MEP)", expanded=True):
        st.write(f"**금액: {in_mep}원**")
        st.caption("실시간 시장 가격과 입찰 가격의 차이에서 발생하는 추가 수익입니다.")
    with st.expander("2. 용량 정산금 (CP)", expanded=True):
        st.write(f"**금액: {in_cp}원**")
        st.caption("발전기가 전력을 공급할 '준비'가 된 상태만으로 받는 고정 보상입니다. 2026년 육지 모델의 핵심 수익원입니다.")
    with st.expander("3. 기대이익 보상 (MAP)"):
        st.write(f"**금액: {in_map}원**")
        st.caption("출력제어로 인해 강제로 발전을 멈췄을 때, 못 번 수익을 보전해주는 보험 같은 정산금입니다.")
    with st.expander("4. 부가 서비스 정산금 (ASP)"):
        st.write(f"**금액: {in_asp}원**")
        st.caption("주파수 조정 등 계통 안정화에 기여했을 때 받는 추가 인센티브입니다.")
    with st.expander("5. 임밸런스 페널티 (IMB)"):
        st.write(f"**금액: {in_imb}원**")
        st.caption("예측 발전량과 실제 발전량의 차이가 클 때 발생하는 차감 항목입니다. V-GEN의 기술력으로 최소화합니다.")

# [새로 추가된 정책 동향 인사이트 섹션]
st.divider()
st.subheader("🚀 2026년 3월 전력시장 정책 동향 및 인사이트")
st.info("💡 **전문가 제언: 육지 재생에너지의 '자원화'가 생존을 결정합니다.**")

insight_c1, insight_c2 = st.columns(2)
with insight_c1:
    st.markdown("""
    #### 1. 예측제도의 일몰과 CP의 등장
    기존의 단순 예측 정산금(kWh당 약 3~4원)은 단계적으로 폐지됩니다. 이제는 전력거래소의 급전 지시를 이행하는 **'준중앙급전 발전기'**로 등록해야만 **kWh당 11원의 용량요금(CP)**을 받을 수 있습니다. 즉, VPP 참여는 선택이 아닌 필수 수익 방어 전략입니다.
    """)
    
with insight_c2:
    st.markdown(f"""
    #### 2. 출력제어 리스크의 수익화 (MAP)
    호남 지역 태양광 출력제어가 빈번해진 현시점에서, 입찰에 참여하지 않은 자원은 일방적인 손실을 입습니다. 하지만 **V-GEN 입찰 자원**은 출력제어 시 **기대이익보상(MAP)**을 통해 매출의 상당 부분을 보전받습니다.
    """)

# [최종 요약 표]
st.divider()
st.subheader("📅 연간 매전 수익 상세 비교")
res_df = pd.DataFrame({
    "구분": ["기존 방식 (매전)", "브이젠 VPP (최종)"],
    "적용 단가 (원/kWh)": [f"{fixed_p:,.1f} 원", f"{total_unit_vpp:,.2f} 원"],
    "연간 총 매출 (만원)": [f"{total_rev_base/10000:,.0f} 만원", f"{total_rev_vpp/10000:,.0f} 만원"],
    "수익 증분 (만원)": ["-", f"+ {net_profit_increase/10000:,.0f} 만원"]
})
st.table(res_df)
