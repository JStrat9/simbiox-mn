import tensorflow as tf
import numpy as np

interpreter = tf.lite.Interpreter(model_path="models/movenet_multipose/movenet_multipose_lightning.tflite")
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print("Modelo cargado correctamente.")
print("Input shape:", input_details[0]['shape'])
print("Output shape:", output_details[0]['shape'])
