import edge_detection as ed
import numpy as np

def filter_colors(image, mask, form = "jpg"):
    color_mask = mask(image)

    filtered_image = np.zeros_like(image[:, :, 0])
    filtered_image[color_mask] = 255

    return filtered_image

def white_mask(image, form = "jpg"):
    red_channel = image[:, :, 0]
    green_channel = image[:, :, 1]
    blue_channel = image[:, :, 2]

    return ((red_channel >= 200) & (green_channel >= 200) & (blue_channel >= 200))

def yellow_mask(image, form = "jpg"):
    red_channel = image[:, :, 0]
    green_channel = image[:, :, 1]
    blue_channel = image[:, :, 2]

    return ((red_channel >= 150) & (green_channel >= 100) & (blue_channel <= 130) \
           & (green_channel - blue_channel >= 50)  & (red_channel - blue_channel >= 50)) \
           & ~ ((red_channel >= 200) & (green_channel >= 200) & (blue_channel >= 200)) 

def line_detect(image, threshold = 60, neighborhood_size = 10):
    accumulator, theta_vals, rho_vals = ed.hough_transform(image)
    peaks = ed.find_hough_peaks(
        accumulator, theta_vals, rho_vals, 
        threshold = threshold, 
        neighborhood_size = neighborhood_size
    )
    return peaks

def region_of_interest(edges, vertices):
    pass

def find_image_lines(
    image, 
    form = "jpg", 
    blur_kernel_size = 5,
    blur_sigma = 1,
    dev_kernel_size = 9,
    dev_sigma = 0.4
):
    img_yellow = filter_colors(image, mask = yellow_mask, form = form)
    img_white = filter_colors(image, mask = white_mask, form = form)
    
    img_yed = ed.edge_detect(
        img_yellow, 
        is_gray = True,
        blur_kernel_size = blur_kernel_size,
        blur_sigma = blur_sigma,
        dev_kernel_size = dev_kernel_size,
        dev_sigma = dev_sigma,
        lower_threshold = 5, 
        upper_threshold = 12,
        form = form
    )
    
    img_wed = ed.edge_detect(
        img_white, 
        is_gray = True,
        blur_kernel_size = blur_kernel_size,
        blur_sigma = blur_sigma,
        dev_kernel_size = dev_kernel_size,
        dev_sigma = dev_sigma,
        lower_threshold = 5, 
        upper_threshold = 12,
        form = form
    )
    yellow_peaks = line_detect(img_yed, threshold = 60)
    white_peaks = line_detect(img_wed, threshold = 60)
    
    return white_peaks, yellow_peaks
    
    