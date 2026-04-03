import requests
from django.shortcuts import render
from requests.exceptions import RequestException
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class SomeAPIView(APIView):

    def get(self, *args, **kwargs):
        try:
            response = requests.get('https://api.stripe.com')
            response.raise_for_status()  # Проверка на ошибки HTTP
            data = response.json()
            # Обработка полученных данных
            return Response(data)
        except RequestException as e:
            # Обработка исключения
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)