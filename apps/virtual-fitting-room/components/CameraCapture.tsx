'use client';

import { useRef, useState, useCallback, useEffect } from 'react';

interface CameraCaptureProps {
  onCapture: (images: string[]) => void;
  label: string;
  multiShot?: boolean;
}

export default function CameraCapture({ onCapture, label, multiShot = false }: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [shots, setShots] = useState<string[]>([]);
  const [stream, setStream] = useState<MediaStream | null>(null);

  // Debug: Log state changes
  useEffect(() => {
    console.log('🔄 [CameraCapture] isStreaming changed:', isStreaming);
  }, [isStreaming]);

  useEffect(() => {
    console.log('📸 [CameraCapture] shots changed:', shots.length);
  }, [shots]);

  const startCamera = useCallback(async () => {
    console.log('🎥 [CameraCapture] startCamera called');
    console.log('🎥 [CameraCapture] videoRef.current:', videoRef.current);

    try {
      console.log('🎥 [CameraCapture] Requesting camera access...');
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'user',
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      });

      console.log('✅ [CameraCapture] Got mediaStream:', mediaStream);
      console.log('🎥 [CameraCapture] Video tracks:', mediaStream.getVideoTracks());

      if (videoRef.current) {
        console.log('✅ [CameraCapture] videoRef.current exists, setting srcObject');
        videoRef.current.srcObject = mediaStream;
        setStream(mediaStream);
        setIsStreaming(true);
        console.log('✅ [CameraCapture] Camera started successfully!');
      } else {
        console.error('❌ [CameraCapture] videoRef.current is null!');
        alert('Chyba: video element nenalezen');
      }
    } catch (err) {
      console.error('❌ [CameraCapture] Error accessing camera:', err);
      alert('Nelze přistoupit ke kameře: ' + (err as Error).message);
    }
  }, []);

  const stopCamera = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
      setIsStreaming(false);
    }
  }, [stream]);

  const takeShot = useCallback(() => {
    if (!videoRef.current) return;

    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    const ctx = canvas.getContext('2d');

    if (ctx) {
      ctx.drawImage(videoRef.current, 0, 0);
      const imageData = canvas.toDataURL('image/jpeg', 0.95);

      if (multiShot) {
        setShots(prev => [...prev, imageData]);
      } else {
        setShots([imageData]);
        stopCamera();
        onCapture([imageData]);
      }
    }
  }, [multiShot, stopCamera, onCapture]);

  const retakeShot = useCallback(() => {
    setShots([]);
    if (!isStreaming) {
      startCamera();
    }
  }, [isStreaming, startCamera]);

  const finishMultiShot = useCallback(() => {
    if (shots.length > 0) {
      stopCamera();
      onCapture(shots);
    }
  }, [shots, stopCamera, onCapture]);

  const removeShot = useCallback((index: number) => {
    setShots(prev => prev.filter((_, i) => i !== index));
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">{label}</h3>
        {multiShot && shots.length > 0 && (
          <span className="text-sm text-gray-600">
            {shots.length} {shots.length === 1 ? 'záběr' : 'záběry'}
          </span>
        )}
      </div>

      {/* Video Preview */}
      <div className={`relative bg-black rounded-lg overflow-hidden ${isStreaming ? '' : 'hidden'}`}>
        <video
          ref={videoRef}
          autoPlay
          playsInline
          className="w-full h-auto"
        />
      </div>

      {/* Captured Shots Preview */}
      {shots.length > 0 && (
        <div className="grid grid-cols-3 gap-2">
          {shots.map((shot, index) => (
            <div key={index} className="relative group">
              <img
                src={shot}
                alt={`Záběr ${index + 1}`}
                className="w-full h-auto rounded border-2 border-green-500"
              />
              <button
                onClick={() => removeShot(index)}
                className="absolute top-1 right-1 bg-red-500 text-white rounded-full w-6 h-6 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                ×
              </button>
              <span className="absolute bottom-1 left-1 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded">
                {index + 1}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Controls */}
      <div className="flex gap-2">
        {!isStreaming && shots.length === 0 && (
          <button
            onClick={() => {
              console.log('🖱️ [CameraCapture] "Spustit kameru" button clicked');
              startCamera();
            }}
            className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
          >
            📷 Spustit kameru
          </button>
        )}

        {isStreaming && (
          <>
            <button
              onClick={takeShot}
              className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition"
            >
              📸 {multiShot ? 'Další záběr' : 'Vyfotit'}
            </button>

            {multiShot && shots.length > 0 && (
              <button
                onClick={finishMultiShot}
                className="flex-1 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition"
              >
                ✓ Hotovo ({shots.length})
              </button>
            )}

            <button
              onClick={stopCamera}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition"
            >
              ⏹ Stop
            </button>
          </>
        )}

        {!isStreaming && shots.length > 0 && (
          <button
            onClick={retakeShot}
            className="flex-1 bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition"
          >
            🔄 Opakovat
          </button>
        )}
      </div>
    </div>
  );
}
