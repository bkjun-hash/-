import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기 (2026 실무형)", layout="wide")

# --- 1. 2026년 3월 기준 정책 프리셋 ---
# 육지(호남 등)는 이제 준중앙급전이 '기본'입니다.
region_config = {
    "호남/육지 (준중앙급전 시행 중)": {
        "cp": 11.0, "mep": 1.2, "map": 0.8, "forecast": 0.0, 
        "status": "2026년 3월 준중앙급전 본격 시행",
        "notice": "⚠️ 기존 예측정산금이 일몰되고 용량요금(CP) 체계로 완전히 전환되었습니다."
    },
    "제주도 (입찰제 안착)": {
        "cp": 22.0, "mep": 1.2, "map": 2.5, "forecast": 0.0, 
        "status": "재생에너지 입찰제도 안착 단계",
        "notice": "✅ 실시간 시장(15분 단위) 이중정산을 통해 수익이 확정됩니다."
    }
}

# --- 2. 사이드바 (익숙한 항목 유지 + 현행 정책 반영) ---
with st.sidebar:
    st.header("📍 1. 지역 및 현행 제도")
    selected_region = st.selectbox("지역 선택", list(region_config.keys()))
    conf = region_config[selected_region]
    st.success(f"현재 상태: {conf['status']}")
    
    st.header("🏭 2. 발전소 정보")
    cap_mw = st.number_input("설비 용량 (MW)", value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간", 2.0, 5.5, 3.6)
    fixed_p = st.number_input("현재 고정단가 (원/kWh)", value=180)

    st.header("📊 3. 정산 항목 (현행 기준)")
    # 사업주가 이해하기 쉬운 용어로 유지하되 정책 수치는 자동 반영
    in_cp = st.number_input("용량 정산금 (CP) - 제도 보장", value=conf['cp'])
    in_mep = st.number_input("전력량 정산금 (MEP) - 추가", value=conf['mep'])
    in_map = st.number_input("출력제어 보상 (MAP) - 손실방지", value=conf['map'])
    
    # 예측정산금은 이제 0원으로 기본 세팅 (일몰 반영)
    in_forecast = st.number_input("기존 예측정산금 (일몰됨)", value=0.0, disabled=True)

    vgen_fee_rate = st.slider("브이젠 수수료 (%)", 0, 30, 20) / 100

# --- 3. 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
# 기존 수익 (고정가만 존재, 예측정산금 일몰)
base_unit = fixed_p 
# VPP 수익 (고정가 + VPP 추가 정산금 순증분)
vpp_extra_gross = in_mep + in_cp + in_map
vpp_extra_net = vpp_extra_gross * (1 - vgen_fee_rate)
total_unit = fixed_p + vpp_extra_net

extra_profit = annual_gen * vpp_extra_net

# --- 4. 메인 화면 UI ---
st.title("📑 V-GEN VPP 현행 수익 분석 대시보드")
st.warning(conf['notice'])

# [강조 박스: 사업주 핵심 지표]
st.markdown(f"""
<div style="background-color:#f8f9fa; padding:25px; border-radius:15px; border: 1px solid #dee2e6; margin-bottom:25px;">
    <h2 style="margin:0; color:#00529C; font-size:24px;">💰 제도 개편 후 연간 순수익 증가: <b>+ {extra_profit/10000:,.0f} 만원</b></h2>
    <div style="display: flex; justify-content: space-between; margin-top:15px;">
        <p style="margin:0; font-size:18px;">현재 단가: <b>{base_unit} 원</b></p>
        <p style="margin:0; font-size:20px; color:#f63366;">VPP 참여 단가: <b>{total_unit:.2f} 원</b></p>
        <p style="margin:0; font-size:18px; color:#00529C;">수익 향상폭: <b>+{vpp_extra_net:.2f} 원/kWh</b></p>
    </div>
</div>
""", unsafe_allow_html=True)

# 시각화 (워터폴 차트: 사업주가 '왜' 돈을 더 버는지 설명)
st.subheader("📈 정산 단가 상세 구성")
fig_wf = go.Figure(go.Waterfall(
    x = ["고정단가", "용량요금(CP)", "기타정산금", "V-GEN 수수료", "최종단가"],
    y = [fixed_p, in_cp, in_mep + in_map, -(vpp_extra_gross * vgen_fee_rate), 0],
    measure = ["relative", "relative", "relative", "relative", "total"],
    text = [f"{fixed_p}", f"+{in_cp}", f"+{in_mep+in_map}", f"-{vpp_extra_gross*vgen_fee_rate:.1f}", f"{total_unit:.1f}"],
    textposition = "outside",
    marker = {"color":["#ADB5BD", "#00529C", "#00529C", "#f63366", "#002D5A"]}
))
st.plotly_chart(fig_wf, use_container_width=True)

# [전문가 제언: 기사 및 KPX 자료 근거]
st.divider()
st.subheader("💡 2026년 3월 시장 대응 핵심 가이드")
col1, col2 = st.columns(2)

with col1:
    st.info("📊 **호남권 준중앙급전제도 핵심**")
    st.write("- 20MW 이하 소규모 자원은 **VPP를 통해서만 참여 가능**합니다.")
    st.write(f"- 예측정산금 대신 **kWh당 {in_cp}원의 확정 CP**를 수령하는 것이 수익의 핵심입니다.")
    

with col2:
    st.error("⚠️ **출력제어 리스크 관리**")
    st.write("- 입찰 미참여 자원은 출력제어 시 보상이 전무합니다.")
    st.write("- VPP 참여 시 **기대이익보상(MAP)**을 통해 제어 시간만큼의 수익을 지켜낼 수 있습니다.")
