# # local
# from .mongo import get_db_handle, get_collection_handle
# # django 
# from django.conf import settings
# # 3rd party
# import folium
# import pygeoip

# def get_ip_info(ip):
#     '''
#     latitude: 위도
#     longitude: 경도
#     country_name: 국가 이름
#     country_code: 국가 코드
#     '''
#     geo = pygeoip.GeoIP('./TeirenSIEM/GeoLiteCity.dat')
#     try:
#         ip_info = geo.record_by_name(ip)
#         country_name=ip_info
#         latitude=ip_info["latitude"]
#         longitude=ip_info["longitude"]
#     except:
#         latitude = '0'
#         longitude = '0'

#     return [latitude, longitude]

# def folium_test(lat, long):
#     '''
#     titles 지도 디자인
#         dark_matter: 검은색 배경
#         positron: 흰색 배경
#         Watercolor: 수도 배경
#         Toner: 흑백
#         Terrain: 회색+mountain
#         없음: 기본 타일
#     '''
#     location=[lat, long]    #default 위도 경도
#     titles="CartoDB positron"   #dark_matter
#     zoom_start=3    #지도 확대
#     m=folium.Map(
#         location=location,
#         zoom_start=zoom_start,
#         max_bounds=True,
#         min_zoom=2, min_lat=-84,
#         max_lat=84, min_lon=-175, max_lon=187,
#     )

#     #ip를 경도위도로 변환
#     db_handle = get_db_handle("ts_db")
#     collection_handle = get_collection_handle(db_handle, 'NCP')
#     log_list = collection_handle.find(
#                     {"sourceIp":{"$ne":None}},
#                     {'_id':0, 'sourceIp':1 }
#                 )


#     ip_info=[]
#     # 마커 찍기
#     for log in log_list:
#         if log not in ip_info:
#             ip_info.append(get_ip_info(log['sourceIp']))  #이거 빼도 느림
#             folium.Marker(
#                 get_ip_info(log['sourceIp'])
#             ).add_to(m)


#     # Export folium map as HTML string
#     map_html = m._repr_html_()

#     return {
#         "map": map_html,
#         "ip_info":ip_info,
#     }
