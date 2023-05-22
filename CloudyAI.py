import tensorflow as tf
import numpy as np


def predict(image_path):
    interpreter = tf.lite.Interpreter(model_path="model_240.tflite")
    classifier = interpreter.get_signature_runner("serving_default")

    img = tf.keras.utils.load_img(image_path, target_size=(240, 240))
    img_array = tf.keras.utils.img_to_array(img)
    img_array = tf.expand_dims(img_array, 0)

    predictions = classifier(sequential_input=img_array)["outputs"]
    score = tf.nn.softmax(predictions[0])

    class_names = ["between", "cloudy", "sunny"]

    return class_names[np.argmax(score)], 100 * np.max(score)
