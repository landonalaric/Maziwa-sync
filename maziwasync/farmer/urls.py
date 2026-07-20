from django.urls import include, path
from farmer import views
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register('feedback', views.FeedbackViewset, basename='Feedback')

urlpatterns = [
    path('collection/', views.FarmerCollection.as_view()),
    path('dashboard/', views.FarmerDashboard.as_view()),
    path('notice/', views.FarmerNoticeview.as_view()),
    path('predict/', views.PredictDisease),

    path('', include(router.urls)),
]