import cv2
import numpy as np
from typing import List, Tuple, Optional
from enum import Enum
import math

class Direction(Enum):
    NORTH = "North"
    SOUTH = "South"
    EAST = "East"
    WEST = "West"
    NORTHEAST = "Northeast"
    NORTHWEST = "Northwest"
    SOUTHEAST = "Southeast"
    SOUTHWEST = "Southwest"

class RoadDirectionAnalyzer:
    def __init__(self, mask: np.ndarray, min_branch_length: int = 100):
        """
        Initialize the road direction analyzer
        
        Args:
            mask: Binary mask of the road network
            min_branch_length: Minimum length of road branch to consider
        """
        self.mask = mask
        self.min_branch_length = min_branch_length
        self.height, self.width = mask.shape
        self.skeleton = None
        self.endpoints = None
        self.branches = None
        
    def analyze(self, start_point: Optional[Tuple[int, int]] = None) -> dict:
        """
        Analyze the road network and find possible travel directions
        
        Args:
            start_point: Optional starting point (x, y). If None, uses center of image
            
        Returns:
            Dictionary containing possible directions and their confidence scores
        """
        # Create skeleton of the road network
        self.skeleton = self._create_skeleton()
        
        # Find endpoints and branches
        self.endpoints = self._find_endpoints()
        self.branches = self._find_branches()
        
        # If no start point provided, use image center
        if start_point is None:
            start_point = (self.width // 2, self.height // 2)
            
        # Find nearest road point to start_point
        start_point = self._find_nearest_road_point(start_point)
        
        # Analyze directions from start point
        directions = self._analyze_directions(start_point)
        
        return directions
    
    def visualize(self, original_image: np.ndarray, start_point: Tuple[int, int], 
                 directions: dict) -> np.ndarray:
        """
        Visualize the direction analysis
        
        Args:
            original_image: Original image to draw on
            start_point: Starting point (x, y)
            directions: Dictionary of directions and confidence scores
            
        Returns:
            Image with visualization overlays
        """
        result = original_image.copy()
        
        # Draw skeleton
        skeleton_overlay = cv2.cvtColor(self.skeleton.astype(np.uint8) * 255, cv2.COLOR_GRAY2BGR)
        result = cv2.addWeighted(result, 0.7, skeleton_overlay, 0.3, 0)
        
        # Draw start point
        cv2.circle(result, start_point, 10, (0, 0, 255), -1)
        
        # Draw direction arrows
        arrow_length = 100
        for direction, score in directions.items():
            if score > 0.2:  # Only draw significant directions
                angle = self._direction_to_angle(direction)
                end_point = (
                    int(start_point[0] + arrow_length * math.cos(angle)),
                    int(start_point[1] + arrow_length * math.sin(angle))
                )
                
                # Color based on confidence score (green = high, red = low)
                color = (
                    int(255 * (1 - score)),  # B
                    int(255 * score),        # G
                    0                        # R
                )
                
                cv2.arrowedLine(result, start_point, end_point, color, 2)
                
                # Add confidence score text
                text_point = (
                    int(start_point[0] + (arrow_length + 10) * math.cos(angle)),
                    int(start_point[1] + (arrow_length + 10) * math.sin(angle))
                )
                cv2.putText(result, f"{direction.value}: {score:.2f}", 
                           text_point, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return result
    
    def _create_skeleton(self) -> np.ndarray:
        """Create a skeleton of the road network using morphological operations"""
        skeleton = np.zeros_like(self.mask)
        img = self.mask.copy()
        
        while True:
            # Morphological erosion
            eroded = cv2.erode(img, None)
            # Morphological opening
            opened = cv2.morphologyEx(eroded, cv2.MORPH_OPEN, None)
            # Subtract opened from eroded to get endpoints
            subset = eroded - opened
            # Add endpoints to skeleton
            skeleton = cv2.bitwise_or(skeleton, subset)
            # Eroded image becomes the new image
            img = eroded.copy()
            
            if cv2.countNonZero(img) == 0:
                break
                
        return skeleton
    
    def _find_endpoints(self) -> List[Tuple[int, int]]:
        """Find endpoints in the skeleton"""
        endpoints = []
        
        # Get coordinates of all road pixels
        road_pixels = np.where(self.skeleton > 0)
        
        for y, x in zip(road_pixels[0], road_pixels[1]):
            # Get 3x3 neighborhood
            neighborhood = self.skeleton[max(0, y-1):min(self.height, y+2),
                                      max(0, x-1):min(self.width, x+2)]
            
            # Count neighbors
            if np.sum(neighborhood > 0) == 2:  # Including the pixel itself
                endpoints.append((x, y))
                
        return endpoints
    
    def _find_branches(self) -> List[List[Tuple[int, int]]]:
        """Find road branches in the skeleton"""
        branches = []
        visited = np.zeros_like(self.skeleton)
        
        # Start from each endpoint
        for endpoint in self.endpoints:
            if visited[endpoint[1], endpoint[0]] == 0:
                branch = []
                current = endpoint
                
                while True:
                    branch.append(current)
                    visited[current[1], current[0]] = 1
                    
                    # Get 3x3 neighborhood
                    y, x = current[1], current[0]
                    neighborhood = self.skeleton[max(0, y-1):min(self.height, y+2),
                                              max(0, x-1):min(self.width, x+2)]
                    neighbor_coords = np.where(neighborhood > 0)
                    
                    # Find unvisited neighbors
                    next_points = []
                    for ny, nx in zip(neighbor_coords[0], neighbor_coords[1]):
                        global_x = x + nx - 1
                        global_y = y + ny - 1
                        
                        if (0 <= global_x < self.width and 
                            0 <= global_y < self.height and
                            visited[global_y, global_x] == 0):
                            next_points.append((global_x, global_y))
                    
                    if not next_points:
                        break
                        
                    current = next_points[0]
                
                if len(branch) >= self.min_branch_length:
                    branches.append(branch)
                    
        return branches
    
    def _find_nearest_road_point(self, point: Tuple[int, int]) -> Tuple[int, int]:
        """Find the nearest point on the road to the given point"""
        x, y = point
        road_pixels = np.where(self.skeleton > 0)
        
        min_dist = float('inf')
        nearest_point = point
        
        for ry, rx in zip(road_pixels[0], road_pixels[1]):
            dist = math.sqrt((rx - x) ** 2 + (ry - y) ** 2)
            if dist < min_dist:
                min_dist = dist
                nearest_point = (rx, ry)
                
        return nearest_point
    
    def _analyze_directions(self, start_point: Tuple[int, int]) -> dict:
        """Analyze possible directions from the start point"""
        directions = {direction: 0.0 for direction in Direction}
        
        # For each branch, calculate its contribution to each direction
        for branch in self.branches:
            # Get branch direction relative to start point
            dx = branch[-1][0] - start_point[0]
            dy = branch[-1][1] - start_point[1]
            angle = math.atan2(dy, dx)
            
            # Calculate branch length
            length = len(branch)
            
            # Weight based on distance from start point
            distance = math.sqrt(dx**2 + dy**2)
            weight = 1.0 / (1.0 + distance / 100.0)  # Decay with distance
            
            # Update direction scores
            for direction in Direction:
                direction_angle = self._direction_to_angle(direction)
                angle_diff = abs(self._normalize_angle(angle - direction_angle))
                
                # Score based on angle difference and branch length
                if angle_diff < math.pi / 4:  # Within 45 degrees
                    score = (1.0 - angle_diff / (math.pi / 4)) * weight * (length / self.min_branch_length)
                    directions[direction] = max(directions[direction], score)
        
        # Normalize scores
        max_score = max(directions.values())
        if max_score > 0:
            directions = {d: s/max_score for d, s in directions.items()}
            
        return directions
    
    @staticmethod
    def _direction_to_angle(direction: Direction) -> float:
        """Convert direction to angle in radians"""
        angles = {
            Direction.EAST: 0,
            Direction.NORTHEAST: -math.pi/4,
            Direction.NORTH: -math.pi/2,
            Direction.NORTHWEST: -3*math.pi/4,
            Direction.WEST: math.pi,
            Direction.SOUTHWEST: 3*math.pi/4,
            Direction.SOUTH: math.pi/2,
            Direction.SOUTHEAST: math.pi/4
        }
        return angles[direction]
    
    @staticmethod
    def _normalize_angle(angle: float) -> float:
        """Normalize angle to [-pi, pi]"""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return abs(angle)

def analyze_road_directions(mask: np.ndarray, original_image: np.ndarray, 
                          start_point: Optional[Tuple[int, int]] = None) -> Tuple[dict, np.ndarray]:
    """
    Analyze possible travel directions based on road segmentation
    
    Args:
        mask: Binary mask of the road network
        original_image: Original image for visualization
        start_point: Optional starting point (x, y)
        
    Returns:
        Tuple of (directions dictionary, visualization image)
    """
    analyzer = RoadDirectionAnalyzer(mask)
    directions = analyzer.analyze(start_point)
    visualization = analyzer.visualize(original_image, 
                                    start_point or (mask.shape[1]//2, mask.shape[0]//2),
                                    directions)
    
    return directions, visualization

# Example usage:
if __name__ == "__main__":
    # Load your stitched image and road mask here
    image = cv2.imread('stitched_image.jpg')
    mask = cv2.imread('road_mask.jpg', cv2.IMREAD_GRAYSCALE)
    
    # Analyze directions
    directions, visualization = analyze_road_directions(mask, image)
    
    # Print possible directions and their confidence scores
    for direction, score in directions.items():
        if score > 0.2:  # Only show significant directions
            print(f"{direction.value}: {score:.2f}")
    
    # Show visualization
    cv2.imshow('Direction Analysis', visualization)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
