import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="V-GEN VPP 수익 시뮬레이터 PRO", layout="wide")

# 세션 상태 초기화 (입력 데이터 임시 저장용)
if 'db' not in st.session_state:
    st.session_state.db = []

# 커스텀 CSS
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .main-card { background-color: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .contact-section { background-color: #E9ECEF; padding: 20px; border-radius: 12px; border: 2px solid #007BFF; }
    </style>
    """, unsafe_allow_html=True)

st.title("📑 V-GEN 차세대 VPP 수익 정산 시뮬레이터")

# --- 지역별 데이터 정의 ---
region_presets = {
    "제주도 (출력제어 매우 높음)": {"mep": 1.2, "cp": 8.0, "map": 2.5, "mwp": 0.1, "imbp": 0.3},
    "전라도/호남 (출력제어 높음)": {"mep": 1.2, "cp": 7.8, "map": 0.8, "mwp": 0.1, "imbp": 0.3},
    "경상도/영남 (출력제어 보통)": {"mep": 1.2, "cp": 7.8, "map": 0.3, "mwp": 0.1, "imbp": 0.3},
    "기타 육지 (출력제어 낮음)": {"mep": 1.2, "cp": 7.8, "map": 0.1, "mwp": 0.1, "imbp": 0.3}
}

# --- 사이드바: 입력 제어 ---
with st.sidebar:
    st.header("📍 1. 대상 지역")
    selected_region = st.selectbox("발전소 위치", list(region_presets.keys()))
    preset = region_presets[selected_region]

    st.header("⚡ 2. 발전소 제원")
    cap_mw = st.number_input("설비 용량 (MW)", min_value=0.1, value=1.0, step=0.1)
    gen_time = st.slider("일평균 발전시간", 2.0, 5.5, 3.6, step=0.1)
    fixed_p = st.number_input("고정가격 단가 (원/kWh)", value=180)

    st.header("📊 3. 5대 정산금 상세 (원/kWh)")
    in_mep = st.number_input("MEP (전력량)", value=preset['mep'])
    in_cp = st.number_input("CP (용량)", value=preset['cp'])
    in_map = st.number_input("MAP (기대이익)", value=preset['map'])
    in_mwp = st.number_input("MWP (변동비)", value=preset['mwp'])
    in_imbp = st.number_input("IMBP (페널티)", value=preset['imbp'])

    st.header("💰 4. 수수료 정책")
    vgen_fee_rate = st.slider("브이젠 수수료 (%)", 0, 30, 20) / 100
    partner_fee_rate = st.slider("영업 채널 배분 (%)", 0, 20, 10) / 100

# --- 계산 로직 ---
annual_gen = cap_mw * 1000 * gen_time * 365
gross_extra_unit = in_mep + in_cp + in_map + in_mwp - in_imbp
owner_net_extra_unit = gross_extra_unit * (1 - vgen_fee_rate)
owner_extra_profit_yr = annual_gen * owner_net_extra_unit

# --- 메인 화면 결과 출력 (기존 디자인 유지) ---
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("5대 정산금 합계", f"{gross_extra_unit:.2f}원")
with m2: st.metric("사업자 순증분", f"{owner_net_extra_unit:.2f}원")
with m3: st.metric("사업자 연 순이익", f"{owner_extra_profit_yr/10000:,.0f}만원")
with m4: st.metric("참여 후 최종 단가", f"{fixed_p + owner_net_extra_unit:.1f}원")

st.markdown("---")

# --- 상담 신청 섹션 (DB 수집용) ---
st.markdown("### 📞 맞춤형 수익 분석 상담 신청")
st.write("위 시뮬레이션 결과를 바탕으로 상세 분석 리포트를 보내드립니다.")

with st.container():
    col1, col2, col3 = st.columns(3)
    with col1:
        comp_name = st.text_input("업체명/성함", placeholder="브이젠에너지")
    with col2:
        contact_info = st.text_input("연락처", placeholder="010-0000-0000")
    with col3:
        target_cap = st.text_input("상담 희망 용량", value=f"{cap_mw} MW")

    if st.button("🚀 상세 분석 및 상담 신청하기"):
        if comp_name and contact_info:
            # 데이터 저장
            new_data = {
                "시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "업체명": comp_name,
                "연락처": contact_info,
                "희망용량": target_cap,
                "지역": selected_region,
                "예상수익": f"{owner_extra_profit_yr/10000:,.0f}만원"
            }
            st.session_state.db.append(new_data)
            st.balloons()
            st.success("신청이 완료되었습니다! PM이 확인 후 곧 연락드리겠습니다.")
        else:
            st.error("업체명과 연락처를 모두 입력해 주세요.")

# --- 관리자 전용 섹션 (PM만 확인) ---
with st.expander("🔐 PM 전용 관리자 메뉴 (데이터 확인)"):
    if st.session_state.db:
        df_db = pd.DataFrame(st.session_state.db)
        st.dataframe(df_db)
        
        # 엑셀 다운로드 기능
        csv = df_db.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 상담 신청 리스트 다운로드 (CSV)",
            data=csv,
            file_name=f"VPP_leads_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv',
        )
    else:
        st.write("아직 접수된 상담 내역이 없습니다.")

st.markdown("---")
# (기존 워터폴 차트 및 상세 표 로직은 가독성을 위해 생략했으나, 실제 파일에는 그대로 유지하시면 됩니다.)
