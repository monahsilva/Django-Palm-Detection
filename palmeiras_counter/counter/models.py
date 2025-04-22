from django.db import models

class ImageUpload(models.Model):
    image = models.ImageField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Imagem: {self.id} - {'Processando' if self.processed else 'Esperando'}"

class ProcessingResult(models.Model):
    original_image = models.OneToOneField(ImageUpload, on_delete=models.CASCADE)
    processed_image = models.ImageField(upload_to='results/', null=True, blank=True)
    palm_count = models.IntegerField(null=True, blank=True)
    processed_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)  # Para armazenar dados adicionais da API
    
    def __str__(self):
        return f"Resultado da imagem {self.original_image.id} - {self.palm_count} palmeiras"
