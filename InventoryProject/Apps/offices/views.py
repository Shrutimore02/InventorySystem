from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Office

@api_view(['GET'])
def get_offices(request):
    offices = Office.objects.order_by('name')
    return Response([
        {
            'id': office.id,
            'name': office.name,
            'location': office.location,
            'floor_choices': office.get_floor_options(),
        }
        for office in offices
    ])
