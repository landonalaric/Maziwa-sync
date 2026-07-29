from email.mime import message

from django.shortcuts import render
from django.contrib.auth import authenticate
from .models import FarmerProfile, PorterProfile
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from django.db import IntegrityError, transaction
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from core.models import User

# Create your views here.
@api_view(['POST'])
@permission_classes([IsAdminUser])
@transaction.atomic
def Register(request):
    # print("request function")
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    role = request.data.get('role')
    phone_number = request.data.get('phone_number')

    # print(username, email, password, role, phone_number)
    
    
    # check if the user already exists
    if User.objects.filter(username=username).exists():
        return Response({"message": "Username already exists"}, status=400)
    if User.objects.filter(email=email).exists():
        return Response({"message": "Email already registered"}, status=400)
    

    try:
        user = User.objects.create_user(
            username=username, email=email, password=password, role=role, phone_number=phone_number)

        if role == 'farmer':
            FarmerProfile.objects.create(
                phone_number=phone_number,
                user=user,
                first_name=request.data.get('first_name'),
                last_name=request.data.get('last_name'),
                national_id_number=request.data.get('national_id_number'),
                farm_name=request.data.get('farm_name')
            )
        elif role == 'porter':
            PorterProfile.objects.create(
              
                user=user,
                first_name=request.data.get('first_name'),
                last_name=request.data.get('last_name'),
                national_id_number=request.data.get('national_id_number'),
                employee_id=request.data.get('employee_id'),
                route_name=request.data.get('route_name'),
            )

        return Response({
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "phone_number": user.phone_number,
            "message": f"{role.capitalize()} profile created successfully"
        })
        # error caught from the db
    except IntegrityError as e:
        return Response({"error": "Integrity error: " + str(e)})
    except Exception as e:
        return Response({"error": "An error occurred: " + str(e)})

# login
@api_view(['POST'])
@permission_classes([AllowAny])
def Login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    # print(username, password)

    user = authenticate(username=username, password=password)

    if not user:
        return Response({"error": "Invalid credentials"}, status=401)
    
    refresh=RefreshToken.for_user(user)

    return Response({
        "username": user.username,
        "role": user.role,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
       
    })


    # ==============
    # get user/profile
    # ============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def Myprofile(request):
    user = request.user
    print(user)

    profile_data = {}
    if user.role=="farmer" and hasattr(user, 'farmer_profile'):
        p=user.farmer_profile
        profile_data = {
            "first_name": p.first_name,
            "last_name": p.last_name,
            "phone_number": p.phone_number,
            "farm_name": p.farm_name,
}
    elif user.role=="porter" and hasattr(user, 'porter_profile'):
        p=user.porter_profile
        profile_data = {
            "first_name": p.first_name,
            "last_name": p.last_name,
            "employee_id": p.employee_id,
            "route_name": p.route_name,
        }

    return Response({
            "id": user.id,
            "username": user.username, 
            "role": user.role,
            "profile": profile_data
        })


# ===========
# logout
# ==========
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def Logout(request):
    try:
        refresh_token = request.data.get("refresh")
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logout successful"})
    except TokenError:
        return Response({"error":  "invalid or expired token"})
    except Exception as e:
        return Response({"error": str (e)})


  