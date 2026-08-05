from django.shortcuts import render
from django.contrib.auth import update_session_auth_hash
from rest_framework.decorators import api_view, permission_classes
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.views import APIView, Response

from core.models import FarmerProfile, Feedback, Payment, PorterProfile, MilkCollection, Notice
from cooperative.serializer import FarmerSerializer, PorterSerializer, NoticeSerializer

from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum

from collector.seriliazer import MilkCollectionSerializer
from cooperative.services import MpesaPayment
from rest_framework import status

# Create your views here.
class AdminDashboardView(APIView):
    # only admin can access this analytics dashboard
    permission_classes = [IsAdminUser]

    # METHOD TO GET THE ANALYTICS
    def get(self, request):
        # define the dates according to django timezone settings
        # used for daily, weekly and monthly calculations
        today = timezone.localdate()
        # calculate the weekly which is 7 days
        week_start = today - timedelta(days=7)

        # farmer and porter stats
        total_farmers = FarmerProfile.objects.count()
        total_porters = PorterProfile.objects.count()

        # Milk collection stats
        # We retrieve all the collection so that we can reuse
        collections = MilkCollection.objects.all()
        total_litres = collections.aggregate(total=Sum('litres'))['total'] or 0
        daily_litres = collections.filter(collection_date=today).aggregate(total=Sum('litres'))['total'] or 0
        # weekly collection
        weekly_litre = collections.filter(collection_date__gte=week_start).aggregate(total=Sum('litres'))['total'] or 0

        # monthly collection
        monthly_litres = collections.filter(
            collection_date__year=today.year,
            collection_date__month=today.month
        ).aggregate(total=Sum('litres'))['total'] or 0
 

        total_revenue=collections.filter(collection_date=today).aggregate(total=Sum('total_amount'))['total'] or 0
       
        weekly_revenue= collections.filter(collection_date__gte=week_start).aggregate(total=Sum('total_amount'))['total'] or 0

        
        monthly_revenue=collections.filter(collection_date__year=today.year, collection_date__month=today.month).aggregate(total=Sum('total_amount'))['total'] or 0

        # Feedback analytics
        feedback = Feedback.objects.all()
        feedback_pending = feedback.filter(status='PENDING').count()
        feedback_resolved = feedback.filter(status='RESOLVED').count()

        # Top farmers - retrieve farmers with highest milk delivery
        top_farmers = FarmerProfile.objects.order_by('-total_milk_delivered')[:5]
        top_farmers_data = FarmerSerializer(top_farmers, many=True).data
          
            # Top ten latest milk collections
        recent_collections = MilkCollection.objects.select_related(
            'farmer',
            'porter'
        ).order_by('-created_at')[:10]

        # convert the collection 
        recent_collection_date = MilkCollectionSerializer(
            recent_collections,
            many=True
        ).data

    



         #   Dashboard response


        data = {
            'total_farmers': total_farmers,
            'total_porters': total_porters,
            'total_litres': total_litres,
            'daily_litres': daily_litres,
            'weekly_litre': weekly_litre,
            'monthly_litres': monthly_litres,
            'total_revenue': total_revenue,
            'weekly_revenue': weekly_revenue,
            'monthly_revenue': monthly_revenue,
            'feedback_pending': feedback_pending,
            'feedback_resolved': feedback_resolved,
            'top_farmers': top_farmers_data,
            'recent_collections': recent_collection_date,
        }

        return Response(data)


class AdminProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "name": user.get_full_name() or user.username,
            "email": user.email,
            "phone": getattr(user, "phone", ""),
            "role": "admin",
        })

    def patch(self, request):
        user = request.user
        data = request.data

        if "name" in data:
            # adjust to however you store name (first_name/last_name, or a profile model)
            user.first_name = data["name"]
        if "email" in data:
            user.email = data["email"]
        if "phone" in data and hasattr(user, "phone"):
            user.phone = data["phone"]

        user.save()
        return Response({"message": "Profile updated successfully"})


class AdminChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")

        if not user.check_password(current_password):
            return Response(
                {"message": "Current password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)  # keeps user logged in after password change

        return Response({"message": "Password changed successfully"})

          



class FarmerViewset(viewsets.ModelViewSet):
    queryset = FarmerProfile.objects.all()
    serializer_class = FarmerSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

class PorterViewset(viewsets.ModelViewSet):
    queryset = PorterProfile.objects.all()
    serializer_class = PorterSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

class MilkCollectionViewset(viewsets.ModelViewSet):
    queryset = MilkCollection.objects.select_related(
        'farmer',
        'porter'
    )
    serializer_class = MilkCollectionSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ['get','post' 'put', 'patch', 'delete']


# Notices board by the cooperative
class NoticeViewset(viewsets.ModelViewSet):
    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer
    permission_classes = [IsAdminUser]
 

   # a method that offer flexibility when you are making a post requests

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def FarmerWithBal(request):
    farmers=FarmerProfile.objects.all()
    data=[] 
    for farmer in farmers:
        earned=MilkCollection.objects.filter(farmer=farmer).aggregate(
            total=Sum('total_amount')
        )['total'] or 0

            #  amount paid to   
        paid=Payment.objects.filter(farmer=farmer, status='COMPLETED').aggregate(
            total=Sum('amount')
        )['total'] or 0

        balance= earned-paid
        if balance>0:
            data.append({
                "farmer_id":farmer.id,
                "farmer":f"{farmer.first_name} {farmer.last_name}",
                "phone":farmer .phone_number,
                "earned": earned,
                "paid":paid,
                "Balance":balance

            })  
    return Response(data)


# intitiate the disbursment to the farmer
@api_view(["POST"])
@permission_classes([IsAdminUser])
def payFarmer(request):
    farmer_id=request.data.get("farmer_id")
    amount=request.data.get('amount')

    farmer=FarmerProfile.objects.get(id=farmer_id)

    earned=MilkCollection.objects.filter(farmer=farmer).aggregate(total=Sum('total_amount'))['total'] or 0

    paid=Payment.objects.filter(farmer=farmer, status='COMPLETED').aggregate(total=Sum('amount'))['total'] or 0

    balance=earned-paid
    if balance<=0:
        return Response({"message":"No pending payment"})
    
    payment=MpesaPayment()
    result= payment.pay_farmer(farmer.phone_number, amount)

    # create the payment Record
    Payment.objects.create(
        farmer=farmer,
        amount=amount,
        payment_method="MPESA",
        originator_conversation_id=result['OriginatorConversationID'],
        transaction_ref=result['ConversationID'],
        payment_date=timezone.now()
    )

    return Response({
        "farmer":f"{farmer.first_name} {farmer.last_name}",
    
    })

# ansychoronous callback processing webhook
@api_view(["POST"])
@permission_classes([AllowAny])
def MpesaCallback(request):
    print("=====Call back Hit=====")
    data=request.data
    print("Data",data)
    result=data["Result"]

    conversation = result.get("OriginatorConversationID")

    payment = Payment.objects.get(OriginatorConversationID=conversation)

    if result["ResultCode"]==0:
        payment.status='COMPLETED'
        payment.transaction_ref=result["TransactionID"]
    else:
        payment.status="FAILED"

    payment.save()
    return Response({"received":True})        