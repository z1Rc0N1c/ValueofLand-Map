import pandas as pd
import requests

# 엑셀 -> 지도(index.html)가 읽는 land_data_vworld.json 만들기
SRC = '토지소유_전체재계산_최종_전필지.xlsx'   # land_all.py 가 만든 파일
OUT = 'land_data_vworld.json'

# 주소 -> 좌표 변환(lat/lng). 지도(index.html)는 이 값을 쓰지 않고, 필지가 수천 개면
# 필지마다 API를 한 번씩 불러서 매우 오래 걸리므로 기본은 꺼둠. 필요할 때만 True 로.
GEOCODE = False

# Vworld API KEY
VWORLD_KEY = "E68BA222-5944-4C0D-9434-C93BD7DF0FFE"

# 1. 정리된 엑셀 불러오기 (지번은 글자로 읽어야 '496' 같은 번지가 숫자로 바뀌지 않음)
df = pd.read_excel(SRC, dtype={'지번': str})

# 1-1. 지도에서 쓰지 않는 컬럼 제거 (면적_x는 반올림된 값, Unnamed는 이름 없는 메모 칸)
df = df.drop(columns=['면적_x'] + [c for c in df.columns if str(c).startswith('Unnamed')],
             errors='ignore')

# 1-2. 비고에 작업 표시용으로 적어둔 말은 지도에 내보내지 않음
df['비고'] = df['비고'].where(~df['비고'].isin(['여기부터', '여기까지', '일단 위쪽']))

# 1-3. 같은 법정동의 같은 지번이 두 번 있으면 한 건으로 합침 (비어 있는 칸은 다른 행의 값으로 채움)
df = df.groupby(['법정동', '지번'], sort=False, as_index=False).first()


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


# 2. 좌표 변환 실행 (GEOCODE = True 일 때만)
if GEOCODE:
    lats, lngs = [], []
    for idx, row in df.iterrows():
        full_addr = f"서울특별시 동대문구 {row['법정동']} {row['지번']}"
        lat, lng = get_vworld_coords(full_addr)
        lats.append(lat)
        lngs.append(lng)

    df['lat'] = lats
    df['lng'] = lngs

# 3. JSON 변환 및 저장
df.to_json(OUT, orient='records', force_ascii=False)
print("JSON 생성 완료!", len(df), "건 ->", OUT)