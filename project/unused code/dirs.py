import cv2
import numpy as np

def get_road_directions(road_mask):
    """
    Detect the directions of roads from a binary road mask image.
    
    Parameters:
    road_mask (numpy.ndarray): Binary image mask representing the roads.
    
    Returns:
    list: List of detected road directions ('up', 'down', 'left', 'right').
    """
    directions = []

    # Detect vertical roads
    if np.any(road_mask[:, ::10]):
        directions.append('up')
        directions.append('down')

    # Detect horizontal roads
    if np.any(road_mask[::10, :]):
        directions.append('left')
        directions.append('right')

    return directions

def display_road_directions(road_mask, image):
    """
    Display the detected road directions on top of the road map image.
    
    Parameters:
    road_mask (numpy.ndarray): Binary image mask representing the roads.
    image (numpy.ndarray): Road map image to overlay the directions on.
    """
    directions = get_road_directions(road_mask)

    # Create an image to overlay the direction indicators
    overlay = np.zeros_like(image)

    # Draw the direction indicators
    if 'up' in directions:
        cv2.putText(overlay, 'UP', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    if 'down' in directions:
        cv2.putText(overlay, 'DOWN', (10, image.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    if 'left' in directions:
        cv2.putText(overlay, 'LEFT', (10, image.shape[0] // 2), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    if 'right' in directions:
        cv2.putText(overlay, 'RIGHT', (image.shape[1] - 100, image.shape[0] // 2), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # Combine the overlay with the original image
    result = cv2.addWeighted(image, 0.8, overlay, 0.2, 0)

    return result
