# django
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse, HttpResponseRedirect

from .src.elasticsearch_log import list_logs
from .src.elasticsearch_log import LogManagement

import json
from elasticsearch import Elasticsearch, ConnectionError

@method_decorator(login_required, name="dispatch")
class LogManagementView(View):
    def get(self, request, resource_type=None, system=None):
        try:
            if 'properties' in request.GET:
                return self.log_property_setting(request, resource_type, system)
            else:
                return self.list_logs(
                    request=request, resource_type=resource_type, system=system.split("_")[0]
                )
        except Exception as e:
            print(e)
            return redirect(f'/logs/{resource_type}/{system}/')

    # 시스템 로그 리스트를 보여주는 함수
    def list_logs(self, request, resource_type, system):
        # logging.basicConfig(level=logging.DEBUG)
        if system == "fortinet":
            system = "fortigate"
        elif system == "genians":
            system = "genian"
        page_number = int(request.GET.get("page", 1))
        system_log = LogManagement(system=system, page=page_number)
        filters = dict(request.GET)
        
        if "page" in filters:
            del filters["page"]
            # print('1'*50)
        if "query" in filters and filters["query"][0] == "":
            del filters["query"]
            # print('2'*50)
        
        
        if "query" not in filters:
            total_count, log_list = system_log.filter_query(filters)
            # print('3'*50)
        # 필터 쿼리가 있는 경우 필터링된 로그만 검색
        elif "query" in filters:
            query_string = filters.pop("query")[0]
            parsed_must, parsed_must_not, parsed_filters = system_log.parse_query_string(
                query_string
            )
            filters.update(parsed_filters)

            total_count, log_list = system_log.filter_query(filters)
            # print('4'*50)
        else:
            total_count, log_list = system_log.search_logs()
            # print('5'*50)

        # 룰셋을 기반으로 로그를 탐지합니다.
        try:
            # print('7'*50)
            # Ajax 요청 처리: Ajax 요청인 경우, 필터링된 로그 리스트와 기타 정보를 JsonResponse로 반환
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                # Apply pagination
                page_obj = system_log.paginate()
                context = {
                    "total_count": total_count,
                    "log_list": log_list,
                    "page_obj": page_obj,
                    "page": page_obj["number"],
                    "system": system.title(),
                    "resource_type": resource_type,
                    "table_properties": system_log.get_property_key(),
                }
                # print('6'*50)
                context = render(request, "M_logs/elasticsearch/log_table.html", context=context)
            else:
                context = {
                    "total_count": total_count,
                    "log_list": log_list,
                    "page_obj": system_log.paginate(),
                    "system": system.title(),
                    "resource_type": resource_type,
                    "page": page_number,
                    "log_properties": system_log.fetch_log_properties(),  # 로그 프로퍼티 추출
                    "table_properties": system_log.get_property_key(),
                }
        except ConnectionError as e:
            # logging.error(f"Connection error: {e}")
            context = {
                "total_count": 0,
                "log_list": [],
                "page_obj": None,
                "system": system.title(),
                "resource_type": resource_type,
                "page": page_number,
                "log_properties": [],
            }
        except Exception as e:
            # logging.error(f"An error occurred: {e}")
            context = {
                "total_count": 0,
                "log_list": [],
                "page_obj": None,
                "system": system.title(),
                "resource_type": resource_type,
                "page": page_number,
                "log_properties": [],
            }
        finally:
            if type(context) == dict:
                context.update({"system_name": (" ").join(system.split("_"))})
                return render(request, "M_logs/elasticsearch/eslog.html", context)
            else:
                return context


    # 룰셋에 따른 로그 리스트를 보여주는 함수
    def logs_by_ruleset(self, request, resourceType, system, ruleset_name):
        es = Elasticsearch(hosts=["http://3.35.81.217:9200/"])
        if system == "fortinet":
            system = "fortigate"
        elif system == "genians":
            system = "genian"
        try:
            page_number = int(request.GET.get("page", 1))
            res = es.search(
                index=f"{system}_ruleset", body={"query": {"match": {"name": ruleset_name}}}
            )
            if res["hits"]["total"]["value"] == 0:
                return render(
                    request,
                    "testing/finevo/error_page.html",
                    {"error": f"No ruleset found with name {ruleset_name}"},
                )

            # LogMangement 클래스 생성 후 rule query 지정
            system_log = LogManagement(system=system, page=page_number)
            rule = res["hits"]["hits"][0]["_source"]
            rule_query = rule["query"]["query"]
            system_log.query = rule_query

            # 필요한 값 받아서 보내주기
            total_count, log_list = system_log.search_logs()
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                # Apply pagination
                page_obj = system_log.paginate()
                context = {
                    "total_count": total_count,
                    "log_list": log_list,
                    "page_obj": page_obj,
                    "page": page_obj["number"],
                    "system": system.title(),
                    "resource_type": resourceType,
                    "log_properties": system_log.fetch_log_properties(),  # 로그 프로퍼티 추출
                    "table_properties": system_log.get_property_key(),
                }
                return render(
                    request, "M_logs/elasticsearch/logs_by_ruleset.html", context=context
                )
            page_obj = system_log.paginate()
            context = {
                "total_count": total_count,
                "system": system.title(),
                "page_obj": page_obj,
                "log_list": log_list,
                "resource_type": resourceType,
                "ruleset_name": ruleset_name,
                "ruleset": json.dumps(
                    rule, indent=4
                ),  # 룰셋 세부 정보를 prettified JSON으로 추가
                "page": page_number,
                "log_properties": system_log.fetch_log_properties(),  # 로그 프로퍼티 추출
                "table_properties": system_log.get_property_key(),
            }
            return render(
                request, "M_logs/elasticsearch/logs_by_ruleset.html", context=context
            )

        except ConnectionError as e:
            return JsonResponse({"error": f"Connection error: {e}"}, status=500)
        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {e}"}, status=500)


    def log_property_setting(self, request, resource_type, system):
        system = system.split("_")[0]
        if system == "fortinet":
            system = "fortigate"
        elif system == "genians":
            system = "genian"
        system_log = LogManagement(system=system, page=1)
        return system_log.save_table_property(request=request)

