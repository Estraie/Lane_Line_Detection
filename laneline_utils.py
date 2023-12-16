import edge_detection as ed
import numpy as np

def filter_colors(image, form = "jpg"):
    red_channel = image[:, :, 0]
    green_channel = image[:, :, 1]
    blue_channel = image[:, :, 2]

    white_yellow_mask = ((red_channel >= 200) & (green_channel >= 200) & (blue_channel >= 200)) \
        | ((red_channel >= 150) & (green_channel >= 100) & (blue_channel <= 130) \
           & (green_channel - blue_channel >= 50)  & (red_channel - blue_channel >= 50))

    filtered_image = np.zeros_like(red_channel)
    filtered_image[white_yellow_mask] = 255

    return filtered_image

def line_detect(image, threshold = 60, neighborhood_size = 10):
    accumulator, theta_vals, rho_vals = ed.hough_transform(image)
    peaks = ed.find_hough_peaks(accumulator, threshold = threshold, neighborhood_size = neighborhood_size)
    return peaks

def region_of_interest(edges, vertices):
    pass

def annotate_image(
    image, 
    form = "jpg", 
    is_gray = False,
    blur_kernel_size = 3,
    blur_sigma = 1,
    dev_kernel_size = 7,
    dev_sigma = 0.4
):
    if not is_gray:
        img = filter_colors(image, form = form)
    
    img = ed.edge_detect(
        img, 
        is_gray = is_gray,
        blur_kernel_size = blur_kernel_size,
        blur_sigma = blur_sigma,
        dev_kernel_size = dev_kernel_size,
        dev_sigma = dev_sigma,
        lower_threshold = 5, 
        upper_threshold = 12,
        form = form
    )
    
    imshape = image.shape
    vertices = np.array([[\
        ((imshape[1] * (1 - trap_bottom_width)) // 2, imshape[0]),\
        ((imshape[1] * (1 - trap_top_width)) // 2, imshape[0] - imshape[0] * trap_height),\
        (imshape[1] - (imshape[1] * (1 - trap_top_width)) // 2, imshape[0] - imshape[0] * trap_height),\
        (imshape[1] - (imshape[1] * (1 - trap_bottom_width)) // 2, imshape[0])]]\
        , dtype=np.int32)
    
    img = region_of_interest(img, vertices)
    
    img = hough_lines(masked_edges, rho, theta, threshold, min_line_length, max_line_gap)
    
    initial_image = image.astype('uint8')
    annotated_image = weighted_img(line_image, initial_image)
    
    return annotated_image
    
    