from django.urls import path
from . import views

urlpatterns = [
    path('history/', views.history_view, name='history'),
    path('statistic/', views.statistic_view, name='statistic'),
    path('settings/', views.settings_view, name='settings'),
    path('', views.upload_view, name='upload'),  
    path('api/upload/', views.upload_image, name='upload_image'),
    path('api/results/<int:pk>/', views.get_result, name='get_result'),
]