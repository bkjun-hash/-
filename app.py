import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기", layout="wide")

# --- 1. 2026년 3월 기준 정책 데이터 ---
region_config = {
    "호남/육지 (준중앙급전 시행 중)": {
        "cp": 11.0, "mep": 1.2, "map": 0.8, 
        "notice": "⚠️ 2026년 3월 준중앙급전 본격 시행: 기존 예측정산금이 CP(11원)로 통합되었습니다."
    },
    "제주도 (입찰제 안착)": {
        "cp": 22.0, "mep": 1.2, "map": 2.5, 
        "notice": "✅ 제주 시범사업: 실시간 시장 정산 및 CP 22원이 적용 중입니다."
    }
}

# --- 2. 사이드바 (기존 항목 유지) ---
with st.sidebar:
    st.header("📍 1. 지역 선택")
    selected_region = st.selectbox("지역 선택", list(region_config.keys()))
    conf = region_config[selected_region]
    
    st.header("🏭 2. 발전소 정보")
    cap_mw = st.number_input("설비 용량 (MW)", value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간", 2.0, 5.5, 3.6)
    fixed_p = st.number_input("현재 고정단가 (원/kWh)", value=180)

    st.header("📊 3. 정산 항목 설정")
    in_cp = st.number_input("용량 정산금 (CP)", value=conf['cp'])
    in_mep = st.number_input("전력량 정산금 (MEP)", value=conf['mep'])
    in_map = st.number_input("출력제어 보상 (MAP)", value=conf['map'])
    
    # 예측정산금은 일몰되었으므로 0으로 고정하여 안내
    in_forecast = st.number_input("기존 예측정산금 (일몰)", value=0.0, disabled=True)

    vgen_fee_rate = st.slider("브이젠 수수료 (%)", 0, 30, 20) / 100

# --- 3. 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
base_unit = fixed_p  # 예측정산금 일몰 반영

vpp_extra_gross = in_cp + in_mep + in_map
vgen_fee = vpp_extra_gross * vgen_fee_rate
owner_net_extra = vpp_extra_gross - vgen_fee
total_unit = fixed_p + owner_net_extra

extra_profit = annual_gen * owner_net_extra

# --- 4. 메인 UI (익숙한 구성 + 정책 보완) ---
st.title("📑 V-GEN VPP 수익 분석 대시보드")
st.warning(conf['notice'])

# [핵심 지표 박스]
st.markdown(f"""
<div style="background-color:#f8f9fa; padding:25px; border-radius:15px; border: 1px solid #dee2e6; margin-bottom:25px;">
    <h2 style="margin:0; color:#00529C; font-size:24px;">💰 연간 예상 수익 증가액: <b>+ {extra_profit/10000:,.0f} 만원</b></h2>
    <div style="display: flex; justify-content: space-between; margin-top:15px;">
        <p style="margin:0; font-size:18px;">현재 단가: <b>{base_unit} 원</b></p>
        <p style="margin:0; font-size:20px; color:#f63366;">VPP 참여 단가: <b>{total_unit:.2f} 원</b></p>
        <p style="margin:0; font-size:18px; color:#00529C;">순증분: <b>+{owner_net_extra:.2f} 원/kWh</b></p>
    </div>
</div>
""", unsafe_allow_html=True)

# [차트 영역 - 오류 수정 포인트]
st.subheader("📈 정산 단가 상세 구성")
fig_wf = go.Figure(go.Waterfall(
    name = "정산단가",
    orientation = "v",
    # x축 항목 (5개)
    x = ["기본단가", "용량요금(CP)", "기타정산금", "V-GEN수수료", "최종단가"],
    # 항목별 성격 정의 (리스트 길이 일치 필수)
    measure = ["relative", "relative", "relative", "relative", "total"],
    # 실제 수치
    y = [fixed_p, in_cp, in_mep + in_map, -vgen_fee, 0],
    text = [f"{fixed_p}", f"+{in_cp}", f"+{in_mep+in_map:.1f}", f"-{vgen_fee:.1f}", f"{total_unit:.1f}"],
    textposition = "outside",
    connector = {"line":{"color":"rgb(63, 63, 63)"}},
    totals = {"marker":{"color":"#002D5A"}},
    increasing = {"marker":{"color":"#00529C"}},
    decreasing = {"marker":{"color":"#f63366"}}
))

fig_wf.update_layout(height=500, showlegend=False)
st.plotly_chart(fig_wf, use_container_width=True)

# [하단 전문가 제언 섹션]
st.divider()
st.subheader("💡 2026년 시장 대응 전략")
c1, c2 = st.columns(2)
with c1:
    st.info("📊 **준중앙급전 수익 구조**")
    st.write("2026년 3월부터 호남/육지권 태양광은 **준중앙급전** 대상입니다.")
    st.write(f"- 일몰된 예측정산금 대신 **kWh당 {in_cp}원의 CP**가 주된 수익원이 됩니다.")
with c2:
    st.error("⚠️ **출력제어 대응**")
    st.write("VPP 참여 자원은 출력제어 시 **기대이익보상(MAP)** 정산금을 받습니다.")
    st.write("- 미참여 자원 대비 연간 수익 방어율이 약 15% 이상 높습니다.")
