import keras
from keras.applications import VGG19
from keras.applications.vgg19 import preprocess_input
from keras import Input
from keras.models import Model
from keras.optimizers import Adam
import numpy as np
from scipy.misc import imresize, imread
from glob import glob
import matplotlib.pyplot as plt
from keras import backend as K
from keras import Sequential
from keras.layers import Conv2D, Dense
import cv2


def sample_images(data_dir, batch_size, high_resolution_shape, low_resolution_shape):
    # Make a list of all images inside the data directory
    all_images = data_dir

    # Choose a random batch of images
    images_batch = np.random.choice(all_images, size=batch_size)

    low_resolution_images = []
    high_resolution_images = []

    for img in images_batch:
        # Get an ndarray of the current image
        img1 = imread(img, mode='RGB')
        img1 = img1.astype(np.float32)

        # Resize the image
        img1_high_resolution = imresize(img1, high_resolution_shape)
        img1_low_resolution = imresize(img1, low_resolution_shape)

        # Do a random horizontal flip
        if np.random.random() < 0.5:
            img1_high_resolution = np.fliplr(img1_high_resolution)
            img1_low_resolution = np.fliplr(img1_low_resolution)

        high_resolution_images.append(img1_high_resolution)
        low_resolution_images.append(img1_low_resolution)

    # Convert the lists to Numpy NDArrays
    return np.array(high_resolution_images), np.array(low_resolution_images)


def build_vgg():
    """
    Builds a pre-trained VGG19 model that outputs image features extracted at the
    third block of the model
    """
    input_shape = (256, 256, 3)
    vgg = VGG19(weights="imagenet")
    print(vgg.summary())
    # Set the outputs to outputs of last conv. layer in block 3
    # See architecture at: https://github.com/keras-team/keras/blob/master/keras/applications/vgg19.py
    vgg.outputs = [vgg.layers[9].output]

    img = Input(shape=input_shape)

    # Extract the image features
    img_features = vgg(img)

    return Model(inputs=[img], outputs=[img_features], name='vgg')


vgg = build_vgg()
vgg.trainable = False
print(vgg.summary())
vgg.compile(optimizer=Adam(lr=0.0002, beta_1=0.9), loss='mse', metrics=['accuracy'])

# Shape of low-resolution and high-resolution images
low_resolution_shape = (64, 64, 3)
high_resolution_shape = (256, 256, 3)

# High and Low resolution inputs to the network
input_high_resolution = Input(shape=high_resolution_shape)
input_low_resolution = Input(shape=low_resolution_shape)

data_dir = glob('./Training_data/*')
batch_size = 1
high_resolution_images, low_resolution_images = sample_images(data_dir=data_dir, batch_size=batch_size,
                                                              high_resolution_shape=high_resolution_shape,
                                                              low_resolution_shape=low_resolution_shape)
high_resolution_images = high_resolution_images / 127.5 - 1
low_resolution_images = low_resolution_images / 127.5 - 1
# print(high_resolution_images.shape)
features = vgg.predict(high_resolution_images)

# print(type(features))
# print(features.shape)
#
# model = Sequential()
# model.add(Conv2D(3, 1, input_shape=(64, 64, 256)))
#
# model.compile(optimizer=Adam(lr=0.1, beta_1=0.9), loss='mse')
#
# features = features.reshape((1, 64, 64, 256))
# print(model.summary())
# o = model.predict(features)
#
# print(o.shape)
# o = o.reshape(64, 64, 3)
# o = 0.5 * o + 0.5
#
# high_resolution_images = high_resolution_images.reshape(256, 256, 3)
# high_resolution_images = 0.5 * high_resolution_images + 0.5
# print(high_resolution_images.shape)
#
# fig = plt.figure()
# ax = fig.add_subplot(1, 2, 1)
# ax.imshow(high_resolution_images)
# ax.axis("off")
# ax.set_title("High-resolution")
#
# ax = fig.add_subplot(1, 2, 2)
# ax.imshow(o)
# ax.axis("off")
# ax.set_title("Features")
# plt.show()

### NEW METHOD ###
high_resolution_images = high_resolution_images.reshape(256, 256, 3)
high_resolution_images = 0.5 * high_resolution_images + 0.5

# fig = plt.figure()
# plt.imshow(high_resolution_images)
# plt.axis("off")
# plt.title("High-resolution")
#
# square = 16
# index = 1
# fig = plt.figure()
# for _ in range(square):
#     for _ in range(square):
#         ax = fig.add_subplot(square, square, index)
#         ax.imshow(features[0, :, :, index - 1], cmap='viridis')
#         ax.axis("off")
#
#         index += 1
#
# plt.show()

smooth = cv2.GaussianBlur(high_resolution_images, (5, 5), 0)
smooth = np.expand_dims(smooth, axis=0)
smooth_features = vgg.predict(smooth)
smooth = np.squeeze(smooth, axis=0)

kernel = np.ones((5, 5), np.float32)/25
dst = cv2.filter2D(high_resolution_images, -1, kernel)
print(dst.shape)
dst = np.expand_dims(dst, axis=0)
d_features = vgg.predict(dst)
dst = np.squeeze(dst, axis=0)
print(d_features.shape)

fig = plt.figure()
ax = fig.add_subplot(3, 2, 1)
ax.imshow(high_resolution_images)
ax.axis("off")
ax.set_title("High-resolution")

ax = fig.add_subplot(3, 2, 2)
ax.imshow(features[0, :, :, 1], cmap='viridis')
ax.axis("off")
ax.set_title("Features")

ax = fig.add_subplot(3, 2, 3)
ax.imshow(smooth)
ax.axis("off")
ax.set_title("Gaussian Blur")

ax = fig.add_subplot(3, 2, 4)
ax.imshow(smooth_features[0, :, :, 1], cmap='viridis')
ax.axis("off")
ax.set_title("Features after Gaussian Blur")

ax = fig.add_subplot(3, 2, 5)
ax.imshow(dst)
ax.axis("off")
ax.set_title("Conv2d")

ax = fig.add_subplot(3, 2, 6)
ax.imshow(d_features[0, :, :, 1], cmap='viridis')
ax.axis("off")
ax.set_title("Features after Conv2d")
plt.show()