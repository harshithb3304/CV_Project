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
  const [selectedImage, setSelectedImage] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [processedImage, setProcessedImage] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [viewerImage, setViewerImage] = useState(null);
  const [viewerTitle, setViewerTitle] = useState('');
  const [parameters, setParameters] = useState({
    lower_threshold: 100,
    upper_threshold: 200,
    gaussian_size: 5,
    gaussian_sigma: 0
  });

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedImage(file);
      setPreviewUrl(URL.createObjectURL(file));
      setProcessedImage(null);
    }
  };

  const handleParameterChange = async (e) => {
    const { name, value } = e.target;
    const newParameters = { ...parameters, [name]: Number(value) };
    setParameters(newParameters);

    try {
      const response = await fetch('http://127.0.0.1:8080/api/update_parameters', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newParameters),
      });

      if (!response.ok) {
        console.error('Failed to update parameters');
      }
    } catch (error) {
      console.error('Error updating parameters:', error);
    }
  };

  const handleSubmit = async () => {
    if (!selectedImage) {
      setUploadStatus('Please select an image first');
      return;
    }

    const formData = new FormData();
    formData.append('image', selectedImage);

    try {
      setIsProcessing(true);
      setUploadStatus('Processing image...');
      const response = await fetch('http://127.0.0.1:8080/api/process_image', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setUploadStatus('Image processed successfully!');
        setProcessedImage(data.edges);
      } else {
        setUploadStatus(`Error: ${data.error}`);
      }
    } catch (error) {
      setUploadStatus('Error: Network or server error');
      console.error('Error:', error);
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

  return (
    <div className="flex flex-col justify-center items-center min-h-screen bg-gray-100 px-4 py-8">
      <div className="text-3xl lg:text-7xl xl:text-7xl text-center p-4">
        Canny Edge Detection
      </div>

      {/* Parameters Controls */}
      <div className="w-full max-w-6xl mt-8 bg-white p-6 rounded-xl shadow-lg">
        <h2 className="text-xl font-semibold mb-4">Edge Detection Parameters</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="flex flex-col">
            <label className="text-sm text-gray-600 mb-1">Lower Threshold</label>
            <input
              type="number"
              name="lower_threshold"
              value={parameters.lower_threshold}
              onChange={handleParameterChange}
              className="border rounded p-2"
              min="0"
              max="255"
            />
          </div>
          <div className="flex flex-col">
            <label className="text-sm text-gray-600 mb-1">Upper Threshold</label>
            <input
              type="number"
              name="upper_threshold"
              value={parameters.upper_threshold}
              onChange={handleParameterChange}
              className="border rounded p-2"
              min="0"
              max="255"
            />
          </div>
          <div className="flex flex-col">
            <label className="text-sm text-gray-600 mb-1">Gaussian Kernel Size</label>
            <select
              name="gaussian_size"
              value={parameters.gaussian_size}
              onChange={handleParameterChange}
              className="border rounded p-2"
            >
              {[3, 5, 7, 9].map(size => (
                <option key={size} value={size}>{size}x{size}</option>
              ))}
            </select>
          </div>
          <div className="flex flex-col">
            <label className="text-sm text-gray-600 mb-1">Gaussian Sigma</label>
            <input
              type="number"
              name="gaussian_sigma"
              value={parameters.gaussian_sigma}
              onChange={handleParameterChange}
              className="border rounded p-2"
              min="0"
              step="0.1"
              multiple
            />
          </div>
        </div>
      </div>

      {/* Images Container */}
      <div className="flex flex-col lg:flex-row gap-8 w-full max-w-6xl mt-8">
        {/* Original Image Section */}
        <div className="flex-1">
          <h2 className="text-xl font-semibold mb-4 text-center">Original Image</h2>
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
            {previewUrl ? (
              <img 
                src={previewUrl} 
                alt="Selected preview" 
                className="w-full h-full object-fill rounded-xl cursor-pointer hover:opacity-90 transition-opacity" 
                // onClick={() => openImageViewer(previewUrl, 'Original Image')}
              />
            ) : (
              <div className="flex flex-col items-center p-10 rounded-xl">
                <img src="upload.png" alt="upload" className="w-32 h-32 mb-4" />
                <div className="text-gray-500 text-sm sm:text-base px-2">
                  Click or drag image here
                </div>
              </div>
            )}
          </label>
        </div>

        {/* Processed Image Section */}
        <div className="flex-1">
          <h2 className="text-xl font-semibold mb-4 text-center">Edge Detection Result</h2>
          <div className="h-80 bg-white p-6 rounded-xl shadow-lg border-2 border-gray-300">
            {processedImage ? (
              <img 
                src={processedImage} 
                alt="Processed" 
                className="w-full h-full object-contain rounded-xl cursor-pointer hover:opacity-90 transition-opacity" 
                onClick={() => openImageViewer(processedImage, 'Edge Detection Result')}
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-500">
                Processed image will appear here
              </div>
            )}
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
        disabled={!selectedImage || isProcessing}
      >
        {isProcessing ? 'Processing...' : 'Process Image'}
      </button>

      {/* Image Viewer Modal */}
      <ImageViewerModal
        image={viewerImage}
        title={viewerTitle}
        onClose={closeImageViewer}
      />
    </div>
  );
}

export default Page;