from django.shortcuts import render
from rest_framework import generics,viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Sum
from core.models import FarmerProfile, MilkCollection, Feedback, Notice
from farmer.serializer import MilkCollectionSerializer,FeedbackSerializer
from cooperative.serializer import NoticeSerializer
from datetime import date
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from .services import CattleAIService
import traceback



# Farmer dashboard
class FarmerDashboard(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        farmer = request.user.farmer_profile
        collection= MilkCollection.objects.filter(farmer=farmer)
        total_collection=collection.count()
        total_litres=collection.aggregate(total=Sum('litres'))['total'] or 0 
        total_amount = collection.aggregate(total=Sum('total_amount'))['total'] or 0

        today_collection = collection.filter(collection_date=date.today()).aggregate(total=Sum('litres'))['total'] or 0
        monthly_earning = collection.filter(
            collection_date__month=timezone.now().month
        ).aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        month_litres = collection.filter(
            collection_date__month=timezone.now().month
        ).aggregate(
            total=Sum('litres')
        )['total'] or 0

        return Response({
            "total_collection": total_collection,
            "total_litres": total_litres,
            "total_amount": total_amount,
            "today_collection": today_collection,
            "monthly_earnings": monthly_earning,
            "month_litres": month_litres,
        })









# Create your views here.
class FarmerCollection(generics.ListAPIView):
    serializer_class = MilkCollectionSerializer
    permission_classes = [IsAuthenticated]
# query set- we fetch data from the model in a class
    def get_queryset(self):
        try:
            farmer = FarmerProfile.objects.get(user=self.request.user)
        except FarmerProfile.DoesNotExist:
            raise PermissionDenied(
                "Only farmers can access this endpoint"
            )
        collections=(
            MilkCollection.objects
            .filter(farmer=farmer)
            .select_related('porter')
            .order_by('-created_at')

        )

        return collections
    
# ==========
# Feedback CRUD
# ============
class FeedbackViewset(viewsets.ModelViewSet):
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        try:
            farmer = self.request.user.farmer_profile
        except AttributeError:
            raise PermissionDenied('only farmers can access this endpoint')
        
        feedback = (
            Feedback.objects
            .filter(farmer=farmer)
            .order_by('-created_at')
        )
        return feedback
    
    # post by yhe farmer token
    def perform_create(self, serializer):
        try:
            farmer= self.request.user.farmer_profile
        except:
            raise PermissionDenied("Only farmers can create feedback")

        serializer.save(farmer=farmer)  

           
class FarmerNoticeview(generics.ListAPIView):
    serializer_class=NoticeSerializer
    permission_classes=[IsAuthenticated]

    def get_queryset(self):
        notices=(
            Notice.objects
            .filter(target__in=['All', 'FARMERS'])
            .order_by('-created_at')
        )
        return notices   

      # AI 
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def PredictDisease(request):

    try:
        print("REQUEST DATA:", request.data)

        animal = request.data.get("Animal")
        age = request.data.get("Age")
        temp = request.data.get("Temperature")
        description = request.data.get("Description")

        if not animal:
            return Response(
                {"error": "Animal is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if age is None:
            return Response(
                {"error": "Age is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if temp is None:
            return Response(
                {"error": "Temperature is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not description:
            return Response(
                {"error": "Description is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        ai_service = CattleAIService()

        result = ai_service.predict(
            animal_type=animal,
            age=float(age),
            temp=float(temp),
            description=description
        )

        return Response(result)

    except Exception as e:
        print(f"Groq Extraction Error: {e}") 
        
        print("========== PREDICTION ERROR ==========")
        print(str(e))
        traceback.print_exc()
        print("======================================")

        return Response(
            {
                "status": "error",
                "message": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )