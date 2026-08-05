from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.models import FarmerProfile, PorterProfile, Notice

User = get_user_model()


class FarmerSerializer(serializers.ModelSerializer):
	email = serializers.EmailField(source='user.email', read_only=True)
	username = serializers.CharField(write_only=True, required=False)
	password = serializers.CharField(write_only=True, min_length=8, required=False)

	class Meta:
		model = FarmerProfile
		fields = [
			'id', 'user', 'username', 'password', 'email',
			'first_name', 'last_name', 'national_id_number', 'phone_number',
			'farm_name', 'farm_size_acres', 'number_of_cows',
			'membership_number', 'join_date', 'mpesa_number',
			'total_milk_delivered', 'total_earnings',
		]
		read_only_fields = ['user', 'join_date', 'total_milk_delivered', 'total_earnings']

	def create(self, validated_data):
		username = validated_data.pop('username')
		password = validated_data.pop('password')

		user = User.objects.create_user(
			username=username,
			password=password,
			role='farmer',
			phone_number=validated_data.get('phone_number'),
			first_name=validated_data.get('first_name', ''),
			last_name=validated_data.get('last_name', ''),
		)

		farmer = FarmerProfile.objects.create(user=user, **validated_data)
		return farmer


class PorterSerializer(serializers.ModelSerializer):
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


class NoticeSerializer(serializers.ModelSerializer):
	class Meta:
		model = Notice
		fields = '__all__'
		read_only_fields = ['created_by']