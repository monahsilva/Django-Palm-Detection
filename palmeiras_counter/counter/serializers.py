from rest_framework import serializers # type: ignore
from .models import ImageUpload, ProcessingResult

class ImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageUpload
        fields = ['id', 'image', 'uploaded_at', 'processed']

class ProcessingResultSerializer(serializers.ModelSerializer):
    original_image = ImageUploadSerializer()
    
    class Meta:
        model = ProcessingResult
        fields = ['id', 'original_image', 'processed_image', 'palm_count', 'processed_at', 'metadata']