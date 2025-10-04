import React, { useState, useRef } from 'react';
import { api } from '../api';

interface GeneratePageProps {
  onBack: () => void;
  onSuccess: (summary: { created: number; requested: number; topic: string }) => void;
}

const pillBtn = 'px-6 py-3 rounded-2xl font-bold shadow-md transition-all';

const GeneratePage: React.FC<GeneratePageProps> = ({ onBack, onSuccess }) => {
  const [mode, setMode] = useState<'link' | 'pdf'>('link');
  const [size, setSize] = useState<'small' | 'large'>('small');
  const [url, setUrl] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [topic, setTopic] = useState('');
  const [subTopic, setSubTopic] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const openFilePicker = () => fileInputRef.current?.click();

  const isPdf = (f: File | null) => !!f && (f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf'));

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] || null;
    if (!f) {
      setFile(null);
      return;
    }
    if (!isPdf(f)) {
      setError('Please upload a PDF file');
      setFile(null);
      return;
    }
    setError(null);
    setFile(f);
  };

  const handleDrop: React.DragEventHandler<HTMLDivElement> = (e) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0] || null;
    if (!f) return;
    if (!isPdf(f)) {
      setError('Please upload a PDF file');
      setFile(null);
      return;
    }
    setError(null);
    setFile(f);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      let result;
      if (mode === 'link') {
        if (!url) throw new Error('Please enter a URL');
        result = await api.generateFromLink({ url, size, topic: topic || undefined, sub_topic: subTopic || undefined });
      } else {
        if (!file) throw new Error('Please select a PDF');
        result = await api.generateFromPdf({ file, size, topic: topic || undefined, sub_topic: subTopic || undefined });
      }
      onSuccess({ created: result.created, requested: result.requested, topic: result.topic });
    } catch (err: any) {
      setError(err?.message || 'Generation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button onClick={onBack} className="p-2 text-gray-600 hover:text-gray-900 transition">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="text-2xl font-extrabold text-gray-800">Create Questions</h1>
        <div className="w-6" />
      </div>

      {/* Mode Switch */}
      <div className="bg-white p-2 rounded-2xl border-2 border-gray-200 w-fit mx-auto">
        <button onClick={() => setMode('link')} className={`${pillBtn} ${mode==='link' ? 'bg-[#58CC02] text-white' : 'bg-gray-100 text-gray-700'} mr-2`}>From Link</button>
        <button onClick={() => setMode('pdf')} className={`${pillBtn} ${mode==='pdf' ? 'bg-[#58CC02] text-white' : 'bg-gray-100 text-gray-700'}`}>From PDF</button>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-white p-6 rounded-2xl border-2 border-gray-200 space-y-4">
        {mode === 'link' ? (
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-600">URL</label>
            <input type="url" value={url} onChange={(e)=>setUrl(e.target.value)} placeholder="https://example.com/article" className="w-full p-3 rounded-xl border-2 border-gray-200 focus:border-[#58CC02] outline-none" />
          </div>
        ) : (
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-600">PDF</label>
            {/* Dropzone */}
            <div
              onDragOver={(e)=>e.preventDefault()}
              onDrop={handleDrop}
              className={`rounded-2xl border-2 border-dashed ${file ? 'border-green-300 bg-green-50' : 'border-gray-300 bg-gray-50'} p-6 flex flex-col items-center justify-center text-center cursor-pointer hover:bg-gray-100 transition`}
              onClick={openFilePicker}
              role="button"
              tabIndex={0}
              onKeyDown={(e)=>{ if (e.key === 'Enter' || e.key === ' ') openFilePicker(); }}
            >
              {!file ? (
                <>
                  <div className="text-5xl mb-2">📄</div>
                  <p className="text-gray-700 font-medium">Drag & drop your PDF here</p>
                  <p className="text-gray-500 text-sm">or click to choose a file</p>
                </>
              ) : (
                <div className="w-full flex items-center justify-between gap-4">
                  <div className="text-left">
                    <div className="font-bold text-gray-800">{file.name}</div>
                    <div className="text-xs text-gray-600">{(file.size/1024/1024).toFixed(2)} MB</div>
                  </div>
                  <button
                    type="button"
                    onClick={(e)=>{ e.stopPropagation(); setFile(null); }}
                    className="px-3 py-2 rounded-xl bg-red-50 text-red-600 border-2 border-red-200 hover:bg-red-100 text-sm font-bold"
                  >
                    Remove
                  </button>
                </div>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept="application/pdf"
                onChange={handleFileChange}
                className="hidden"
              />
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-600">Topic (optional)</label>
            <input value={topic} onChange={(e)=>setTopic(e.target.value)} placeholder="e.g., Internet Addiction" className="w-full p-3 rounded-xl border-2 border-gray-200 focus:border-[#58CC02] outline-none" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-600">Sub-topic (optional)</label>
            <input value={subTopic} onChange={(e)=>setSubTopic(e.target.value)} placeholder="e.g., Social Media" className="w-full p-3 rounded-xl border-2 border-gray-200 focus:border-[#58CC02] outline-none" />
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-600">Size</label>
          <div className="flex gap-3">
            <button type="button" onClick={()=>setSize('small')} className={`${pillBtn} ${size==='small' ? 'bg-[#58CC02] text-white' : 'bg-gray-100 text-gray-700'}`}>Small (25)</button>
            <button type="button" onClick={()=>setSize('large')} className={`${pillBtn} ${size==='large' ? 'bg-[#58CC02] text-white' : 'bg-gray-100 text-gray-700'}`}>Large (50)</button>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border-2 border-red-200 rounded-xl text-red-700 text-sm">{error}</div>
        )}

        <div className="flex justify-end">
          <button type="submit" disabled={loading} className={`${pillBtn} bg-[#58CC02] text-white hover:bg-[#46A302] ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}>
            {loading ? 'Generating…' : 'Generate'}
          </button>
        </div>
      </form>

      {/* Tips */}
      <div className="bg-white p-4 rounded-2xl border-2 border-gray-200 text-gray-600 text-sm">
        Tip: For paywalled or complex pages, use the PDF option for best results.
      </div>
    </div>
  );
};

export default GeneratePage;
