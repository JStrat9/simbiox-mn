# detectors/movenet_inference.py

import cv2
import numpy as np
import tensorflow as tf
from typing import List, Optional

class MoveNet:
    """
    Wrapper para MoveNet TFLite (Lightning o Thunder) con
    funciones de inferencia y preprocesamiento.
    """

    def __init__(self, model_path: str):
        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        
        # Resize input tensor to expected shape and reallocate
        self.interpreter.resize_tensor_input(0, [1, 256, 256, 3])
        self.interpreter.allocate_tensors()
        
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        # Infer input shape and dtype
        input_shape = self.input_details[0]['shape']  # [1, H, W, 3]
        self.input_height = int(input_shape[1])
        self.input_width = int(input_shape[2])
        self.input_dtype = self.input_details[0]['dtype']
        # quantization params (scale, zero_point) for input/output
        self.input_quant = self.input_details[0].get('quantization', (0.0, 0))
        self.output_quant = self.output_details[0].get('quantization', (0.0, 0))
        print(f"[DEBUG] MoveNet input dtype={self.input_dtype}, quant={self.input_quant}")
        print(f"[DEBUG] MoveNet output dtype={self.output_details[0]['dtype']}, quant={self.output_quant}")

    def run(self, frame: np.ndarray) -> List[np.ndarray]:
        """
        Ejecuta MoveNet sobre un frame BGR y devuelve
        lista de keypoints, cada uno shape (17,3) [y, x, score].
        """

        if frame is None:
            return []

        img_resized = cv2.resize(frame, (self.input_width, self.input_height))
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)

        if self.input_dtype == np.uint8:
            input_tensor = np.expand_dims(img_rgb.astype(np.uint8), axis=0)
        else:
            input_tensor = np.expand_dims(img_rgb.astype(np.float32)/255.0, axis=0)

        self.interpreter.set_tensor(self.input_details[0]['index'], input_tensor)
        self.interpreter.invoke()
        output = self.interpreter.get_tensor(self.output_details[0]['index'])
        # output shape: [1, num_people, 56] (MultiPose)
        output = np.copy(output)
        # If output is quantized, dequantize using scale and zero_point
        out_scale, out_zp = self.output_quant
        if out_scale and out_zp is not None and np.issubdtype(self.output_details[0]['dtype'], np.integer):
            output = out_scale * (output.astype(np.float32) - out_zp)

        # Debug: print sample ranges
        if output.size == 0:
            print("[DEBUG] MoveNet output empty")
        else:
            print("[DEBUG] MoveNet output shape:", output.shape)
            sample = output[0][0]
            print("[DEBUG] sample[:12]:", np.round(sample[:12], 4))
            kp0 = sample[:51].reshape((17,3))
            print("[DEBUG] kp0 y range:", kp0[:,0].min(), kp0[:,0].max())
            print("[DEBUG] kp0 x range:", kp0[:,1].min(), kp0[:,1].max())
            print("[DEBUG] kp0 conf range:", kp0[:,2].min(), kp0[:,2].max())
            if sample.shape[0] > 55:
                print("[DEBUG] pose score:", float(sample[55]))

        if output.size == 0:
            print("[DEBUG] MoveNet output empty")
        else:
            print("[DEBUG] MoveNet output shape:", output.shape)
            # inspect first detected person
            sample = output[0][0]
            print("[DEBUG] sample[:12]:", np.round(sample[:12], 4))
            kp0 = sample[:51].reshape((17,3))
            print("[DEBUG] kp0 y range:", kp0[:,0].min(), kp0[:,0].max())
            print("[DEBUG] kp0 x range:", kp0[:,1].min(), kp0[:,1].max())
            print("[DEBUG] kp0 conf range:", kp0[:,2].min(), kp0[:,2].max())
            if sample.shape[0] > 55:
                print("[DEBUG] pose score:", float(sample[55]))
        

        people = []
        for person_raw in output[0]:
            keypoints = person_raw[:51].reshape((17,3))  # 17 keypoints * 3
            score = person_raw[55]  # pose score
            if score > 0.01:
                people.append(keypoints)
        return people