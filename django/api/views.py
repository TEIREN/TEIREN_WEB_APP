from django.shortcuts import render
from rest_framework.decorators import api_view
from django.contrib.auth.decorators import login_required
from rest_framework.response import Response

API_VERSION = 'v1'
### api view ###
@login_required
def index(request):
    return render(request, "api/index.html")

# def version(request):
#     return render(request, "api/v1.html")

# def cypher(request):
#     if request.method == 'POST':
#         cypher = request.POST.get('cypher', '')
#         return render(request, 'api/{}/cypher.html'.format(API_VERSION), {'cypher': cypher})
#     else: # GET
#         return render(request, 'api/{}/cypher.html'.format(API_VERSION))

### api endpoint ###

from rest_framework import generics
from rest_framework import viewsets
from .models import Cypher
from .serializers import CypherSerializer
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter
from rest_framework.filters import OrderingFilter
from django.db.models import Q


class CypherListCreateView(generics.ListCreateAPIView):
    queryset = Cypher.objects.all()
    serializer_class = CypherSerializer


class CypherViewSet(viewsets.ModelViewSet):
    queryset = Cypher.objects.all()
    serializer_class = CypherSerializer
    pagination_class = PageNumberPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['cypher_type']
    ordering_fields = ['index']

    def get_queryset(self):
        queryset = super().get_queryset()
        cypher_type = self.request.query_params.get('cypher_type', None)
        function_name = self.request.query_params.get('function_name', None)
        
        filter_conditions = Q()
        if cypher_type:
            filter_conditions &= Q(cypher_type=cypher_type)
        if function_name:
            filter_conditions &= Q(function_name=function_name)
        queryset = queryset.filter(filter_conditions)

        # ordering
        ordering = self.request.query_params.get('ordering', None)
        if ordering in self.ordering_fields:
            queryset = queryset.order_by(ordering)

        return queryset

    def destroy(self, request, pk=None):
        obj = get_object_or_404(self.queryset, pk=pk)
        obj.delete()
        return Response({'message': 'Object deleted successfully'})
    
    
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView

class CypherQuerySet(APIView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def get_params(self, request):
        cypher_type_param = request.query_params.get('cypher_type')
        obj = get_object_or_404(Cypher, cypher_type=cypher_type_param)
        response_data = {
            'cypher_type': obj.cypher_type,
            'cypher': obj.cypher
        }
        return Response(response_data)        


@api_view(['POST'])
def create_cypher(request):
    serializer = CypherSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)
