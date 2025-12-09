import cv2
import numpy as np
import tensorflow as tf
import os

MODEL_PATH = "models/movenet_multipose/movenet_multipose_lightning.tflite"
IMAGE_PATH = "tests/squat_down.jpg"
OUTPUT_PATH = "tests/test_output_keypoints.jpg"

# Verificar existencia de archivos
if not os.path.exists(MODEL_PATH):
    print(f"❌ Modelo no encontrado: {MODEL_PATH}")
    exit(1)

if not os.path.exists(IMAGE_PATH):
    print(f"❌ Imagen no encontrada: {IMAGE_PATH}")
    exit(1)

# Cargar imagen
img = cv2.imread(IMAGE_PATH)
print(f"✅ Imagen cargada: shape={img.shape}")
rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# Cargar modelo TFLite
print("Cargando modelo TFLite...")
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print(f"Input details: {input_details[0]['shape']}, dtype={input_details[0]['dtype']}")
print(f"Output details: {output_details[0]['shape']}, dtype={output_details[0]['dtype']}")

# Preparar imagen para el modelo
input_height = input_details[0]['shape'][1]
input_width = input_details[0]['shape'][2]
input_img = cv2.resize(rgb, (input_width, input_height))
input_tensor = np.expand_dims(input_img.astype(np.uint8), axis=0)  # MultiPose Lightning espera uint8

print(f"Input preparado: shape={input_tensor.shape}, dtype={input_tensor.dtype}")

# Ejecutar inferencia
print("Ejecutando inferencia...")
interpreter.set_tensor(input_details[0]["index"], input_tensor)
interpreter.invoke()

# Obtener output
output = interpreter.get_tensor(output_details[0]['index'])
print(f"Output shape: {output.shape}")  # [1, num_people, 56]

num_people = output.shape[1]

# Iterar sobre personas detectadas
for person_idx in range(num_people):
    person_data = output[0][person_idx]
    
    # Ignorar si persona no detectada (todo cero)
    if np.all(person_data == 0):
        continue

    # Reorganizar keypoints: [17,3] (y, x, confidence)
    keypoints = person_data[:17*3].reshape(17, 3)

    # Dibujar keypoints en la imagen original
    for i, (y_norm, x_norm, confidence) in enumerate(keypoints):
        if confidence > 0.3:
            y = int(y_norm * img.shape[0])
            x = int(x_norm * img.shape[1])
            cv2.circle(img, (x, y), 5, (0, 255, 0), -1)
            cv2.putText(img, f"{i}", (x+5, y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

# Guardar imagen con keypoints
cv2.imwrite(OUTPUT_PATH, img)
print(f"✅ Keypoints dibujados y guardados en: {OUTPUT_PATH}")
