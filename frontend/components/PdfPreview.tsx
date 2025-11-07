'use client';

import { useState, useEffect } from 'react';

interface PdfPreviewProps {
  pdfFilename: string;
  onClose?: () => void;
}

export default function PdfPreview({ pdfFilename, onClose }: PdfPreviewProps) {
  const [status, setStatus] = useState<'checking' | 'converting' | 'ready' | 'error'>('checking');
  const [pdfUrl, setPdfUrl] = useState('');

  useEffect(() => {
    checkPdfStatus();
  }, [pdfFilename]);

  const checkPdfStatus = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/pdf/status/${pdfFilename}`);
      const data = await res.json();

      if (res.status === 200 && data.ready) {
        // PDF ready!
        setStatus('ready');
        setPdfUrl(`http://localhost:8000/api/pdf/view/${pdfFilename}`);
      } else if (res.status === 202) {
        // Still converting, check again in 1.5s
        setStatus('converting');
        setTimeout(checkPdfStatus, 1500);
      } else {
        setStatus('error');
      }
    } catch (err) {
      console.error('PDF status check error:', err);
      setStatus('error');
    }
  };

  const handleDownload = async () => {
    const res = await fetch(`http://localhost:8000/api/download/pdf/${pdfFilename}`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = pdfFilename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleOpenTab = () => {
    window.open(pdfUrl, '_blank');
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-900 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Resume Preview</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {status === 'checking' && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600 dark:text-gray-300">Checking PDF status...</p>
              </div>
            </div>
          )}

          {status === 'converting' && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600 dark:text-gray-300">Converting to PDF...</p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">This usually takes 2-5 seconds</p>
              </div>
            </div>
          )}

          {status === 'ready' && (
            <iframe
              src={pdfUrl}
              className="w-full h-full"
              title="Resume PDF Preview"
            />
          )}

          {status === 'error' && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-red-600 dark:text-red-400">
                <p className="text-xl mb-2">⚠️</p>
                <p>Failed to load PDF preview</p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        {status === 'ready' && (
          <div className="flex items-center justify-end gap-3 p-4 border-t border-slate-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-800">
            <button
              onClick={handleDownload}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
            >
              📥 Download PDF
            </button>
            <button
              onClick={handleOpenTab}
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition"
            >
              🔗 Open in New Tab
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
