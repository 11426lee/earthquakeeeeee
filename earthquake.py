import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim  # 국가 찾기용 라이브러리 추가

# ==========================================
# 🎨 화사한 화이트 & 블루 테마 CSS 주입
# ==========================================
st.set_page_config(
    page_title="세계 지진 위험도 분석 시스템",
    page_icon="🌍",
    layout="centered"
)

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    h1, h2, h3, p, span, label, div { color: #2D3748 !important; }
    h1 { color: #007BFF !important; font-weight: 800 !important; }
    
    .stNumberInput > div > div > input {
        background-color: #F8F9FA !important;
        border: 1px solid #E2E8F0 !important;
        color: #2D3748 !important;
        border-radius: 8px !important;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #4FACFE 0%, #00F2FE 100%) !important; 
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: 800 !important;
        font-size: 1.1rem !important;
        padding: 12px 24px !important;
        box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4) !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(79, 172, 254, 0.6) !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ 오리지널 지진 분석 로직 + 국가 정보 조회
# ==========================================

# 역지오코딩(좌표 -> 주소 변환) 모듈 초기화
geolocator = Nominatim(user_agent="earthquake_app")

# 데이터 불러오기
try:
    df_new = pd.read_csv("earthquake.csv")
except:
    st.error("earthquake.csv 파일을 찾을 수 없습니다.")
    st.stop()

risk_dict = {0: '높음', 1: '낮음', 2: '중간'}
colors = {0: 'red', 1: 'blue', 2: 'green'}

st.title("🌍 세계 지진 위험도 분석 시스템")
st.write("위도와 경도를 입력하면 주변 지진 데이터를 기반으로 위험도와 국가 위치를 분석합니다.")

# 사용자 입력
lat = st.number_input("위도 입력", value=37.5)
lon = st.number_input("경도 입력", value=127.0)

if st.button("위험도 및 국가 분석 🚀"):

    # 1. 입력한 위도/경도로 국가 이름 찾기
    country_name = "정보 없음"
    try:
        # 언어를 한국어('ko')로 설정하여 국가명 검색
        location = geolocator.reverse(f"{lat}, {lon}", language='ko', timeout=5)
        if location and 'address' in location.raw:
            country_name = location.raw['address'].get('country', '해상 (바다)')
        else:
            country_name = "해상 (바다)"
    except:
        country_name = "위치 정보 조회 지연"

    # 2. 주변 지진 찾기
    near_df = df_new[
        (df_new['위도'] >= lat - 5) &
        (df_new['위도'] <= lat + 5) &
        (df_new['경도'] >= lon - 5) &
        (df_new['경도'] <= lon + 5)
    ]

    if len(near_df) == 0:
        st.warning(f"📍 위치: {country_name} | 주변 지진 데이터가 없습니다.")
    else:
        cluster_ratio = near_df['cluster'].value_counts(normalize=True)
        main_cluster = cluster_ratio.idxmax()

        # 분석 결과 및 국가 정보 출력
        st.markdown(f"""
            <div style='background-color: #F0F8FF; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #E2E8F0; margin-bottom: 20px;'>
                <p style='margin: 0; font-size: 1.1rem; color: #64748B;'>📍 분석 위치: <strong>{country_name}</strong></p>
                <h3 style='color: #007BFF; margin: 10px 0 0 0;'>예상 지진 위험도: {risk_dict[main_cluster]}</h3>
            </div>
        """, unsafe_allow_html=True)

        # 지도 생성
        m = folium.Map(location=[lat, lon], zoom_start=5, tiles="CartoDB positron")
        df_sample = df_new.sample(min(len(df_new), 500), random_state=42)

        for i in range(len(df_sample)):
            cluster = df_sample.iloc[i]['cluster']
            folium.CircleMarker(
                location=[df_sample.iloc[i]['위도'], df_sample.iloc[i]['경도']],
                radius=df_sample.iloc[i]['규모'],
                color=colors[cluster],
                fill=True,
                fill_color=colors[cluster],
                fill_opacity=0.7
            ).add_to(m)

        folium.Marker(
            location=[lat, lon],
            popup=country_name,
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)

        st_folium(m, width=1000, height=600, returned_objects=[])