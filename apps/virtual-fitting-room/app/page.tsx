'use client';

import { useState } from 'react';
import UploadZone from '@/components/UploadZone';
import CameraCapture from '@/components/CameraCapture';
import ResultViewer from '@/components/ResultViewer';
import HistoryPanel from '@/components/HistoryPanel';

type CaptureMode = 'upload' | 'camera';

export default function Home() {
  const [personImage, setPersonImage] = useState<File | null>(null);
  const [clothingImage, setClothingImage] = useState<File | null>(null);
  const [personCameraShots, setPersonCameraShots] = useState<string[]>([]);
  const [clothingCameraShots, setClothingCameraShots] = useState<string[]>([]);
  const [personName, setPersonName] = useState('');
  const [clothingName, setClothingName] = useState('');
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState('');
  const [personMode, setPersonMode] = useState<CaptureMode>('upload');
  const [clothingMode, setClothingMode] = useState<CaptureMode>('upload');

  // Helper: Convert base64 to File
  const base64ToFile = (base64: string, filename: string): File => {
    const arr = base64.split(',');
    const mime = arr[0].match(/:(.*?);/)?.[1] || 'image/jpeg';
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) {
      u8arr[n] = bstr.charCodeAt(n);
    }
    return new File([u8arr], filename, { type: mime });
  };

  // Helper: Merge multiple camera shots
  const mergeCameraShots = async (shots: string[]): Promise<string> => {
    if (shots.length === 0) return '';
    if (shots.length === 1) return shots[0];

    try {
      const response = await fetch('http://localhost:5001/merge-shots', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ shots }),
      });

      const data = await response.json();
      return data.success ? data.merged_image : shots[0];
    } catch (error) {
      console.warn('Merge failed, using first shot:', error);
      return shots[0];
    }
  };

  // Validate inputs based on mode
  const hasPersonData = personMode === 'upload' ? personImage : personCameraShots.length > 0;
  const hasClothingData = clothingMode === 'upload' ? clothingImage : clothingCameraShots.length > 0;

  const handleTryOn = async () => {
    console.log('🎨 [TryOn] Starting virtual try-on...');
    console.log('   Person mode:', personMode, 'Data:', hasPersonData);
    console.log('   Clothing mode:', clothingMode, 'Data:', hasClothingData);

    if (!hasPersonData || !hasClothingData || !personName || !clothingName) {
      alert('Vyplňte prosím všechna pole a nahrajte obrázky nebo je vyfotografujte');
      return;
    }

    setLoading(true);
    console.log('⏳ [TryOn] Loading started');

    try {
      const formData = new FormData();

      // Handle person image
      if (personMode === 'camera') {
        setLoadingStep('📸 Zpracovávám fotky osoby...');
        console.log('📸 [TryOn] Merging person camera shots...');
        const mergedPerson = await mergeCameraShots(personCameraShots);
        const personFile = base64ToFile(mergedPerson, 'person-camera.jpg');
        formData.append('personImage', personFile);
        console.log('✅ [TryOn] Person image prepared from camera');
      } else {
        setLoadingStep('📤 Připravuji obrázek osoby...');
        formData.append('personImage', personImage!);
        console.log('✅ [TryOn] Person image prepared from upload');
      }

      // Handle clothing image
      if (clothingMode === 'camera') {
        setLoadingStep('📸 Zpracovávám fotky oblečení...');
        console.log('📸 [TryOn] Merging clothing camera shots...');
        const mergedClothing = await mergeCameraShots(clothingCameraShots);
        const clothingFile = base64ToFile(mergedClothing, 'clothing-camera.jpg');
        formData.append('clothingImage', clothingFile);
        console.log('✅ [TryOn] Clothing image prepared from camera');
      } else {
        setLoadingStep('📤 Připravuji obrázek oblečení...');
        formData.append('clothingImage', clothingImage!);
        console.log('✅ [TryOn] Clothing image prepared from upload');
      }

      formData.append('personName', personName);
      formData.append('clothingName', clothingName);

      setLoadingStep('🚀 Posílám na AI server...');
      console.log('🚀 [TryOn] Sending request to API...');
      const response = await fetch('/api/try-on', {
        method: 'POST',
        body: formData,
      });

      setLoadingStep('🎨 AI generuje výsledek...');
      console.log('📥 [TryOn] Response received:', response.status);
      const data = await response.json();
      console.log('📦 [TryOn] Response data:', data);

      if (data.success) {
        setLoadingStep('✅ Hotovo!');
        setResult(data.resultUrl);
      } else {
        alert('Chyba: ' + data.error);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Nastala chyba při zpracování');
    } finally {
      setLoading(false);
      setLoadingStep('');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 dark:text-white mb-2">
            🎨 Virtuální Zkušební Kabina
          </h1>
          <p className="text-gray-600 dark:text-gray-300">
            Vyzkoušejte si oblečení pomocí AI technologie
          </p>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Panel - History */}
          <div className="lg:col-span-1">
            <HistoryPanel onSelect={(item) => {
              setResult(item.resultUrl);
            }} />
          </div>

          {/* Center - Upload and Result */}
          <div className="lg:col-span-2">
            {/* Upload Zones */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              {/* Person Upload/Camera */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-800 dark:text-white">
                    👤 Osoba
                  </h3>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setPersonMode('upload')}
                      className={`px-3 py-1 rounded text-sm transition ${
                        personMode === 'upload'
                          ? 'bg-purple-600 text-white'
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                      }`}
                    >
                      📤 Upload
                    </button>
                    <button
                      onClick={() => setPersonMode('camera')}
                      className={`px-3 py-1 rounded text-sm transition ${
                        personMode === 'camera'
                          ? 'bg-purple-600 text-white'
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                      }`}
                    >
                      📷 Kamera
                    </button>
                  </div>
                </div>

                <input
                  type="text"
                  placeholder="Jméno osoby"
                  value={personName}
                  onChange={(e) => setPersonName(e.target.value)}
                  className="w-full mb-4 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
                />

                {personMode === 'upload' ? (
                  <UploadZone
                    onFileSelect={setPersonImage}
                    accept="image/*,video/*"
                    label="Nahrajte fotku nebo video"
                    type="person"
                  />
                ) : (
                  <CameraCapture
                    onCapture={setPersonCameraShots}
                    label="Vyfotit osobu"
                    multiShot={true}
                  />
                )}
              </div>

              {/* Clothing Upload/Camera */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-800 dark:text-white">
                    👕 Oblečení
                  </h3>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setClothingMode('upload')}
                      className={`px-3 py-1 rounded text-sm transition ${
                        clothingMode === 'upload'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                      }`}
                    >
                      📤 Upload
                    </button>
                    <button
                      onClick={() => setClothingMode('camera')}
                      className={`px-3 py-1 rounded text-sm transition ${
                        clothingMode === 'camera'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                      }`}
                    >
                      📷 Kamera
                    </button>
                  </div>
                </div>

                <input
                  type="text"
                  placeholder="Název oblečení"
                  value={clothingName}
                  onChange={(e) => setClothingName(e.target.value)}
                  className="w-full mb-4 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />

                {clothingMode === 'upload' ? (
                  <UploadZone
                    onFileSelect={setClothingImage}
                    accept="image/*"
                    label="Nahrajte obrázek oblečení"
                    type="clothing"
                  />
                ) : (
                  <CameraCapture
                    onCapture={setClothingCameraShots}
                    label="Vyfotit oblečení"
                    multiShot={true}
                  />
                )}
              </div>
            </div>

            {/* Try On Button */}
            <div className="mb-6">
              <button
                onClick={handleTryOn}
                disabled={loading || !hasPersonData || !hasClothingData || !personName || !clothingName}
                className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-400 disabled:to-gray-500 text-white font-semibold py-4 px-6 rounded-lg shadow-lg transition-all transform hover:scale-105 disabled:scale-100 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <div className="flex flex-col items-center gap-2">
                    <span>⏳ Zpracovávám...</span>
                    {loadingStep && <span className="text-sm opacity-90">{loadingStep}</span>}
                  </div>
                ) : '✨ Vyzkoušet oblečení'}
              </button>
            </div>

            {/* Result Viewer */}
            {result && (
              <ResultViewer
                imageUrl={result}
                loading={loading}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
