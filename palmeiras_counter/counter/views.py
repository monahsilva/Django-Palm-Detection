from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import ImageUpload, ProcessingResult
from .serializers import ImageUploadSerializer, ProcessingResultSerializer
import requests
from django.conf import settings
import os

@api_view(['POST'])
def upload_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image_file = request.FILES['image']
        
        upload = ImageUpload(image=image_file)
        upload.save()
        
        # Chamar tarefa assíncrona
        from .tasks import process_image_async
        process_image_async.delay(upload.id)
        
        return Response({
            'message': 'Image uploaded and queued for processing',
            'image_id': upload.id
        }, status=status.HTTP_202_ACCEPTED)
    
    return Response({
        'error': 'No image provided'
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_result(request, pk):
    try:
        result = ProcessingResult.objects.get(pk=pk)
        serializer = ProcessingResultSerializer(result)
        return Response(serializer.data)
    except ProcessingResult.DoesNotExist:
        return Response({
            'error': 'Result not found'
        }, status=status.HTTP_404_NOT_FOUND)

def upload_view(request):
    return render(request, 'counter/upload.html')

def history_view(request):
    results = ProcessingResult.objects.all().order_by('-processed_at')
    has_results = results.exists()
    context = {
        'results': results,
        'has_results': has_results,  
        'total_count': results.count(),
        'total_palms': sum(r.palm_count for r in results if r.palm_count),
        'average': round(sum(r.palm_count for r in results if r.palm_count) / results.count(), 1) if results.count() > 0 else 0
    }
    return render(request, 'counter/history.html', context)

def settings_view(request):
    return render(request, 'counter/settings.html')

def statistic_view(request):
    return render(request, 'counter/statistic.html')