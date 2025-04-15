from celery import shared_task
from .models import ImageUpload, ProcessingResult
import requests
from django.conf import settings
import os

@shared_task
def process_image_async(image_id):
    try:
        upload = ImageUpload.objects.get(id=image_id)
        
        # Mesmo código de processamento da view, mas assíncrono
        api_url = "https://api.palm-detection.com/process"
        
        with open(upload.image.path, 'rb') as img:
            files = {'image': img}
            response = requests.post(api_url, files=files)
        
        if response.status_code == 200:
            result_data = response.json()
            result = ProcessingResult(
                original_image=upload,
                palm_count=result_data.get('count', 0),
                metadata=result_data
            )
            
            if 'processed_image_url' in result_data:
                img_response = requests.get(result_data['processed_image_url'])
                if img_response.status_code == 200:
                    img_path = os.path.join(settings.MEDIA_ROOT, 'results', f'processed_{upload.id}.jpg')
                    with open(img_path, 'wb') as f:
                        f.write(img_response.content)
                    result.processed_image = f'results/processed_{upload.id}.jpg'
            
            result.save()
            upload.processed = True
            upload.save()
            
            return True
        return False
    except Exception as e:
        print(f"Error processing image {image_id}: {str(e)}")
        return False