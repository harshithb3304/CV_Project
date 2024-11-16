"use client"
import React, { useState } from 'react';
import { X } from 'lucide-react';

const ImageViewerModal = ({ image, title, onClose }) => {
  if (!image) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4">
      <div className="relative w-full max-w-7xl bg-white rounded-lg shadow-xl">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="text-xl font-semibold text-gray-900">{title}</h3>
          <button
            onClick={onClose}
            className="text-gray-600 hover:text-gray-900 focus:outline-none"
          >
            <X size={24} />
          </button>
        </div>
        <div className="relative p-4 bg-gray-100 flex items-center justify-center" style={{ minHeight: '80vh' }}>
          <img
            src={image}
            alt={title}
            className="max-w-full max-h-[80vh] object-contain"
          />
        </div>
      </div>
    </div>
  );
};

const Page = () => {
  const [selectedImages, setSelectedImages] = useState([]);
  const [previewUrls, setPreviewUrls] = useState([]);
  const [processedImages, setProcessedImages] = useState({});
  const [imageError, setImageError] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [viewerImage, setViewerImage] = useState(null);
  const [viewerTitle, setViewerTitle] = useState('');

  const handleImageChange = (e) => {
    const files = Array.from(e.target.files);
    setSelectedImages((prevImages) => [...prevImages, ...files]);

    const newPreviewUrls = files.map((file) => URL.createObjectURL(file));
    setPreviewUrls((prevUrls) => [...prevUrls, ...newPreviewUrls]);
  };

  const removeImage = (index) => {
    setSelectedImages(prev => prev.filter((_, i) => i !== index));
    setPreviewUrls(prev => {
      URL.revokeObjectURL(prev[index]);
      return prev.filter((_, i) => i !== index);
    });
  };

  const clearImageStates = () => {
    previewUrls.forEach(url => URL.revokeObjectURL(url));
    setSelectedImages([]);
    setPreviewUrls([]);
    setImageError(false);
  };

  const handleSubmit = async () => {
    if (selectedImages.length === 0) {
      setUploadStatus('Please select at least one image');
      return;
    }

    setIsProcessing(true);
    setUploadStatus('Processing images...');

    try {
      const formData = new FormData();
      selectedImages.forEach((image) => {
        formData.append('image', image);
      });

      const response = await fetch('http://127.0.0.1:8080/api/process_image', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (response.ok && data.processed_images) {
        setProcessedImages(data.processed_images);
        setUploadStatus('Images processed successfully!');
        clearImageStates(); // Clear selected images after successful processing
      } else {
        setUploadStatus(`Error processing images: ${data.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Processing error:', error);
      setUploadStatus('Error: Network or server error');
    } finally {
      setIsProcessing(false);
    }
  };

  const openImageViewer = (image, title) => {
    setViewerImage(image);
    setViewerTitle(title);
  };

  const closeImageViewer = () => {
    setViewerImage(null);
    setViewerTitle('');
  };

  //const labels= ['Stitched image', 'Masked image', 'Colored Road Image', 'Final Image'];

  return (
    <div className="flex flex-col justify-center items-center min-h-screen bg-gray-100 px-4 py-8">
      <div className="text-3xl lg:text-7xl xl:text-7xl text-center p-4">
        Road Intersection Pathfinding using Stitching and Segmentation
      </div>

      <div className="w-full max-w-6xl mt-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Original Images Section */}
          <div>
            <h2 className="text-xl font-semibold mb-4">Original Images</h2>
            <label
              htmlFor="input-file"
              className="flex flex-col justify-center items-center p-6 h-80 bg-white text-center rounded-xl shadow-lg hover:cursor-pointer border-2 border-dashed border-gray-300 hover:border-red-500 transition-colors"
            >
              <input
                type="file"
                accept="image/*"
                id="input-file"
                className="hidden"
                onChange={handleImageChange}
                multiple
              />
              <div className="flex flex-col items-center p-4 rounded-xl">
                <img src="upload.png" alt="upload" className="w-16 h-16 mb-2" />
                <div className="text-gray-500 text-sm">
                  Click or drag images here
                </div>
              </div>
            </label>

            <div className="grid gap-4 p-4 cursor-pointer">
              {previewUrls.map((url, index) => (
                <div key={index} className="relative bg-white p-2 rounded-xl shadow-lg">
                  <button
                    onClick={() => removeImage(index)}
                    className="absolute top-4 right-4 bg-red-500 text-white rounded-full p-1 hover:bg-red-600"
                  >
                    <X size={16} />
                  </button>
                  <img
                    src={url}
                    alt={`Preview ${index + 1}`}
                    className="w-full h-48 object-contain rounded"
                    onClick={() => openImageViewer(url, `Original Image ${index + 1}`)}
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Processed Images Section */}
          <div>
            <h2 className="text-xl font-semibold mb-4">Result</h2>
            <div className="bg-white rounded-xl shadow-lg">
              {Object.keys(processedImages).length > 0 ? (
                <div className="grid gap-4 p-4">
                  {Object.entries(processedImages).map(([key, value], index) => (
                    <div key={index} className="relative bg-white p-2 rounded-xl shadow-lg">
                      <img
                        src={value}
                        alt={`Processed ${index + 1}`}
                        className="w-full h-48 object-contain rounded cursor-pointer"
                        onClick={() => openImageViewer(value, `Processed Image ${index + 1}`)}
                        onError={() => {
                          console.error('Image loading error');
                          setImageError(true);
                        }}
                      />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="w-full h-80 flex items-center justify-center text-gray-500 bg-gray-50 rounded">
                  {isProcessing ? (
                    'Processing...'
                  ) : (
                    <div className="flex flex-col items-center">
                      <div className="text-lg mb-2">Awaiting processing</div>
                      <div className="text-sm text-gray-400">Upload and process images to see results</div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {uploadStatus && (
        <div className={`mt-6 p-3 rounded-lg ${
          uploadStatus.includes('Error')
            ? 'bg-red-100 text-red-700'
            : uploadStatus.includes('success')
            ? 'bg-green-100 text-green-700'
            : 'bg-blue-100 text-blue-700'
        }`}>
          {uploadStatus}
        </div>
      )}

      <button
        className="p-4 mt-6 bg-black rounded-lg text-center text-white w-40 hover:bg-gray-800 disabled:bg-gray-400 disabled:cursor-not-allowed"
        onClick={handleSubmit}
        disabled={selectedImages.length === 0 || isProcessing}
      >
        {isProcessing ? 'Processing...' : 'Process Images'}
      </button>

      <ImageViewerModal
        image={viewerImage}
        title={viewerTitle}
        onClose={closeImageViewer}
      />
    </div>
  );
};

export default Page;