import os

from imutils import contours
from skimage import measure
import numpy as np
import imutils
import cv2
import tensorflow as tf
import pandas as pd


def normalize(input_image, input_mask):
    input_image = tf.cast(input_image, tf.float32) / 255.0
    input_mask -= 1
    return input_image, input_mask


def find_images(data_dir:str, extension: str) -> list:
    """
    Return list of image filenames
    :param data_dir:
    :return:
    """
    images = []
    dir_files = os.listdir(data_dir)
    for f in dir_files:
        if f'.{extension}' in f:
            images.append(f)
    return images


class ImageProcessor:
    def __init__(self, params):
        self.params = params
        self.images = []
        self.masks = []

    def convert_greyscale(self):
        image_count = len(self.images)
        current_image = 1
        for image in self.images:
            image_path = f'./data/01_raw/{image}'

            loaded_image = cv2.imread(image_path)
            gray = cv2.cvtColor(loaded_image, cv2.COLOR_BGR2GRAY)

            # save grayscale image
            save_path = f'./data/03_primary/images/gs_{image}'
            cv2.imwrite(save_path, gray)

            contrast = cv2.equalizeHist(gray)
            blurred = cv2.GaussianBlur(contrast, (11, 11), 0)
            thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.erode(thresh, None, iterations=2)
            thresh = cv2.dilate(thresh, None, iterations=4)

            # save mask image
            save_path = f'./data/03_primary/masks/gs_{image}'
            cv2.imwrite(save_path, thresh)
            print(image)
            print(f'Converted image to grayscale: \t {current_image}/{image_count}')
            current_image += 1

    def convert_mask_to_array(self):
        """
        Convert mask input image into numpy array
        :return:
        """
        mask_count = len(self.masks)
        current_mask = 1
        for mask in self.masks:
            image_path = f'./data/03_primary/masks/{mask}'
            loaded_mask = cv2.imread(image_path)
            # Convert BGR to RGB
            rgb_mask = cv2.cvtColor(loaded_mask, cv2.COLOR_BGR2RGB)
            # Convert RGB to gray
            gray_mask = cv2.cvtColor(rgb_mask, cv2.COLOR_RGB2GRAY)

            # save mask array
            save_path = f'./data/03_primary/arrays/gs_{mask}'
            np.save(save_path, gray_mask)
            print(f'Converted mask to array: \t {current_mask}/{mask_count}')
            current_mask += 1

    def run(self):
        image_ext = self.params['IMAGE_EXT']

        if self.params['GENERATE_MASKS']:
            self.images = find_images(
                data_dir='./data/01_raw/',
                extension=image_ext
            )
            self.convert_greyscale()

        if self.params['GENERATE_ARRAYS']:
            self.masks = find_images(
                data_dir='./data/03_primary/masks/',
                extension=image_ext
            )
            self.convert_mask_to_array()
