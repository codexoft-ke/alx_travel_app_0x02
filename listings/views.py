from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create your views here.

@swagger_auto_schema(
    method='get',
    operation_description="Welcome endpoint for the ALX Travel App API",
    responses={
        200: openapi.Response(
            description="Welcome message",
            examples={
                "application/json": {
                    "message": "Welcome to ALX Travel App API",
                    "version": "1.0.0",
                    "endpoints": {
                        "swagger": "/swagger/",
                        "redoc": "/redoc/",
                        "admin": "/admin/"
                    }
                }
            }
        )
    }
)
@api_view(['GET'])
def welcome_view(request):
    """
    Welcome endpoint that provides basic API information.
    """
    return Response({
        "message": "Welcome to ALX Travel App API",
        "version": "1.0.0",
        "endpoints": {
            "swagger": "/swagger/",
            "redoc": "/redoc/",
            "admin": "/admin/"
        }
    }, status=status.HTTP_200_OK)
