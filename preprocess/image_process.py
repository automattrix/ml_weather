import os
from skimage.draw import line
from imutils import contours
from skimage import measure
from skimage.transform import (hough_line, hough_line_peaks)
from math import ceil
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

    def rotate_images(self):
        # https://stackoverflow.com/a/56675787
        # https: // scikit - image.org / docs / dev / auto_examples / edges / plot_line_hough_transform.html
        image_count = len(self.images)
        current_image = 1
        for image in self.images:
            image_path = f'./data/01_raw/{image}'
            # Load Image
            loaded_image = cv2.imread(image_path)
            # Convert to grayscale
            gray = cv2.cvtColor(loaded_image, cv2.COLOR_BGR2GRAY)
            # Convert non-black pixels to pure white. Creates white box (image) on black background
            thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)[1]
            # Smooth
            thresh = cv2.erode(thresh, None, iterations=2)
            thresh = cv2.dilate(thresh, None, iterations=4)
            # Resize
            thresh = cv2.resize(thresh, (0, 0), fx=0.25, fy=0.25)
            # Find edges of white box
            edges = cv2.Canny(thresh, 100, 200)
            img = edges
            row_length = len(img[0]) - 1

            # Draw a horizontal line to use to create an angle with the satellite image border
            width, height = img.shape
            thickness = 5
            y_offset = int(ceil(height/2))
            for x in range(1, thickness):
                rr, cc = line(x+y_offset, 1, x+y_offset, row_length)
                img[rr, cc] = 1

            # Crop image (only working with top half)
            y = 0
            x = 0
            h = height - int(ceil(height/2))
            w = width
            crop = img[y:y + h, x:x + w]

            # Perform Hough Transformation to detect lines
            hspace, angles, distances = hough_line(crop)

            # Find angle
            angle = []
            for _, a, distances in zip(*hough_line_peaks(hspace, angles, distances)):
                angle.append(a)
            # Obtain angle for each line
            angles = [a * 180 / np.pi for a in angle]

            # Rotate image to make it line up square
            rotated = imutils.rotate(loaded_image, angles[0])

            # Save image
            save_path = f'./data/02_preprocessing/rotated_{image}'
            cv2.imwrite(save_path, rotated)

            print(f'Fixed image rotation: \t {current_image}/{image_count}')
            current_image += 1

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

        # Rotate image
        if self.params['PREPROCESS_IMGS']:
            self.images = find_images(
                data_dir='./data/01_raw/',
                extension=image_ext
            )
            self.rotate_images()

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
