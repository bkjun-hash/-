import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기", layout="wide")

# --- 1. 정책 데이터 (2026년 3월 기준) ---
region_config = {
    "호남/육지 (준중앙급전 시행 중)": {
        "mep": 1.2, "cp": 11.0, "map": 0.8, "asp": 0.5, "imb": -0.3,
        "desc": "육지형 준중앙급전 (CP 11원 중심)"
    },
    "호남/육지 (입찰제 확대 시나리오)": {
        "mep": 2.5, "cp": 11.0, "map": 1.5, "asp": 0.8, "imb": -0.5,
        "desc": "육지형 재생에너지 입찰제 (수익 다각화)"
    },
    "제주도 (입찰제 안착)": {
        "mep": 1.2, "cp": 22.0, "map": 2.5, "asp": 1.0, "imb": -0.8,
        "desc": "제주 시범사업 (전국 최대 CP 적용)"
    }
}

# --- 2. 사이드바 구성 ---
with st.sidebar:
    st.header("📍 1. 지역 선택")
    selected_region = st.selectbox("지역 및 제도 선택", list(region_config.keys()))
    conf = region_config[selected_region]
    
    st.header("🏭 2. 발전소 정보")
    cap_mw = st.number_input("설비 용량 (MW)", value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간", 2.0, 5.5, 3.6)
    fixed_p = st.number_input("현재 고정가격 단가 (원/kWh)", value=180)

    st.header("📊 3. 정산금 상세 설정 (5가지)")
    # 기존 항목 명칭 및 5가지 체계 유지
    in_mep = st.number_input("1. 에너지 정산금 (MEP)", value=conf['mep'])
    in_cp = st.number_input("2. 용량 정산금 (CP)", value=conf['cp'])
    in_map = st.number_input("3. 기대이익 보상 (MAP)", value=conf['map'])
    in_asp = st.number_input("4. 부가 서비스 정산금 (ASP)", value=conf['asp'])
    in_imb = st.number_input("5. 임밸런스 페널티 (IMB)", value=conf['imb'])

    st.header("🤝 4. 수익 배분 비율 설정")
    # 사업주 비율을 먼저 조정하면 VGEN 수수료가 자동 계산되도록 구성
    owner_share = st.slider("사업주 배분 비율 (%)", 50, 100, 80)
    vgen_fee_rate = 100 - owner_share
    st.info(f"💡 브이젠 수수료: {vgen_fee_rate}%")

# --- 3. 수익 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365

# VPP 추가 정산금 총합
vpp_extra_total_unit = in_mep + in_cp + in_map + in_asp + in_imb
# 사업주에게 돌아가는 순 추가 단가
owner_net_extra_unit = vpp_extra_total_unit * (owner_share / 100)
# 최종 단가
total_unit_vpp = fixed_p + owner_net_extra_unit

# 수익 총액 계산
total_rev_base = annual_gen * fixed_p
total_rev_vpp = annual_gen * total_unit_vpp
net_profit_increase = total_rev_vpp - total_rev_base

# --- 4. 메인 화면 UI ---
st.title("📑 V-GEN VPP 수익 분석 대시보드")
st.markdown(f"**적용 모델:** {selected_region} | **수익 배분:** 사업주 {owner_share}% : 브이젠 {vgen_fee_rate}%")

# [수익 비교 대시보드]
st.markdown("### 💰 연간 총 수익 및 증대 효과")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("기존 총 수익 (매전)", f"{total_rev_base/10000:,.0f} 만원")
with c2:
    st.metric("VPP 참여 총 수익", f"{total_rev_vpp/10000:,.0f} 만원", f"+{net_profit_increase/10000:,.0f} 만원")
with c3:
    st.metric("최종 정산 단가", f"{total_unit_vpp:.2f} 원", f"+{owner_net_extra_unit:.2f} 원")

st.divider()

# [워터폴 차트 및 상세 항목]
col_left, col_right = st.columns([1.5, 1])

with col_left:
    st.subheader("📈 정산 단가 구성 변화 (원/kWh)")
    fig_wf = go.Figure(go.Waterfall(
        x = ["고정단가", "CP(용량)", "MEP(에너지)", "기타(MAP+ASP)", "페널티(IMB)", "수수료차감", "최종단가"],
        measure = ["relative", "relative", "relative", "relative", "relative", "relative", "total"],
        y = [fixed_p, in_cp, in_mep, in_map + in_asp, in_imb, -(vpp_extra_total_unit * (vgen_fee_rate/100)), 0],
        text = [f"{fixed_p}", f"+{in_cp}", f"+{in_mep}", f"+{in_map+in_asp}", f"{in_imb}", f"-{(vpp_extra_total_unit * (vgen_fee_rate/100)):.1f}", f"{total_unit_vpp:.1f}"],
        textposition = "outside",
        decreasing = {"marker":{"color":"#f63366"}},
        increasing = {"marker":{"color":"#00529C"}},
        totals = {"marker":{"color":"#002D5A"}}
    ))
    st.plotly_chart(fig_wf, use_container_width=True)

with col_right:
    st.subheader("📋 정산금 상세 명세")
    st.write(f"**1. 용량 정산금 (CP):** {in_cp}원")
    st.write(f"**2. 에너지 정산금 (MEP):** {in_mep}원")
    st.write(f"**3. 기대이익 보상 (MAP):** {in_map}원")
    st.write(f"**4. 부가 서비스 (ASP):** {in_asp}원")
    st.write(f"**5. 임밸런스 페널티 (IMB):** {in_imb}원")
    st.divider()
    st.write(f"**합계 VPP 추가 정산금:** {vpp_extra_total_unit:.2f}원")
    st.write(f"**사업주 순수익분 ({owner_share}%):** {owner_net_extra_unit:.2f}원")

# [최종 요약 표]
st.divider()
st.subheader("📅 매전 수익 상세 비교 데이터")
res_df = pd.DataFrame({
    "구분": ["기존 방식 (매전)", "브이젠 VPP (최종)"],
    "적용 단가 (원/kWh)": [f"{fixed_p:,.1f} 원", f"{total_unit_vpp:,.2f} 원"],
    "연간 총 매출 (만원)": [f"{total_rev_base/10000:,.0f} 만원", f"{total_rev_vpp/10000:,.0f} 만원"],
    "수익 증분 (만원)": ["-", f"+ {net_profit_increase/10000:,.0f} 만원"]
})
st.table(res_df)
