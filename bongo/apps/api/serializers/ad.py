from bongo.apps.bongo import models
from rest_framework import serializers


class AdSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Ad
        fields = ('id', 'run_from', 'run_through', 'owner', 'url', 'adfile')
