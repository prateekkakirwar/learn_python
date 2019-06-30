import tensorflow
import numpy
import tqdm
import os
import sys
import pandas

tensorflow.enable_eager_execution(config=tensorflow.ConfigProto(allow_soft_placement=True, gpu_options=tensorflow.GPUOptions(allow_growth=True)))

os.environ["CUDA_VISIBLE_DEVICES"] = '0'
model_name = 'converted_model'
model_dir = 'estimator_model'

(train_image, train_label), (test_image, test_label) = tensorflow.keras.datasets.mnist.load_data()
test_image = test_image.reshape(-1, 28, 28, 1).astype(numpy.float32)
train_image = (train_image - 127.5) / 128
test_label = test_label.astype(numpy.int32)

interpreter = tensorflow.lite.Interpreter(model_path=os.path.join(model_dir, model_name) + '.tflite')
interpreter.allocate_tensors()

input_index = interpreter.get_input_details()[0]["index"]
output_index = interpreter.get_output_details()[0]["index"]

total = 0
for image, label in zip(test_image, test_label):
    interpreter.set_tensor(input_index, image.reshape(-1, 28, 28))
    interpreter.invoke()
    predict = interpreter.get_tensor(output_index)
    if predict == label:
        total = total + 1
print(total / test_image.shape[0])