from django.urls import path
from core import views
from collector import views as collector_views


urlpatterns = [
    path('auth/register/', views.Register),
    path('auth/login/', views.Login),
    path('auth/myprofile/', views.Myprofile),
    path('auth/logout/', views.Logout),
    path('milk_collection/add/', collector_views.AddMilkCollection),
]
 