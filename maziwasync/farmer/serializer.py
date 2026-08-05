from rest_framework import serializers

from core.models import FarmerProfile, MilkCollection, Feedback

class MilkCollectionSerializer(serializers.ModelSerializer):
    porter_name = serializers.SerializerMethodField()

    class Meta:
        model = MilkCollection
        fields = ['id', 'litres', 'session', 'price_per_litre', 'total_amount', 'collection_date', 'porter_name']

# use it when you want to alter the field on how it looks like in a model


        

    def get_porter_name(self, obj):
        return f"{obj.porter.first_name} {obj.porter.last_name}"
        
        

        # Feedback serializer
class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
                model= Feedback
                fields=['id','title','description', 'status', 'created_at', 'updated_at']
                read_only_fields=['status','created_at','updated_at']

class FarmerSerializer(serializers.ModelSerializer):
	email = serializers.EmailField(source='user.email', read_only=True)

	class Meta:
		model = FarmerProfile
		fields = [
			'id', 'user', 'email', 'first_name', 'last_name',
			'national_id_number', 'phone_number', 'farm_name',
			'farm_size_acres', 'number_of_cows', 'membership_number',
			'join_date', 'mpesa_number', 'total_milk_delivered',
			'total_earnings',
		]                