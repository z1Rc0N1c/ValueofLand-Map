import pandas as pd
import requests

# 1. 정리된 엑셀 불러오기
df = pd.read_excel('토지소유_전체재계산_최종.xlsx')

# Vworld API KEY
VWORLD_KEY = "E68BA222-5944-4C0D-9434-C93BD7DF0FFE"


def get_vworld_coords(address):
    url = "https://api.vworld.kr/req/address"
    params = {
        "service": "address",
        "request": "getcoord",
        "version": "2.0",
        "crs": "epsg:4326",  # WGS84 위경도 좌표계
        "address": address,
        "refine": "true",
        "simple": "false",
        "type": "PARCEL",  # 지번 주소 검색
        "key": VWORLD_KEY
    }

    try:
        res = requests.get(url, params=params).json()
        if res['response']['status'] == 'OK':
            x = float(res['response']['result']['point']['x'])  # 경도(lng)
            y = float(res['response']['result']['point']['y'])  # 위도(lat)
            return y, x
    except Exception as e:
        pass
    return None, None


# 2. 좌표 변환 실행
lats, lngs = [], []
for idx, row in df.iterrows():
    full_addr = f"서울특별시 동대문구 {row['법정동']} {row['지번']}"
    lat, lng = get_vworld_coords(full_addr)
    lats.append(lat)
    lngs.append(lng)

df['lat'] = lats
df['lng'] = lngs

# 3. JSON 변환 및 저장
df.to_json('land_data_vworld.json', orient='records', force_ascii=False)
print("좌표 포함 JSON 생성 완료!")