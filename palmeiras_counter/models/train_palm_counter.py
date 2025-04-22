# models/train_palm_counter.py
import os
import cv2
import numpy as np
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, UpSampling2D
from tensorflow.keras.optimizers import Adam
from sklearn.model_selection import train_test_split

def create_model(input_shape=(256, 256, 3)):
    """Cria um modelo U-Net simplificado para detecção de palmeiras"""
    inputs = Input(input_shape)
    
    # Encoder
    x = Conv2D(32, (3, 3), activation='relu', padding='same')(inputs)
    x = MaxPooling2D((2, 2))(x)
    x = Conv2D(64, (3, 3), activation='relu', padding='same')(x)
    x = MaxPooling2D((2, 2))(x)
    
    # Decoder
    x = Conv2D(64, (3, 3), activation='relu', padding='same')(x)
    x = UpSampling2D((2, 2))(x)
    x = Conv2D(32, (3, 3), activation='relu', padding='same')(x)
    x = UpSampling2D((2, 2))(x)
    
    # Saída
    outputs = Conv2D(1, (1, 1), activation='sigmoid')(x)
    
    model = Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer=Adam(), loss='binary_crossentropy')
    return model

def load_and_preprocess_data(image_dir, mask_dir):
    """Carrega e pré-processa os dados de treinamento"""
    images = []
    masks = []
    
    for img_name in os.listdir(image_dir):
        img_path = os.path.join(image_dir, img_name)
        mask_path = os.path.join(mask_dir, img_name)
        
        img = cv2.imread(img_path)
        img = cv2.resize(img, (256, 256))
        img = img / 255.0
        
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        mask = cv2.resize(mask, (256, 256))
        mask = (mask > 0).astype(np.float32)
        mask = np.expand_dims(mask, axis=-1)
        
        images.append(img)
        masks.append(mask)
    
    return np.array(images), np.array(masks)

def train_model():
    # Carregar dados
    X, y = load_and_preprocess_data('dataset/images', 'dataset/masks')
    
    # Dividir em treino e teste
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    
    # Criar e treinar modelo
    model = create_model()
    model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=20, batch_size=8)
    
    # Salvar modelo
    model.save('palm_counter_model.h5')