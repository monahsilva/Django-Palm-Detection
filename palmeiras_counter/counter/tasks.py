import cv2
import numpy as np
from celery import shared_task
from django.conf import settings
from .models import ImageUpload, ProcessingResult
import os
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Conv2D
from tensorflow.keras.applications import EfficientNetB0

def create_advanced_model():
    """Cria um modelo baseado em EfficientNet para melhor precisão, achei no artigo 5"""
    base = EfficientNetB0(include_top=False, input_shape=(256, 256, 3), weights='imagenet')
    base.trainable = False  # Congela as camadas do EfficientNet
    
    x = base.output
    x = Conv2D(1, (1, 1), activation='sigmoid')(x)
    return Model(inputs=base.input, outputs=x)

def get_model():
    """Cacheia o modelo em memória"""
    if not hasattr(get_model, 'model'):
        model_path = os.path.join(settings.BASE_DIR, 'models', 'palm_counter_advanced.h5')
        if not os.path.exists(model_path):
            # Cria e salva o modelo se não existir
            model = create_advanced_model()
            model.save(model_path)
        get_model.model = load_model(model_path)
    return get_model.model

def preprocess_image(img, target_size=(256, 256)):
    """Pré-processamento da imagem"""
    img = cv2.resize(img, target_size)
    img = img / 255.0  # Normalização
    return np.expand_dims(img, axis=0)  # Adiciona dimensão do batch

def post_process(prediction):
    """Pós-processamento para melhorar a contagem"""
    # Converte predição para formato OpenCV
    prediction = (prediction.squeeze() > 0.5).astype(np.uint8) * 255
    
    # Remove pequenos ruídos
    kernel = np.ones((3,3), np.uint8)
    cleaned = cv2.morphologyEx(prediction, cv2.MORPH_OPEN, kernel)
    
    # Encontra contornos
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return len(contours), contours

def draw_boxes(image, contours):
    """Desenha bounding boxes na imagem original"""
    image = image.copy()
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
    return image

# --- Tarefa Celery Principal ---
@shared_task(bind=True, max_retries=3)
def process_image_async(self, image_id):
    try:
        upload = ImageUpload.objects.get(id=image_id)
        image_path = upload.image.path
        original_img = cv2.imread(image_path)
        
        # Pré-processamento
        img = preprocess_image(original_img)
        
        # Predição
        model = get_model()
        prediction = model.predict(img)
        
        # Pós-processamento e contagem
        count, contours = post_process(prediction)
        
        # Gera imagem com bounding boxes
        processed_img = draw_boxes(original_img, contours)
        processed_path = os.path.join(settings.MEDIA_ROOT, 'processed', f'processed_{image_id}.jpg')
        os.makedirs(os.path.dirname(processed_path), exist_ok=True)
        cv2.imwrite(processed_path, processed_img)
        
        # Salva resultados
        result = ProcessingResult(
            original_image=upload,
            palm_count=count,
            processed_image=f'processed/processed_{image_id}.jpg',
            processed=True
        )
        result.save()
        
        upload.processed = True
        upload.save()
        
        return True

    except Exception as e:
        self.retry(exc=e, countdown=60)