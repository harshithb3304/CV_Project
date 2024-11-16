from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
from cannyedge import ImageProcessor
from seg import load_images, stitch_images, create_road_mask, clean_mask, color_roads, display_road_directions, ResizeWithAspectRatio
import cv2
import base64

app = Flask(__name__)
CORS(app)

# Create base directories if they don't exist
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER


def create_upload_subfolder():
    """Create a timestamped subfolder for uploads"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    subfolder_path = os.path.join(UPLOAD_FOLDER, f'upload_batch_{timestamp}')
    os.makedirs(subfolder_path, exist_ok=True)
    return subfolder_path


@app.route("/api/process_image", methods=["POST"])
def process_image_route():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image file in request"}), 400

        files = request.files.getlist('image')
        if not files or len(files) == 0:
            return jsonify({"error": "No files provided"}), 400

        print(f"Received {len(files)} files for processing.")

        # Create subfolder and save images
        upload_subfolder = create_upload_subfolder()
        image_paths = []

        for i, file in enumerate(files):
            if file.filename == '':
                return jsonify({"error": f"File {i+1} has no name"}), 400

            file_path = os.path.join(upload_subfolder, f'image_{i}.png')
            file.save(file_path)
            image_paths.append(file_path)

        # Process images using seg.py functions
        images = load_images(image_paths)
        panorama = stitch_images(images)
        road_mask = create_road_mask(panorama)
        cleaned_mask = clean_mask(road_mask)
        result = color_roads(panorama, cleaned_mask)
        final_result, directions = display_road_directions(cleaned_mask, panorama)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'processed_{timestamp}.jpg'
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        # Save to output folder
        cv2.imwrite(output_path, final_result)

        # Convert to base64
        _, buffer = cv2.imencode('.jpg', final_result)
        image_base64 = base64.b64encode(buffer).decode('utf-8')

        return jsonify({
            "message": "Images processed successfully",
            "processed_image": f"data:image/jpeg;base64,{image_base64}",
            "image_path": output_path,
            "directions": list(directions)
        }), 200

    except Exception as e:
        print(f"Error processing images: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=8080)
