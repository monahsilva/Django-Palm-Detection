# counter/tasks.py
from celery import shared_task
import requests
from django.conf import settings
from .models import ImageUpload, ProcessingResult
import os
import cv2
import numpy as np
from tensorflow.keras.models import load_model

@shared_task(bind=True, max_retries=3)
def process_image_async(self, image_id):
    try:
        # 1. Obter a imagem do banco de dados
        upload = ImageUpload.objects.get(id=image_id)
        
        # 2. Carregar a imagem
        image_path = upload.image.path
        img = cv2.imread(image_path)
        
        # 3. Pré-processamento
        img = preprocess_image(img)
        
        # 4. Carregar modelo (cacheado para melhor performance)
        model = get_model()
        
        # 5. Fazer a predição
        count = predict_palm_trees(model, img)
        
        # 6. Salvar resultados
        result = ProcessingResult(
            original_image=upload,
            palm_count=count,
            processed=True
        )
        result.save()
        
        # 7. Atualizar status do upload
        upload.processed = True
        upload.save()
        
        return True
    
    except Exception as e:
        # Se falhar, tenta novamente até 3 vezes
        self.retry(exc=e, countdown=60)

def get_model():
    """Cacheia o modelo em memória para evitar recarregar a cada requisição"""
    if not hasattr(get_model, 'model'):
        model_path = os.path.join(settings.BASE_DIR, 'models', 'palm_counter_model.h5')
        get_model.model = load_model(model_path)
    return get_model.model

def preprocess_image(img, target_size=(256, 256)):
    """Pré-processa a imagem para o formato esperado pelo modelo"""
    img = cv2.resize(img, target_size)
    img = img / 255.0  # Normalização
    img = np.expand_dims(img, axis=0)  # Adiciona dimensão do batch
    return img

def predict_palm_trees(model, img):
    """Faz a predição usando o modelo carregado"""
    predictions = model.predict(img)
    return int(np.sum(predictions > 0.5))  # Conta pixels acima do threshold