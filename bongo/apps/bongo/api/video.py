from bongo.apps.bongo.models import Video
from bongo.apps.bongo.serializers import VideoSerializer
from rest_framework import generics

class VideoList(generics.ListCreateAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer

class VideoDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
