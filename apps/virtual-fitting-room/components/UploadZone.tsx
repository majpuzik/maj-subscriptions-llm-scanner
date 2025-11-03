'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';

interface UploadZoneProps {
  onFileSelect: (file: File | null) => void;
  accept?: string;
  label?: string;
  type?: 'person' | 'clothing';
}

export default function UploadZone({ onFileSelect, accept = 'image/*', label = 'Nahrajte soubor', type = 'clothing' }: UploadZoneProps) {
  const [preview, setPreview] = useState<string | null>(null);
  const [showUrlInput, setShowUrlInput] = useState(false);
  const [urlInput, setUrlInput] = useState('');
  const [downloading, setDownloading] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      onFileSelect(file);

      // Create preview
      const reader = new FileReader();
      reader.onload = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: accept.split(',').reduce((acc, curr) => {
      acc[curr.trim()] = [];
      return acc;
    }, {} as Record<string, string[]>),
    multiple: false,
  });

  const handleDownloadFromUrl = async () => {
    if (!urlInput.trim()) {
      alert('Zadejte URL obrázku');
      return;
    }

    setDownloading(true);

    try {
      const response = await fetch('/api/download-image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: urlInput,
          name: `url-download-${Date.now()}.jpg`,
          type: type,
        }),
      });

      const data = await response.json();

      if (data.success) {
        // Create a File object from the downloaded image
        const imgResponse = await fetch(data.url);
        const blob = await imgResponse.blob();
        const file = new File([blob], 'downloaded.jpg', { type: blob.type });

        onFileSelect(file);
        setPreview(data.url);
        setShowUrlInput(false);
        setUrlInput('');
      } else {
        // Check if it's a 403 error (blocked)
        if (data.error.includes('403')) {
          alert('❌ Web blokuje automatické stahování.\n\n💡 Řešení:\n1. Otevři URL v novém okně\n2. Pravým tlačítkem → "Uložit obrázek jako..."\n3. Nahraj ho pomocí drag & drop výše');
        } else {
          alert('Chyba při stahování: ' + data.error);
        }
      }
    } catch (error) {
      console.error('Download error:', error);
      alert('Nepodařilo se stáhnout obrázek');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="space-y-2">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all
          ${isDragActive
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500'
          }
        `}
      >
        <input {...getInputProps()} />

        {preview ? (
          <div className="space-y-2">
            <img
              src={preview}
              alt="Preview"
              className="max-h-48 mx-auto rounded-lg object-cover"
            />
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Klikněte nebo přetáhněte pro změnu
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="text-4xl">📁</div>
            <p className="text-gray-600 dark:text-gray-400">
              {isDragActive ? 'Pusťte soubor zde...' : label}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-500">
              nebo klikněte pro výběr
            </p>
          </div>
        )}
      </div>

      {/* URL Download Section */}
      {showUrlInput ? (
        <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg space-y-2" onClick={(e) => e.stopPropagation()}>
          <input
            type="url"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            placeholder="https://example.com/image.jpg"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white text-sm"
            onKeyPress={(e) => e.key === 'Enter' && handleDownloadFromUrl()}
            disabled={downloading}
          />
          <div className="flex gap-2">
            <button
              onClick={handleDownloadFromUrl}
              disabled={downloading}
              className="flex-1 px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 text-sm"
            >
              {downloading ? '⏳ Stahuji...' : '⬇ Stáhnout'}
            </button>
            <button
              onClick={() => { setShowUrlInput(false); setUrlInput(''); }}
              className="px-3 py-1.5 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-white rounded-md hover:bg-gray-400 dark:hover:bg-gray-500 text-sm"
            >
              ✕
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={(e) => { e.stopPropagation(); setShowUrlInput(true); }}
          className="w-full px-3 py-2 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-md transition-colors"
        >
          🔗 Nebo stáhnout z URL
        </button>
      )}
    </div>
  );
}
