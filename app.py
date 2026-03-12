import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 분석기", layout="wide")

# --- 1. 정책 데이터 (2026년 3월 기준) ---
region_config = {
    "호남/육지 (준중앙급전 시행)": {"cp": 11.0, "mep": 1.2, "map": 0.8, "desc": "육지 확대 모델 (CP 11원)"},
    "제주도 (입찰제 안착)": {"cp": 22.0, "mep": 1.2, "map": 2.5, "desc": "제주 시범사업 모델 (CP 22원)"}
}

# --- 2. 사이드바 입력 ---
with st.sidebar:
    st.header("📍 1. 발전소 정보")
    selected_region = st.selectbox("지역 선택", list(region_config.keys()))
    conf = region_config[selected_region]
    
    cap_mw = st.number_input("설비 용량 (MW)", value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간", 2.0, 5.5, 3.6)
    fixed_p = st.number_input("고정가격 단가 (원/kWh)", value=180)

    st.header("📊 2. 정산금 상세 설정")
    in_cp = st.number_input("용량 정산금 (CP)", value=conf['cp'])
    in_mep = st.number_input("전력량 정산금 (MEP)", value=conf['mep'])
    in_map = st.number_input("출력제어 보상 (MAP)", value=conf['map'])
    
    vgen_fee_rate = st.slider("브이젠 수수료 (%)", 0, 30, 20) / 100

# --- 3. 수익 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365 # 연간 총 발전량(kWh)

# [A] 기존 방식 총액 (예측정산금 일몰 후 고정가 매전만 수행)
total_rev_base = annual_gen * fixed_p

# [B] VPP 참여 후 총액
vpp_extra_gross = in_cp + in_mep + in_map
vgen_fee_unit = vpp_extra_gross * vgen_fee_rate
owner_net_extra_unit = vpp_extra_gross - vgen_fee_unit
total_unit_vpp = fixed_p + owner_net_extra_unit

total_rev_vpp = annual_gen * total_unit_vpp
net_profit_increase = total_rev_vpp - total_rev_base

# --- 4. 메인 화면 구성 ---
st.title("📑 V-GEN VPP 수익 분석 대시보드")
st.info(f"💡 현재 **{selected_region}** 정책이 적용 중입니다. (예측정산금 일몰 반영)")

# [핵심 총액 비교 섹션]
st.markdown("### 💰 연간 총 수익 비교 (매전 + 정산금)")
m1, m2, m3 = st.columns(3)

with m1:
    st.markdown("""<div style="text-align:center; padding:20px; border-radius:10px; background-color:#f8f9fa;">
                <p style="color:#666; margin-bottom:5px;">기존 방식 (단순 매전)</p>
                <h2 style="margin:0;">""" + f"{total_rev_base/10000:,.0f} 만원" + """</h2>
                <p style="color:#888;">단가 """ + f"{fixed_p}원" + """ 적용</p>
                </div>""", unsafe_allow_html=True)

with m2:
    st.markdown("""<div style="text-align:center; padding:20px; border-radius:10px; background-color:#eef6ff; border:2px solid #00529C;">
                <p style="color:#00529C; font-weight:bold; margin-bottom:5px;">VPP 참여 (최종 수익)</p>
                <h2 style="margin:0; color:#00529C;">""" + f"{total_rev_vpp/10000:,.0f} 만원" + """</h2>
                <p style="color:#00529C;">단가 """ + f"{total_unit_vpp:.2f}원" + """ 적용</p>
                </div>""", unsafe_allow_html=True)

with m3:
    st.markdown("""<div style="text-align:center; padding:20px; border-radius:10px; background-color:#fff1f0; border:2px solid #f63366;">
                <p style="color:#f63366; font-weight:bold; margin-bottom:5px;">연간 순수익 증대</p>
                <h2 style="margin:0; color:#f63366;">""" + f"+ {net_profit_increase/10000:,.0f} 만원" + """</h2>
                <p style="color:#f63366;">기존 대비 """ + f"{(net_profit_increase/total_rev_base)*100:.1f}% 상승" + """</p>
                </div>""", unsafe_allow_html=True)

st.divider()

# [정산금 상세 분석 섹션]
st.subheader("🔍 VPP 정산금 상세 항목 (수익 증대 원인)")
col_a, col_b = st.columns([1.2, 1])

with col_a:
    # 워터폴 차트
    fig_wf = go.Figure(go.Waterfall(
        x = ["고정단가", "용량정산(CP)", "기타정산(MEP+MAP)", "수수료 차감", "최종단가"],
        measure = ["relative", "relative", "relative", "relative", "total"],
        y = [fixed_p, in_cp, in_mep + in_map, -vgen_fee_unit, 0],
        text = [f"{fixed_p}원", f"+{in_cp}원", f"+{in_mep+in_map:.1f}원", f"-{vgen_fee_unit:.1f}원", f"{total_unit_vpp:.1f}원"],
        textposition = "outside",
        decreasing = {"marker":{"color":"#f63366"}},
        increasing = {"marker":{"color":"#00529C"}},
        totals = {"marker":{"color":"#002D5A"}}
    ))
    fig_wf.update_layout(height=450, margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_wf, use_container_width=True)

with col_b:
    st.markdown(f"""
    #### 📝 정산금별 상세 설명
    
    **1. 용량 정산금 (CP: {in_cp}원/kWh)**
    - **원리**: 발전소의 '공급 가능 용량'에 대해 지급하는 고정 보상금입니다.
    - **장점**: 발전량과 상관없이 설비 대기만으로도 받는 **안정적인 확정 수익**입니다.
    
    **2. 전력량 정산금 (MEP: {in_mep}원/kWh)**
    - **원리**: 실시간 시장 입찰을 통해 고정가격 외에 추가로 발생하는 전력 거래 이익입니다.
    
    **3. 기대이익 보상 (MAP: {in_map}원/kWh)**
    - **원리**: **출력제어**로 인해 발전이 중단될 경우, 못 번 수익을 보전해주는 정산금입니다.
    - **효과**: 제주/호남 지역 사장님들의 가장 큰 고민인 출력제어 리스크를 수익으로 바꿉니다.
    """)

# [하단 영업용 데이터]
st.divider()
st.subheader("📊 연간 수익 요약 표")
summary_df = pd.DataFrame({
    "구분": ["기존 방식 (매전)", "V-GEN VPP (최종)"],
    "적용 단가 (원/kWh)": [f"{fixed_p} 원", f"{total_unit_vpp:.2f} 원"],
    "연간 총 수익 (만원)": [f"{total_rev_base/10000:,.0f} 만원", f"{total_rev_vpp/10000:,.0f} 만원"],
    "수익 증분 (만원)": ["-", f"+ {net_profit_increase/10000:,.0f} 만원"]
})
st.table(summary_df)
