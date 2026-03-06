import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="브이젠 VPP 5대 정산 시뮬레이터", layout="wide")

# 디자인 개선
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { border: 1px solid #dee2e6; padding: 15px; border-radius: 10px; background-color: white; }
    .sidebar .sidebar-content { background-image: linear-gradient(#2e7bcf,#2e7bcf); color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔋 브이젠(V-GEN) VPP 입찰시장 5대 정산 시뮬레이터")
st.caption("신재생에너지 입찰제도의 모든 정산 항목을 정밀하게 분석합니다.")

# --- 사이드바: 입력 섹션 ---
with st.sidebar:
    st.header("🏢 발전소 기본 정보")
    cap_mw = st.number_input("설비 용량 (MW)", min_value=0.1, value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간 (시간)", 2.0, 5.5, 3.6, step=0.1)
    fixed_p = st.number_input("고정가격계약 단가 (원/kWh)", min_value=100, value=180)
    
    st.divider()
    
    st.header("💰 5대 입찰 정산 항목 (원/kWh)")
    # 1. 용량정산금 (CP)
    in_cp = st.number_input("1. 용량정산금 (CP)", value=5.5, step=0.1, help="발전 준비 상태에 대한 보상")
    # 2. 부가정산금 (MAP)
    in_map = st.number_input("2. 부가정산금 (MAP)", value=2.0, step=0.1, help="출력제어 시 기회비용 보전")
    # 3. 정산차익 (MPR)
    in_mpr = st.number_input("3. 정산차익 (MPR)", value=0.5, step=0.1, help="입찰가와 실시간가 차이에 의한 추가 이익")
    # 4. 보상정산금 (EAC)
    in_eac = st.number_input("4. 보상정산금 (EAC)", value=0.2, step=0.1, help="계통 기여도 및 기타 보상 항목")
    # 5. 예측오차 페널티 (IMBP) - 차감항목
    in_imbp = st.number_input("5. 예측오차 페널티 (IMBP)", value=0.3, step=0.1, help="예측 오차 발생 시 차감 (입력값만큼 마이너스)")
    
    st.divider()
    st.header("🤝 배분 설정")
    vgen_fee_pct = st.slider("브이젠 운영 수수료 (%)", 0, 30, 20) / 100

# --- 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
# kWh당 추가 단가 합계 (4개 항목 합산 - 페널티 1개 차감)
net_extra_unit = in_cp + in_map + in_mpr + in_eac - in_imbp

# 수익액 계산
total_extra_rev = annual_gen * net_extra_unit
owner_net_profit = total_extra_rev * (1 - vgen_fee_pct)
vgen_fee_amt = total_extra_rev * vgen_fee_pct

# --- 결과 대시보드 ---
st.subheader("📍 핵심 수익 요약")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("최종 추가 단가", f"{net_extra_unit:.2f} 원/kWh")
with c2:
    st.metric("연간 추가 순이익", f"{owner_net_profit:,.0f} 원")
with c3:
    st.metric("월평균 보너스", f"{owner_net_profit/12:,.0f} 원")
with c4:
    st.metric("20년 누적 수익", f"{owner_net_profit*20/100000000:.2f} 억원")

st.divider()

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📊 5대 항목별 기여도 분석")
    # 항목별 데이터를 데이터프레임으로 변환
    source_df = pd.DataFrame({
        "정산 항목": ["용량정산금(CP)", "부가정산금(MAP)", "정산차익(MPR)", "보상정산금(EAC)", "예측페널티(IMBP)"],
        "단가 (원/kWh)": [in_cp, in_map, in_mpr, in_eac, -in_imbp]
    })
    st.bar_chart(source_df, x="정산 항목", y="단가 (원/kWh)", color="#2E7BCF")
    st.info("💡 **PM 분석:** '용량정산금(CP)'과 '부가정산금(MAP)'이 전체 수익의 안정적인 베이스가 됩니다.")

with col_right:
    st.subheader("📑 상세 정산 명세서 (연간)")
    detail_data = {
        "구분": ["기존 고정가격 매출", "입찰 참여 총 추가수익", "브이젠 운영 수수료", "사업자 최종 순증분"],
        "금액 (원)": [
            f"{annual_gen * fixed_p:,.0f}",
            f"{total_extra_rev:,.0f}",
            f"{vgen_fee_amt:,.0f}",
            f"**{owner_net_profit:,.0f}**"
        ]
    }
    st.table(pd.DataFrame(detail_data))

# 영업용 멘트
st.success(f"✅ **브이젠 파트너십 제안:** {cap_mw}MW 발전소 기준, 20년간 총 **{owner_net_profit*20:,.0f}원**의 자산 가치를 추가로 창출할 수 있습니다.")
