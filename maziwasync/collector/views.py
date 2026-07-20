from datetime import timedelta

from django.utils import timezone
from django.db.models import Sum

from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics 
from core.models import FarmerProfile, PorterProfile, MilkCollection, Notice
from collector.seriliazer import MilkCollectionSerializer
from cooperative.serializer import NoticeSerializer

# create your views here

# porter dashboard 
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def PorterDashboard(request):
    # get the logged porter/user from the token
    try:
        porter = request.user.porter_profile
    except PorterProfile.DoesNotExist:
        return Response({'error':"Only porters can access this dashboard"})


    # time settings
    today = timezone.now().date()
    week_start=today-timedelta(days=7)
    month_start= today.replace(day=1)

    # Today's collection
    today_collections = MilkCollection.objects.filter(porter=porter, collection_date=today)
    today_collections_today = today_collections.count()
    total_litres_today = today_collections.aggregate(total=Sum('litres'))['total'] or 0
    total_amount_today = today_collections.aggregate(total=Sum('total_amount'))['total'] or 0

    # weekly/monthly
    weekly_collections = MilkCollection.objects.filter(porter=porter, collection_date__gte=week_start)
    total_litres_week = weekly_collections.aggregate(total=Sum('litres'))['total'] or 0

    monthly_collections = MilkCollection.objects.filter(porter=porter, collection_date__gte=month_start)
    total_litres_month = monthly_collections.aggregate(total=Sum('litres'))['total'] or 0

    last_collections=MilkCollection.objects.filter(porter=porter).order_by("created_at")[:5]

    # serialize the multiple milk collection records since last_collections is a queryset
    last_collections_list = MilkCollectionSerializer(last_collections, many=True).data

    response_data = {
        'date': today,
        'assigned_farmers': porter.assigned_farmers.count(),
        'total_collections_today': today_collections_today,
        'total_litres_today': total_litres_today,
        'total_amount_today': total_amount_today,
        'total_litres_week': total_litres_week,
        'total_litres_month': total_litres_month,
        'last_collections': last_collections_list,
        'porter_name': f"{porter.first_name} {porter.last_name}",
        'route_name': porter.route_name,
        'employee_id': porter.employee_id,
    }

    return Response(response_data)






# Create your views here.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def AddMilkCollection(request):


    try:
        porters = request.user.porter_profile
    except PorterProfile.DoesNotExist:
        return Response({"error": "Only porters can add milk collection "}, status=403)
    

    #  check if the farmer exists
    try:
        national_id_number=request.data.get('national_id_number')
        farmer=FarmerProfile.objects.get(national_id_number=national_id_number)
    except FarmerProfile.DoesNotExist:
        return Response({"error": "Farmer does not exist"}, status=404)
    
    



    collection = MilkCollection.objects.create(
        farmer=farmer,
        porter=porters,
        litres=request.data.get('litres'),
        session=request.data.get("session")
        
    )


    return Response({
        "message": "Milk collection recorded successfully",
        "collection_id": collection.id,
        "farmer": f"{farmer.first_name} {farmer.last_name}",
        "porter": f"{porters.first_name} {porters.last_name}",
    })


class MyCollections(generics.ListAPIView):
    serializer_class = MilkCollectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        porter = self.request.user.porter_profile
        collections = (
            MilkCollection.objects
            .filter(porter=porter)
            .select_related('farmer')
            .order_by('created_at')
        )
        return collections


   
class PorterNoticeview(generics.ListAPIView):
    serializer_class=NoticeSerializer
    permission_classes=[IsAuthenticated]

    def get_queryset(self):
        notices=(
            Notice.objects
            .filter(target__in=['All', 'PORTERS'])
            .order_by('-created_at')
        )
        return notices     