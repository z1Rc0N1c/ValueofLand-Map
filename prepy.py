import pandas as pd
import requests

# 1. 정리된 엑셀 불러오기 (지번은 글자로 읽어야 '496' 같은 번지가 숫자로 바뀌지 않음)
df = pd.read_excel('토지소유_전체재계산_최종.xlsx', dtype={'지번': str})

# 1-1. 지도에서 쓰지 않는 컬럼 제거 (면적_x는 반올림된 값, Unnamed는 이름 없는 메모 칸)
df = df.drop(columns=['면적_x'] + [c for c in df.columns if str(c).startswith('Unnamed')],
             errors='ignore')

# 1-2. 비고에 작업 표시용으로 적어둔 말은 지도에 내보내지 않음
df['비고'] = df['비고'].where(~df['비고'].isin(['여기부터', '여기까지', '일단 위쪽']))

# 1-3. 같은 법정동의 같은 지번이 두 번 있으면 한 건으로 합침 (비어 있는 칸은 다른 행의 값으로 채움)
df = df.groupby(['법정동', '지번'], sort=False, as_index=False).first()

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
print("좌표 포함 JSON 생성 완료!", len(df), "건")