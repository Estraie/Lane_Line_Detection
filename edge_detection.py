import numpy as np
import pandas as pd
from scipy.ndimage import convolve, convolve1d

def rgb_to_gray(image):
    """Generate a gray scale image from an RGB(A) image."""
    return (np.dot(image[..., :3], [0.299, 0.587, 0.114]) * 255).astype(np.uint8)

def gaussian_kernel(size, sigma = 1.0):
    """Generate a Gaussian kernel with standard deviation = sigma within the interval [-size, size]."""
    kernel = np.fromfunction(
        lambda x, y: (1/ (2 * np.pi * sigma ** 2)) * np.exp(- ((x - (size - 1) / 2) ** 2 + (y - (size - 1) / 2) ** 2) / (2 * sigma ** 2)),
        (size, size)
    )
    return kernel / np.sum(kernel)

def gaussian_blur(image, kernel_size, sigma):
    """Apply Guassian Blurring to the image."""
    kernel = gaussian_kernel(kernel_size, sigma)
    return convolve(image, kernel)

def gaussian_derivative_kernel(size, sigma, order = 1):
    """Generate a 1D Gaussian derivative kernel."""
    if size % 2 == 0:
        size += 1
    kernel = np.fromfunction(
        lambda x: (x - (size - 1) / 2) * np.exp(-((x - (size - 1) / 2) ** 2) / (2 * sigma ** 2)),
        (size,)
    )
    kernel = (-1) ** order * kernel / (np.sqrt(2 * np.pi) * sigma ** 3)
    return kernel / np.sum(np.abs(kernel)) 

def apply_gradient_operator(image, kernel):
    """Apply the gradient operator to the image using the provided kernels."""
    gradient_x = convolve1d(image, kernel, axis = -1, mode = 'reflect')
    gradient_y = convolve1d(image, kernel, axis = -2, mode = 'reflect')
    return gradient_x, gradient_y

def non_max_suppression(gradient_x, gradient_y):
    """Apply non-max suppression (NMS) to the image using its gradient images."""
    gradient_magnitude = np.sqrt(gradient_x ** 2 + gradient_y ** 2)
    gradient_direction = np.arctan2(gradient_y, gradient_x)

    rows, cols = gradient_magnitude.shape
    result = np.zeros_like(gradient_magnitude, dtype=np.uint8)

    for i in range(1, rows - 2):
        j = np.arange(1, cols - 2)
        mag = gradient_magnitude[i, j]
        angle = gradient_direction[i, j] % np.pi

        t = np.abs(np.tan(angle))
        mask = (-1 < t) & (t < 1)

        x1, y1 = i - 1, (j[mask] - t[mask]).astype(int)
        x2, y2 = i - 1, (j[mask] - t[mask] + 1).astype(int)
        x3, y3 = i + 1, (j[mask] + t[mask] + 1).astype(int)
        x4, y4 = i + 1, (j[mask] + t[mask]).astype(int)

        c1 = (1 - t[mask]) * gradient_magnitude[x1, y1] + t[mask] * gradient_magnitude[x2, y2]
        c2 = (1 - t[mask]) * gradient_magnitude[x3, y3] + t[mask] * gradient_magnitude[x4, y4]
        mask2 = np.zeros_like(mask, dtype = bool)
        mask2[mask] = (mag[mask] >= c1) & (mag[mask] >= c2)
        result[i, j[mask2]] = mag[mask2]
        
        mask = (-1 >= t) | (t >= 1)
        
        t = 1 / t
        x1, y1 = (i - t[mask]).astype(np.int16), j[mask] - 1
        x2, y2 = (i - t[mask] + 1).astype(np.int16), j[mask] - 1
        x3, y3 = (i + t[mask] + 1).astype(np.int16), j[mask] + 1
        x4, y4 = (i + t[mask]).astype(np.int16), j[mask] + 1

        c1 = (1 - t[mask]) * gradient_magnitude[x1, y1] + t[mask] * gradient_magnitude[x2, y2]
        c2 = (1 - t[mask]) * gradient_magnitude[x3, y3] + t[mask] * gradient_magnitude[x4, y4]

        mask2 = np.zeros_like(mask, dtype = bool)
        mask2[mask] = (mag[mask] >= c1) & (mag[mask] >= c2)
        result[i, j[mask2]] = mag[mask2]

    return result

def thinning_double_threshold(img, t1 = 5, t2 = 13):
    """Applying double threshold thinning algorithm to the image."""
    result = np.zeros_like(img)
    strong_edges = img >= t2
    weak_edges = (img >= t1) & (img < t2)

    result[strong_edges] = 255
    result[~(strong_edges | weak_edges)] = 0  

    for i in range(1, img.shape[0] - 1):
        for j in range(1, img.shape[1] - 1):
            if weak_edges[i, j]:
                if np.any(strong_edges[i - 1 : i + 2, j - 1 : j + 2]):
                    result[i, j] = 255
                    
    return result

def get_neighbors(img, i, j):
    """Retrieve the 8 neighbours of the pixel img[i, j]."""
    rows, cols = img.shape
    neighbors = []

    for x in range(max(0, i - 1), min(i + 2, rows)):
        for y in range(max(0, j - 1), min(j + 2, cols)):
            if x != i or y != j:
                neighbors.append(img[x, y])

    return np.array(neighbors)[np.array([1, 2, 4, 7, 6, 5, 3, 0])]

def thinning_zhangsuen(img):
    """Apply Zhang-Suen Thinning algorithm （张太怡-孫靖夷细化算法） to the image."""
    # 效果一般，速度贼慢
    img = img.copy()
    rows, cols = img.shape

    to_be_processed = np.column_stack(np.where(img == 1))

    i = 0
    while i < 20:
        i += 1
        to_delete = []
        
        # Iteration 1
        for point in to_be_processed:
            i, j = point
            neighbors = get_neighbors(img, i, j)
            
            # The indices of neighbors:
            # P9 P2 P3
            # P8 P1 P4
            # P7 P6 P5
            # Criterion 1A: 2 <= #(Neighbor == 1) >= 6
            # Criterion 1B: #(0 -> 1 when iterating using indices above) == 1
            # Criterion 1C: P2 * P4 * P6 == 0
            # Criterion 1D: P4 * P6 * P8 == 0
            if          (2 <= np.sum(neighbors) <= 6) \
                    and (sum(neighbors[i] == 0 and neighbors[(i + 1) % 8] == 1 for i in range(0, 8)) == 1) \
                    and (neighbors[1] * neighbors[3] * neighbors[5] == 0) \
                    and (neighbors[3] * neighbors[5] * neighbors[7] == 0):
                to_delete.append(point)
                
        for point in to_delete:
            img[point[0], point[1]] = 0    
            
        to_be_processed = np.delete(to_be_processed, to_delete, axis=0)
        
        if len(to_delete) == 0:
            break
            
        to_delete = []
        
        # Iteration 2
        for point in to_be_processed:
            i, j = point
            neighbors = get_neighbors(img, i, j)
            
            # Criterion 2A: 2 <= #(Neighbor == 1) >= 6
            # Criterion 2B: #(0 -> 1 when iterating using indices above) == 1
            # Criterion 2C: P2 * P4 * P8 == 0
            # Criterion 2D: P2 * P6 * P8 == 0
            if          (2 <= np.sum(neighbors) <= 6) \
                    and (sum(neighbors[i] == 0 and neighbors[(i + 1) % 8] == 1 for i in range(0, 8)) == 1) \
                    and (neighbors[1] * neighbors[3] * neighbors[7] == 0) \
                    and (neighbors[1] * neighbors[5] * neighbors[7] == 0):
                to_delete.append(point)
                
        for point in to_delete:
            img[point[0], point[1]] = 0    
            
        to_be_processed = np.delete(to_be_processed, to_delete, axis=0)
        
        if len(to_delete) == 0:
            break

    return img

def calculate_angle_image(grad_x, grad_y):
    """Return the image whose elements are arctan(grad_y / grad_x)."""
    return np.arctan2(grad_y, grad_x)

# def gaussian_blur_color(image, kernel_size, sigma):
#     """Apply Gaussian blur to a three-channel image."""
#     result = np.zeros_like(image, dtype=np.float32)
#     for i in range(image.shape[2]):
#         result[..., i] = gaussian_blur(image[..., i], kernel_size, sigma)
#     return result

# def compute_all_channels_gradients(image, kernel):
#     """Compute gradients for all channels and combine them."""
#     all_gradients_x = np.zeros_like(image, dtype=np.float32)
#     all_gradients_y = np.zeros_like(image, dtype=np.float32)

#     for i in range(image.shape[-1]):
#         channel = image[..., i]
#         gradients_x, gradients_y = apply_gradient_operator(channel, kernel)
#         all_gradients_x[..., i] = gradients_x
#         all_gradients_y[..., i] = gradients_y

#     return all_gradients_x, all_gradients_y

# def non_max_suppression(gradient_x, gradient_y):
#     gradient_magnitude = np.sqrt(gradient_x ** 2 + gradient_y ** 2)
#     gradient_direction = np.arctan2(gradient_y, gradient_x)
#     rows, cols = gradient_magnitude.shape
#     result = np.ones_like(gradient_magnitude)
#     print("Done 1")
#     angle_quantized = np.round(gradient_direction / (np.pi/4)) % 4

#     for i in range(1, rows-2):
#         if i % 400 == 0:
#             print(f"Done {i}")
#         for j in range(1, cols-2):
#             mag = gradient_magnitude[i, j]
#             direction = angle_quantized[i, j]

#             if direction == 0 and (mag >= gradient_magnitude[i, j-1]) and (mag >= gradient_magnitude[i, j+1]):
#                 result[i, j] = 0
#             elif direction == 1 and (mag >= gradient_magnitude[i-1, j+1]) and (mag >= gradient_magnitude[i+1, j-1]):
#                 result[i, j] = 0
#             elif direction == 2 and (mag >= gradient_magnitude[i-1, j]) and (mag >= gradient_magnitude[i+1, j]):
#                 result[i, j] = 0
#             elif direction == 3 and (mag >= gradient_magnitude[i-1, j-1]) and (mag >= gradient_magnitude[i+1, j+1]):
#                 result[i, j] = 0

#     return result

# def nms(gradient_magnitude, gradient_direction):
#     rows, cols = gradient_magnitude.shape
#     result = np.zeros_like(gradient_magnitude)
#     print("Done 1")
#     angle_quantized = np.round(gradient_direction / (np.pi/4)) % 4

#     for i in range(1, rows-2):
#         if i % 400 == 0:
#             print(f"Done {i}")
#         for j in range(1, cols-2):
#             mag = gradient_magnitude[i, j]
#             direction = angle_quantized[i, j]

#             if direction == 0 and (mag >= gradient_magnitude[i, j-1]) and (mag >= gradient_magnitude[i, j+1]):
#                 result[i, j] = mag
#             elif direction == 1 and (mag >= gradient_magnitude[i-1, j+1]) and (mag >= gradient_magnitude[i+1, j-1]):
#                 result[i, j] = mag
#             elif direction == 2 and (mag >= gradient_magnitude[i-1, j]) and (mag >= gradient_magnitude[i+1, j]):
#                 result[i, j] = mag
#             elif direction == 3 and (mag >= gradient_magnitude[i-1, j-1]) and (mag >= gradient_magnitude[i+1, j+1]):
#                 result[i, j] = mag

#     return result
