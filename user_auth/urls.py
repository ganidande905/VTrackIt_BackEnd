from django.urls import path
from .views import register_api, verify_otp_api

urlpatterns = [
    path('register/', register_api, name='register_api'),
    path('verify-otp/', verify_otp_api, name='verify_otp_api'),
]