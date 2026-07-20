from rest_framework import serializers
from core.models import MilkCollection

# porter serializer for the milk collection
class MilkCollectionSerializer(serializers.ModelSerializer):
    farmer_name = serializers.SerializerMethodField()
    national_id_number = serializers.CharField(
        source='farmer.national_id_number',
        read_only=True
    )

    class Meta:
        model = MilkCollection
        fields = [
            'id',
            'national_id_number',
            'farmer_name',
            'litres',
            'session',
            'total_amount',
            'collection_date',
        ]

    def get_farmer_name(self, obj):
        return f"{obj.farmer.first_name} {obj.farmer.last_name}"
    


    # 
class RecentCollectionSeriliazer(serializers.ModelSerializer):
        farmer_name=serializers.SerializerMethodField()
        class Meta:
            model= MilkCollection
            fields=['id', 'farmer_name', 'litres', 'session', 'collection_date', 'total_amount']
            def get_farmer_name(self, obj):
                return f"{obj.farmer.first_name} {obj.faarmer.last_name}"
