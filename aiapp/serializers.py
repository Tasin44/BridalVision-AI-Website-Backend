from rest_framework import serializers
from .models import Dress, TryOn

class DressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dress
        fields = "__all__"


class TryOnSerializer(serializers.ModelSerializer):
    class Meta:
        model = TryOn
        fields = "__all__"