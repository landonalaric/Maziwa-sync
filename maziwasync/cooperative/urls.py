from django.urls import path, include
from . import views

from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register('farmer', views.FarmerViewset,basename='farmers' )
router.register('porter', views.PorterViewset,basename='porters' )
router.register('milkcollection', views.MilkCollectionViewset,basename='collection')
router.register('notice', views.NoticeViewset, basename='notice')
urlpatterns = [
	path('', include(router.urls)),
   path('dashboard/', views.AdminDashboardView.as_view()),
   path('farmer/balance/', views.FarmerWithBal),
   path('payFarmer/',views.payFarmer),
   path('Callback/',views.MpesaCallback)
   
]