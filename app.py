import streamlit as st
import pandas as pd

# 페이지 설정 및 테마
st.set_page_config(page_title="브이젠 VPP 맞춤형 수익 계산기", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stNumberInput [data-testid="stMarkdownContainer"] p { font-weight: bold; color: #1f77b4; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 브이젠(V-GEN) VPP 맞춤형 수익 시뮬레이터")
st.info("발전소별 예상 정산단가를 직접 입력하여 정밀한 수익 모델을 설계하세요.")

# --- 사이드바: 입력 변수 ---
with st.sidebar:
    st.header("1️⃣ 발전소 기본 정보")
    capacity_mw = st.number_input("설비 용량 (MW)", min_value=0.1, value=1.0, step=0.1)
    fixed_price = st.number_input("고정가격계약 단가 (원/kWh)", min_value=100, value=180)
    util_rate = st.slider("연간 이용률 (%)", 10.0, 40.0, 15.0) / 100

    st.divider()
    
    st.header("2️⃣ 예상 정산 단가 설정 (원/kWh)")
    # PM님이 직접 입력하고 싶어 하신 핵심 포인트
    user_cp = st.number_input("용량정산금(CP) 예상", value=5.5, step=0.1, help="발전 준비 상태에 따른 보상")
    user_map = st.number_input("부가정산금(MAP) 예상", value=2.0, step=0.1, help="출력제어 시 보전받는 금액")
    user_imbp = st.number_input("예측오차 페널티(IMBP) 차감", value=0.3, step=0.1, help="예측 오차로 인해 차감되는 비용")
    
    st.divider()
    
    st.header("3️⃣ 수수료 설정 (%)")
    fee_rate = st.slider("브이젠 운영 수수료율", 0, 30, 20) / 100

# --- 계산 로직 ---
# 1. 총 추가 단가 (kWh당 보너스)
net_extra_unit = user_cp + user_map - user_imbp

# 2. 연간 발전량 및 매출
annual_gen = capacity_mw * 1000 * 24 * 365 * util_rate
total_alpha_revenue = annual_gen * net_extra_unit

# 3. 배분 계산
vgen_fee = total_alpha_revenue * fee_rate
owner_profit = total_alpha_revenue - vgen_fee
partner_profit = vgen_fee * 0.1 # 파트너는 브이젠 수익의 10% 가정

# --- 메인 화면 결과 ---
# 상단 요약 지표
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("최종 kWh당 추가 이익", f"{net_extra_unit:.2f} 원")
with m2:
    st.metric("사업자 연간 순이익", f"{owner_profit:,.0f} 원")
with m3:
    st.metric("20년 누적 순이익", f"{owner_profit * 20:,.0f} 원")

st.divider()

# 시각화 영역
col_left, col_right = st.columns([1.5, 1])

with col_left:
    st.subheader("📈 입찰 참여 시 수익 구조 변화")
    # 기존 매출 vs 참여 후 매출 비교 데이터
    base_rev = annual_gen * fixed_price
    total_rev = base_rev + owner_profit
    
    compare_df = pd.DataFrame({
        "구분": ["기존 매출 (고정가격)", "브이젠 참여 (추가수익 포함)"],
        "연간 매출 (원)": [base_rev, total_rev]
    })
    st.bar_chart(compare_df, x="구분", y="연간 매출 (원)", color="#003366")

with col_right:
    st.subheader("📋 상세 정산 리포트")
    report_data = {
        "항목": ["연간 발전량", "연간 총 추가 이익", "브이젠 수수료", "사업자 최종 입금액", "파트너 수수료(참고)"],
        "금액": [
            f"{annual_gen:,.0f} kWh",
            f"{total_alpha_revenue:,.0f} 원",
            f"{vgen_fee:,.0f} 원",
            f"**{owner_profit:,.0f} 원**",
            f"{partner_profit:,.0f} 원"
        ]
    }
    st.table(pd.DataFrame(report_data))

# PM 메시지
st.warning(f"💡 **PM 분석:** 현재 입력하신 단가 설정 시, 사업자는 고정가격 대비 약 **{ (owner_profit/base_rev)*100 :.2f}%**의 추가 수익률을 달성할 수 있습니다.")
