'use client';

import { useEffect, useState } from 'react';

interface TryOnHistory {
  id: string;
  personName: string;
  clothingName: string;
  resultUrl: string;
  createdAt: string;
}

interface HistoryPanelProps {
  onSelect: (item: TryOnHistory) => void;
}

export default function HistoryPanel({ onSelect }: HistoryPanelProps) {
  const [history, setHistory] = useState<TryOnHistory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await fetch('/api/history');
      const data = await response.json();
      if (data.success) {
        setHistory(data.history);
      }
    } catch (error) {
      console.error('Error fetching history:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 h-full">
      <h3 className="text-xl font-bold mb-4 text-gray-800 dark:text-white">
        📚 Historie
      </h3>

      {loading ? (
        <div className="text-center text-gray-600 dark:text-gray-400">
          <div className="animate-spin text-2xl mb-2">⏳</div>
          <p className="text-sm">Načítám...</p>
        </div>
      ) : history.length === 0 ? (
        <div className="text-center text-gray-500 dark:text-gray-400 py-8">
          <div className="text-4xl mb-2">📭</div>
          <p className="text-sm">Zatím žádná historie</p>
        </div>
      ) : (
        <div className="space-y-3 max-h-[calc(100vh-200px)] overflow-y-auto">
          {history.map((item) => (
            <div
              key={item.id}
              onClick={() => onSelect(item)}
              className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <div className="flex items-center gap-3">
                <img
                  src={item.resultUrl}
                  alt={`${item.personName} - ${item.clothingName}`}
                  className="w-16 h-16 object-cover rounded"
                />
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-gray-800 dark:text-white truncate">
                    {item.personName}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                    {item.clothingName}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500">
                    {new Date(item.createdAt).toLocaleDateString('cs-CZ')}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <button
        onClick={fetchHistory}
        className="mt-4 w-full px-4 py-2 bg-gray-200 dark:bg-gray-700 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors text-gray-800 dark:text-white text-sm"
      >
        🔄 Obnovit
      </button>
    </div>
  );
}
