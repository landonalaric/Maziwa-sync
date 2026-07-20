from django.urls import path
from collector import views
from .views import MyCollections  

urlpatterns = [
    path('dashboard/', views.PorterDashboard),
    path('milk_collection/add/', views.AddMilkCollection),
    path('collection/my/', MyCollections.as_view()),
    path('notice/', views.PorterNoticeview.as_view())
]