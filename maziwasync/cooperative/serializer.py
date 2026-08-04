from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.models import FarmerProfile, PorterProfile, Notice

User = get_user_model()


# admin/cooperative farmer account
class FarmerSerializer(serializers.ModelSerializer):
	class Meta:
		model = FarmerProfile
		fields = '__all__'


class PorterSerializer(serializers.ModelSerializer):
	# these belong to the User model, not PorterProfile — accept them here,
	# then use them in create() to build the linked User account
	username = serializers.CharField(write_only=True)
	password = serializers.CharField(write_only=True, min_length=8)
	phone_number = serializers.CharField(write_only=True, required=False, allow_blank=True)

class Meta:
    model = PorterProfile
    fields = [
        'id', 'username', 'password', 'phone_number',
        'first_name', 'last_name', 'national_id_number',
        'employee_id', 'route_name', 'profile_image',
        'hire_date', 'is_active', 'total_collections',
        'total_litres_collected',
    ]
    read_only_fields = [
        'hire_date', 'total_collections', 'total_litres_collected'
    ]

def create(self, validated_data):
		username = validated_data.pop('username')
		password = validated_data.pop('password')
		phone_number = validated_data.pop('phone_number', None)

		user = User.objects.create_user(
			username=username,
			password=password,
			role='porter',
			phone_number=phone_number,
			first_name=validated_data.get('first_name', ''),
			last_name=validated_data.get('last_name', ''),
		)

		porter = PorterProfile.objects.create(user=user, **validated_data)
		return porter


# Notice
class NoticeSerializer(serializers.ModelSerializer):
	class Meta:
		model = Notice
		fields = '__all__'
		read_only_fields = ['created_by']