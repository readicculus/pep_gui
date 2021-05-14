import cv2
import numpy as np
import kwiver.vital.types as kvt


def ocv_load(image_fp):
    return cv2.imread(image_fp, cv2.IMREAD_UNCHANGED)

def ocv_load_normed(image_fp):
    im = ocv_load(image_fp)
    im_norm = ((im - np.min(im)) / (0.0 + np.max(im) - np.min(im)))
    im_norm = im_norm * 255.0
    im_norm = im_norm.astype(np.uint8)
    return im_norm

def load_image_kvr_container(fp, load_fn):
    im = load_fn(fp)
    np_image = np.array(im)
    vital_im = kvt.Image(np_image)
    im_container = kvt.ImageContainer(vital_im)
    return im_container

