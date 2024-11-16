import cv2
import numpy as np
import os
from typing import List, Tuple, Optional

NUM_IMAGES = 6


def ResizeWithAspectRatio(image, width=2560, height=None, inter=cv2.INTER_AREA):
    dim = None
    (h, w) = image.shape[:2]

    if width is None and height is None:
        return image
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))

    return cv2.resize(image, dim, interpolation=inter)

def load_images(image_paths: List[str]) -> List[np.ndarray]:
    images = []
    for image_path in image_paths:
        img = cv2.imread(image_path)
        if img is not None:
            images.append(img)
    return images


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
    
    resized_mask = ResizeWithAspectRatio(mask)
    #cv2.imshow('Mask', resized_mask)
    #cv2.waitKey(0)
    return mask

def stitch_images(images):
    stitcher = cv2.Stitcher_create()
    status, panorama = stitcher.stitch(images)
    print(f"Panorama Generated")
    return panorama

def clean_mask(mask: np.ndarray, min_area: int = 1000) -> np.ndarray:
    original_mask = mask.copy()
    cleaned_mask = original_mask.copy()
    
    # 1. Apply morphological operations
    kernel_size = 1
    iterations = 1
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
    
    return filtered_mask

def color_roads(image, mask, color = (0, 255, 0)):
    result = image.copy()
    
    # Create color overlay
    color_overlay = np.zeros_like(image)
    color_overlay[mask > 0] = color
    
    # Blend the original image with the color overlay
    alpha = 0.4  # Transparency factor
    result = cv2.addWeighted(result, 1 - alpha, color_overlay, alpha, 0)
    
    return result

def display_road_directions(road_mask, image):

    image_center = (road_mask.shape[1] // 2, road_mask.shape[0] // 2)

    contour_data = cv2.findContours(road_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contour_data[0] if len(contour_data) == 2 else contour_data[1]

    labeled_directions = set()

    for contour in contours:
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            continue  # Skip contour if area == 0

        dx = cx - image_center[0]
        dy = image_center[1] - cy  # Reverse y to make positive angles upwards
        angle = np.arctan2(dy, dx) * 180 / np.pi

        # Determine the direction based on the angle
        if -15 <= angle <= 15:
            direction = "East"
        elif 15 < angle <= 75:
            direction = "Northeast"
        elif 75 < angle <= 105:
            direction = "North"
        elif 105 < angle <= 190:
            direction = "Northwest"
        elif angle > 190 or angle < -165:
            direction = "West"
        elif -165 < angle <= -105:
            direction = "Southwest"
        elif -105 < angle <= -75:
            direction = "South"
        elif -75 < angle <= -15:
            direction = "Southeast"
        
        if direction not in labeled_directions:
            cv2.putText(image, direction, (cx, cy), 
                        cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 0, 255), 5)
            labeled_directions.add(direction)
    
    return image, labeled_directions


def main():
    
    try:
        # Load images
        images = load_images()
        if len(images) < 2:
            print("Need at least two images to perform stitching")
            exit()
            
        # Stitch images
        print("Stitching images...")
        panorama = stitch_images(images)
        cv2.imwrite('stitched_image.jpg', panorama)
        
        # Create road mask
        road_mask = create_road_mask(panorama)
        
        
        cleaned_mask = clean_mask(road_mask)
        cv2.imwrite('road_mask.jpg', cleaned_mask)
        
        # Color the roads
        result = color_roads(panorama, cleaned_mask)
                
        # Show and save result
        resized_result = ResizeWithAspectRatio(result)
        cv2.imshow('Colored Roads', resized_result)
        cv2.waitKey(0)
        
        cv2.imwrite('colored_roads.jpg', result)
        print("Result saved as 'colored_roads.jpg'")
        
        result2, directions = display_road_directions(cleaned_mask, panorama)
        resized_result2 = ResizeWithAspectRatio(result2)
        cv2.imshow('Final Result', resized_result2)
        cv2.waitKey(0)
        cv2.imwrite('final.jpg', result2)
        print("Result saved as 'final.jpg'")
        print(directions)
        print("End of Program")
        
        
        cv2.destroyAllWindows()
        
        return
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
