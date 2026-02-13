import React, { useState, useEffect } from 'react';
import { Upload, FileText, CheckCircle, AlertTriangle, Play, Download, RefreshCw, X } from 'lucide-react';
import { uploadXml, startAudit, getAuditStatus, getDownloadUrl, getAuditResults } from '../api';
import ResultsTable from './ResultsTable';

const AuditInterface: React.FC = () => {
    const [activeStep, setActiveStep] = useState<'upload' | 'processing' | 'results'>('upload');
    const [file, setFile] = useState<File | null>(null);
    const [dragActive, setDragActive] = useState(false);
    const [auditId, setAuditId] = useState<string | null>(null);
    const [progress, setProgress] = useState(0);
    const [statusMessage, setStatusMessage] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [auditResult, setAuditResult] = useState<any>(null); // Replace 'any' with proper type if available

    // Polling for progress
    useEffect(() => {
        let interval: NodeJS.Timeout;

        if (activeStep === 'processing' && auditId) {
            interval = setInterval(async () => {
                try {
                    const status = await getAuditStatus(auditId);
                    setProgress(status.progress);
                    setStatusMessage(status.step);

                    if (status.status === 'completed') {
                        // Fetch detailed results
                        try {
                            const results = await getAuditResults(auditId);
                            // Combine status info with detailed results
                            setAuditResult({ ...status, result: results });
                        } catch (e) {
                            console.error("Error fetching results", e);
                            setAuditResult(status);
                        }
                        setActiveStep('results');
                        clearInterval(interval);
                    } else if (status.status === 'error') {
                        setError(status.error || 'Erro desconhecido');
                        clearInterval(interval);
                    }
                } catch (err) {
                    console.error("Polling error", err);
                    // Don't stop polling immediately on intermittent network error, but maybe limit retries
                }
            }, 1000);
        }

        return () => clearInterval(interval);
    }, [activeStep, auditId]);

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            validateAndSetFile(e.dataTransfer.files[0]);
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        e.preventDefault();
        if (e.target.files && e.target.files[0]) {
            validateAndSetFile(e.target.files[0]);
        }
    };

    const validateAndSetFile = (file: File) => {
        if (file.type === "text/xml" || file.name.endsWith(".xml")) {
            setFile(file);
            setError(null);
        } else {
            setError("Por favor, envie apenas arquivos XML.");
        }
    };

    const handleUploadAndStart = async () => {
        if (!file) return;

        try {
            setActiveStep('processing');
            setProgress(5);
            setStatusMessage("Enviando arquivo...");

            const uploadResp = await uploadXml(file);
            setAuditId(uploadResp.audit_id);

            setStatusMessage("Iniciando auditoria...");
            await startAudit(uploadResp.audit_id);

        } catch (err: any) {
            setError(err.response?.data?.detail || "Erro ao iniciar auditoria");
            setActiveStep('upload'); // Go back to upload on initial failure
        }
    };

    const handleReset = () => {
        setFile(null);
        setAuditId(null);
        setProgress(0);
        setStatusMessage('');
        setAuditResult(null);
        setError(null);
        setActiveStep('upload');
    };

    return (
        <div className="max-w-6xl mx-auto p-6 font-sans text-slate-800">
            <header className="mb-10 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
                        AuditTax AP
                    </h1>
                    <p className="text-slate-500 mt-1">Sistema de Auditoria Fiscal Automatizada</p>
                </div>
                <div className="flex space-x-2">
                    {['Upload', 'Processamento', 'Resultados'].map((step, idx) => {
                        const stepKey = ['upload', 'processing', 'results'][idx];
                        const isActive = activeStep === stepKey;
                        const isCompleted = ['upload', 'processing', 'results'].indexOf(activeStep) > idx;

                        return (
                            <div key={step} className={`flex items-center space-x-2 px-4 py-2 rounded-full ${isActive ? 'bg-blue-50 text-blue-700 font-medium' : isCompleted ? 'text-green-600' : 'text-slate-400'}`}>
                                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${isActive ? 'bg-blue-600 text-white' : isCompleted ? 'bg-green-500 text-white' : 'bg-slate-200'}`}>
                                    {isCompleted ? <CheckCircle size={14} /> : idx + 1}
                                </div>
                                <span>{step}</span>
                            </div>
                        );
                    })}
                </div>
            </header>

            <main className="bg-white rounded-2xl shadow-xl min-h-[500px] flex flex-col relative overflow-hidden">
                {error && (
                    <div className="absolute top-0 left-0 right-0 bg-red-50 p-4 border-b border-red-100 flex items-center justify-between text-red-700 z-10">
                        <div className="flex items-center space-x-2">
                            <AlertTriangle size={20} />
                            <span>{error}</span>
                        </div>
                        <button onClick={() => setError(null)}><X size={18} /></button>
                    </div>
                )}

                {/* UPLOAD VIEW */}
                {activeStep === 'upload' && (
                    <div className="flex-1 flex flex-col items-center justify-center p-12 animate-in fade-in duration-500">
                        <div
                            className={`w-full max-w-2xl border-2 border-dashed rounded-3xl p-12 flex flex-col items-center justify-center text-center transition-all duration-200 ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-slate-300 hover:border-blue-400 hover:bg-slate-50'}`}
                            onDragEnter={handleDrag}
                            onDragLeave={handleDrag}
                            onDragOver={handleDrag}
                            onDrop={handleDrop}
                        >
                            <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mb-6 text-blue-600">
                                <Upload size={32} />
                            </div>
                            <h3 className="text-xl font-semibold mb-2">Arraste seu arquivo XML aqui</h3>
                            <p className="text-slate-500 mb-8">ou clique para selecionar do computador</p>

                            <input
                                id="file-upload"
                                type="file"
                                className="hidden"
                                accept=".xml,text/xml"
                                onChange={handleChange}
                            />
                            <label
                                htmlFor="file-upload"
                                className="px-8 py-3 bg-white border border-slate-200 shadow-sm rounded-xl font-medium text-slate-700 hover:bg-slate-50 cursor-pointer transition-colors"
                            >
                                Selecionar Arquivo
                            </label>
                        </div>

                        {file && (
                            <div className="mt-8 w-full max-w-2xl bg-slate-50 rounded-xl p-4 flex items-center justify-between border border-slate-200 animate-in slide-in-from-bottom-2">
                                <div className="flex items-center space-x-4">
                                    <div className="p-2 bg-white rounded-lg border border-slate-100 shadow-sm text-blue-600">
                                        <FileText size={24} />
                                    </div>
                                    <div>
                                        <p className="font-medium text-slate-900">{file.name}</p>
                                        <p className="text-sm text-slate-500">{(file.size / 1024).toFixed(2)} KB</p>
                                    </div>
                                </div>
                                <button
                                    onClick={handleUploadAndStart}
                                    className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors flex items-center space-x-2 shadow-lg shadow-blue-600/20"
                                >
                                    <Play size={18} />
                                    <span>Iniciar Auditoria</span>
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {/* PROCESSING VIEW */}
                {activeStep === 'processing' && (
                    <div className="flex-1 flex flex-col items-center justify-center p-12">
                        <div className="w-full max-w-md text-center">
                            <div className="relative w-32 h-32 mx-auto mb-8">
                                <div className="absolute inset-0 border-4 border-slate-100 rounded-full"></div>
                                <div
                                    className="absolute inset-0 border-4 border-blue-600 rounded-full border-t-transparent animate-spin"
                                // style={{ transform: `rotate(${progress * 3.6}deg)` }} // Optional: connect rotation to progress if implementing circular progress
                                ></div>
                                <div className="absolute inset-0 flex items-center justify-center text-2xl font-bold text-slate-700">
                                    {Math.round(progress)}%
                                </div>
                            </div>

                            <h3 className="text-xl font-semibold mb-2 text-slate-900">Processando Auditoria...</h3>
                            <p className="text-slate-500 mb-8">{statusMessage}</p>

                            <div className="w-full bg-slate-100 rounded-full h-2 mb-2 overflow-hidden">
                                <div
                                    className="bg-blue-600 h-2 rounded-full transition-all duration-500 ease-out"
                                    style={{ width: `${progress}%` }}
                                ></div>
                            </div>
                            <p className="text-xs text-slate-400">Isso pode levar alguns minutos dependendo do tamanho do XML</p>
                        </div>
                    </div>
                )}

                {/* RESULTS VIEW */}
                {activeStep === 'results' && auditResult && (
                    <div className="flex-1 p-8 animate-in fade-in flex flex-col h-full">
                        <div className="flex justify-between items-start mb-6">
                            <div>
                                <h2 className="text-2xl font-bold text-slate-900 mb-2">Resultados da Auditoria</h2>
                                <p className="text-slate-500 flex items-center gap-2">
                                    <span className="font-mono bg-slate-100 px-2 py-1 rounded text-xs">{auditId}</span>
                                    {auditResult.result?.summary && (
                                        <span className="text-sm">
                                            • {auditResult.result.summary.total} itens processados
                                        </span>
                                    )}
                                </p>
                            </div>
                            <div className="flex space-x-3">
                                <button onClick={handleReset} className="px-4 py-2 text-slate-600 hover:bg-slate-50 rounded-lg font-medium flex items-center space-x-2 transition-colors border border-slate-200">
                                    <RefreshCw size={18} />
                                    <span>Nova Auditoria</span>
                                </button>
                                {auditId && (
                                    <a
                                        href={getDownloadUrl(auditId)}
                                        download
                                        className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium shadow-lg shadow-green-600/20 flex items-center space-x-2 transition-colors"
                                    >
                                        <Download size={18} />
                                        <span>Exportar CSV</span>
                                    </a>
                                )}
                            </div>
                        </div>

                        {/* Metrics Cards */}
                        {auditResult.result?.summary && (
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-slate-500 mb-1">Total de Itens</p>
                                        <p className="text-2xl font-bold text-slate-800">{auditResult.result.summary.total}</p>
                                    </div>
                                    <div className="bg-blue-50 p-2 rounded-lg text-blue-600">
                                        <FileText size={24} />
                                    </div>
                                </div>
                                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-slate-500 mb-1">Conformes</p>
                                        <p className="text-2xl font-bold text-green-600">{auditResult.result.summary.compliant}</p>
                                    </div>
                                    <div className="bg-green-50 p-2 rounded-lg text-green-600">
                                        <CheckCircle size={24} />
                                    </div>
                                </div>
                                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-slate-500 mb-1">Divergentes</p>
                                        <p className="text-2xl font-bold text-orange-600">{auditResult.result.summary.divergent}</p>
                                    </div>
                                    <div className="bg-orange-50 p-2 rounded-lg text-orange-600">
                                        <AlertTriangle size={24} />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Interactive Table */}
                        <div className="flex-1 min-h-0">
                            {auditResult.result?.items ? (
                                <ResultsTable items={auditResult.result.items} />
                            ) : (
                                <div className="text-center py-12 text-slate-400">
                                    Carregando detalhes...
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
};

export default AuditInterface;
