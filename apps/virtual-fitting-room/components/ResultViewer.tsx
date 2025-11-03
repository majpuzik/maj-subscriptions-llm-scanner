'use client';

import { useState } from 'react';
import Image from 'next/image';

interface ResultViewerProps {
  imageUrl: string;
  loading?: boolean;
}

export default function ResultViewer({ imageUrl, loading = false }: ResultViewerProps) {
  const [rotation, setRotation] = useState(0);
  const [zoom, setZoom] = useState(1);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl p-6">
      <h3 className="text-xl font-bold mb-4 text-gray-800 dark:text-white">
        ✨ Výsledek
      </h3>

      {/* Controls */}
      <div className="mb-4 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            🔄 Rotace: {rotation}°
          </label>
          <input
            type="range"
            min="-180"
            max="180"
            value={rotation}
            onChange={(e) => setRotation(Number(e.target.value))}
            className="w-full"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            🔍 Zoom: {zoom.toFixed(1)}x
          </label>
          <input
            type="range"
            min="0.5"
            max="3"
            step="0.1"
            value={zoom}
            onChange={(e) => setZoom(Number(e.target.value))}
            className="w-full"
          />
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => { setRotation(0); setZoom(1); }}
            className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors text-gray-800 dark:text-white"
          >
            🔄 Reset
          </button>
          <button
            onClick={() => window.open(imageUrl, '_blank')}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            📥 Stáhnout
          </button>
        </div>
      </div>

      {/* Image Display */}
      <div className="relative bg-gray-100 dark:bg-gray-900 rounded-lg overflow-hidden min-h-[500px] flex items-center justify-center">
        {loading ? (
          <div className="text-center">
            <div className="animate-spin text-6xl mb-4">⏳</div>
            <p className="text-gray-600 dark:text-gray-400">Zpracovávám...</p>
          </div>
        ) : (
          <div
            style={{
              transform: `rotate(${rotation}deg) scale(${zoom})`,
              transition: 'transform 0.3s ease',
            }}
            className="relative max-w-full max-h-[500px]"
          >
            <img
              src={imageUrl}
              alt="Virtual Try-On Result"
              className="max-w-full max-h-[500px] object-contain rounded-lg"
            />
          </div>
        )}
      </div>

      {/* Info */}
      <div className="mt-4 text-center text-sm text-gray-600 dark:text-gray-400">
        💡 Tip: Použijte ovládací prvky výše pro rotaci a zoom
      </div>
    </div>
  );
}
