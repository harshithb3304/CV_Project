import cv2
import numpy as np
import os
from typing import List, Tuple, Optional

NUM_IMAGES = 7

def load_images():
    images = []
    for i in range(NUM_IMAGES):
        img = cv2.imread(f'image_{i}.png')
        if img is not None:
            images.append(img)
    return images

def stitch_images(images):
    stitcher = cv2.Stitcher_create()
    status, panorama = stitcher.stitch(images)
    return panorama
    

def create_road_mask(image):
    def nothing(x):
        pass

    # Convert image to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = None
    
    low_h = 2
    high_h = 30
    low_s = 0
    high_s = 50
    low_v = 114
    high_v = 245
    
    lower = np.array([low_h, low_s, low_v])
    upper = np.array([high_h, high_s, high_v])
    mask = cv2.inRange(hsv, lower, upper)

    return mask

def clean_mask(mask: np.ndarray, min_area: int = 1000) -> np.ndarray:
    # Create window for trackbars
    window_name = 'Mask Cleanup Controls'
    cv2.namedWindow(window_name)
    
    def nothing(x):
        pass
    
    # Create trackbars for cleaning parameters
    cv2.createTrackbar('Kernel Size', window_name, 3, 20, nothing)
    cv2.createTrackbar('Iterations', window_name, 1, 5, nothing)
    cv2.createTrackbar('Min Area', window_name, 1000, 10000, nothing)
    
    original_mask = mask.copy()
    
    while True:
        # Get current positions of trackbars
        kernel_size = cv2.getTrackbarPos('Kernel Size', window_name)
        iterations = cv2.getTrackbarPos('Iterations', window_name)
        min_area = cv2.getTrackbarPos('Min Area', window_name)
        
        # Ensure kernel size is odd
        kernel_size = kernel_size if kernel_size % 2 == 1 else kernel_size + 1
        
        # Create a clean copy to work with
        cleaned_mask = original_mask.copy()
        
        # 1. Apply morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        
        # Close operation to fill gaps
        cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel, iterations=iterations)
        
        # Open operation to remove small noise
        cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_OPEN, kernel, iterations=iterations)
        
        # 2. Filter contours by area
        contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Create empty mask
        filtered_mask = np.zeros_like(cleaned_mask)
        
        # Draw only contours with area larger than min_area
        for contour in contours:
            area = cv2.contourArea(contour)
            if area >= min_area:
                cv2.drawContours(filtered_mask, [contour], -1, 255, -1)
        
        # 3. Smooth edges
        #filtered_mask = cv2.GaussianBlur(filtered_mask, (5, 5), 0)
        #_, filtered_mask = cv2.threshold(filtered_mask, 127, 255, cv2.THRESH_BINARY)
        
        # Show results
        #cv2.imshow('Original Mask', original_mask)
        cv2.imshow('Cleaned Mask', filtered_mask)
        
        # Press 'q' to finish cleaning
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyWindow('Original Mask')
            cv2.destroyWindow('Cleaned Mask')
            cv2.destroyWindow(window_name)
            return filtered_mask
            
def color_roads(image: np.ndarray, mask: np.ndarray, color: Tuple[int, int, int] = (0, 255, 0)) -> np.ndarray:
    """
    Color the roads in the image using the provided mask
    
    Args:
        image: Input image
        mask: Binary mask of road areas
        color: BGR color tuple for roads (default: green)
    Returns:
        Image with colored roads
    """
    result = image.copy()
    
    # Create color overlay
    color_overlay = np.zeros_like(image)
    color_overlay[mask > 0] = color
    
    # Blend the original image with the color overlay
    alpha = 0.4  # Transparency factor
    result = cv2.addWeighted(result, 1 - alpha, color_overlay, alpha, 0)
    
    return result

def main():
    
    try:
        # Load images
        images = load_images()
        
        # Stitch images
        print("Stitching images...")
        panorama = stitch_images(images)
        if panorama is None:
            raise ValueError("Failed to stitch images")
        
        
        # Create road mask
        print("Creating road mask...")
        print("Adjust the trackbars to create a mask for the roads")
        print("Press 'q' when done")
        road_mask = create_road_mask(panorama)
        
        # Clean up the mask
        print("Cleaning up the mask...")
        print("Adjust the cleanup parameters and press 'q' when satisfied")
        cleaned_mask = clean_mask(road_mask)
        
        # Color the roads
        result = color_roads(panorama, cleaned_mask)
        
        # Show and save result
        cv2.imshow('Final Result', result)
        cv2.imwrite('colored_roads.jpg', result)
        print("Result saved as 'colored_roads.jpg'")
        
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
