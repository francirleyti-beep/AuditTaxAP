import React, { useState, useEffect, useRef } from 'react';
import { Upload, FileText, CheckCircle, AlertTriangle, Play, Download, RefreshCw, X, Moon, Sun, History, BarChart2 } from 'lucide-react';
import { uploadXml, startAudit, getAuditResults, getDownloadUrl, getAudits, AuditSummary } from '../api';
import ResultsTable from './ResultsTable';
import { DashboardCharts } from './DashboardCharts';
import InvoiceHeader from './InvoiceHeader';
import ConsistencyAlert from './ConsistencyAlert';

const AuditInterface: React.FC = () => {
    // ... existing state ...

    const [activeStep, setActiveStep] = useState<'upload' | 'processing' | 'results' | 'history'>('upload');
    const [file, setFile] = useState<File | null>(null);
    const [dragActive, setDragActive] = useState(false);
    const [auditId, setAuditId] = useState<string | null>(null);
    const [progress, setProgress] = useState(0);
    const [statusMessage, setStatusMessage] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [auditResult, setAuditResult] = useState<any>(null);
    const [darkMode, setDarkMode] = useState(localStorage.getItem('theme') === 'dark');
    const [history, setHistory] = useState<AuditSummary[]>([]);

    // WebSocket ref
    const ws = useRef<WebSocket | null>(null);

    // Dark Mode Effect
    useEffect(() => {
        if (darkMode) {
            document.documentElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        }
    }, [darkMode]);

    // WebSocket Connection
    useEffect(() => {
        if (activeStep === 'processing' && auditId) {
            // Close existing connection if any
            if (ws.current) ws.current.close();

            const wsUrl = `ws://localhost:8000/api/ws/audit/${auditId}`;
            const socket = new WebSocket(wsUrl);
            ws.current = socket;

            socket.onopen = () => {
                console.log('Connected to WebSocket');
            };

            socket.onmessage = async (event) => {
                try {
                    const data = JSON.parse(event.data);
                    setProgress(data.progress);
                    setStatusMessage(data.step);

                    if (data.status === 'completed') {
                        const results = await getAuditResults(auditId);
                        setAuditResult({ ...data, result: results });
                        setActiveStep('results');
                        socket.close();
                    } else if (data.status === 'error') {
                        setError(data.error || 'Erro no processamento');
                        setActiveStep('upload'); // Re-enable buttons
                        socket.close();
                    }
                } catch (e) {
                    console.error("Error parsing WS message", e);
                }
            };

            socket.onerror = (err) => {
                console.error("WebSocket error", err);
                // Fallback or retry logic could go here
            };

            return () => {
                socket.close();
            };
        }
    }, [activeStep, auditId]);

    // Fetch History
    const fetchHistory = async () => {
        try {
            const data = await getAudits();
            setHistory(data);
        } catch (e) {
            console.error("Failed to fetch history", e);
        }
    };

    useEffect(() => {
        if (activeStep === 'history') {
            fetchHistory();
        }
    }, [activeStep]);


    // Handlers
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
            setProgress(0);
            setStatusMessage("Iniciando...");

            const uploadResp = await uploadXml(file);
            setAuditId(uploadResp.audit_id);
            await startAudit(uploadResp.audit_id);

        } catch (err: any) {
            setError(err.response?.data?.detail || "Erro ao iniciar auditoria");
            setActiveStep('upload');
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

    const loadAuditFromHistory = async (id: string) => {
        try {
            setAuditId(id);
            const results = await getAuditResults(id);
            setAuditResult({ result: results }); // Mocking full status obj
            setActiveStep('results');
        } catch (e) {
            setError("Erro ao carregar auditoria.");
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors duration-200">
            <div className="max-w-7xl mx-auto p-6 font-sans text-slate-800 dark:text-slate-200">
                <header className="mb-10 flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400">
                            AuditTax AP
                        </h1>
                        <p className="text-slate-500 dark:text-slate-400 mt-1">Sistema de Auditoria Fiscal Automatizada</p>
                    </div>

                    <div className="flex items-center space-x-4">
                        {/* Steps / Tabs */}
                        <div className="flex bg-white dark:bg-slate-800 rounded-full p-1 shadow-sm border border-slate-200 dark:border-slate-700">
                            <button
                                onClick={() => activeStep !== 'processing' && setActiveStep('upload')}
                                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${activeStep === 'upload' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'}`}
                            >
                                <Upload size={16} className="inline mr-2" /> Novo
                            </button>
                            <button
                                onClick={() => activeStep !== 'processing' && setActiveStep('history')}
                                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${activeStep === 'history' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'}`}
                            >
                                <History size={16} className="inline mr-2" /> Histórico
                            </button>
                        </div>

                        {/* Dark Mode Toggle */}
                        <button
                            onClick={() => setDarkMode(!darkMode)}
                            className="p-2 rounded-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                        >
                            {darkMode ? <Sun size={20} /> : <Moon size={20} />}
                        </button>
                    </div>
                </header>

                <main className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl min-h-[500px] flex flex-col relative overflow-hidden border border-slate-100 dark:border-slate-700 transition-colors duration-200">
                    {error && (
                        <div className="absolute top-0 left-0 right-0 bg-red-50 dark:bg-red-900/30 p-4 border-b border-red-100 dark:border-red-900/50 flex items-center justify-between text-red-700 dark:text-red-300 z-10">
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
                                className={`w-full max-w-2xl border-2 border-dashed rounded-3xl p-12 flex flex-col items-center justify-center text-center transition-all duration-200 ${dragActive ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-slate-300 dark:border-slate-600 hover:border-blue-400 hover:bg-slate-50 dark:hover:bg-slate-800/50'}`}
                                onDragEnter={handleDrag}
                                onDragLeave={handleDrag}
                                onDragOver={handleDrag}
                                onDrop={handleDrop}
                            >
                                <div className="w-20 h-20 bg-blue-100 dark:bg-blue-900/50 rounded-full flex items-center justify-center mb-6 text-blue-600 dark:text-blue-400">
                                    <Upload size={32} />
                                </div>
                                <h3 className="text-xl font-semibold mb-2 text-slate-900 dark:text-white">Arraste seu arquivo XML aqui</h3>
                                <p className="text-slate-500 dark:text-slate-400 mb-8">ou clique para selecionar do computador</p>

                                <input
                                    id="file-upload"
                                    type="file"
                                    className="hidden"
                                    accept=".xml,text/xml"
                                    onChange={handleChange}
                                />
                                <label
                                    htmlFor="file-upload"
                                    className="px-8 py-3 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 shadow-sm rounded-xl font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-600 cursor-pointer transition-colors"
                                >
                                    Selecionar Arquivo
                                </label>
                            </div>

                            {file && (
                                <div className="mt-8 w-full max-w-2xl bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4 flex items-center justify-between border border-slate-200 dark:border-slate-600 animate-in slide-in-from-bottom-2">
                                    <div className="flex items-center space-x-4">
                                        <div className="p-2 bg-white dark:bg-slate-600 rounded-lg border border-slate-100 dark:border-slate-500 shadow-sm text-blue-600 dark:text-blue-400">
                                            <FileText size={24} />
                                        </div>
                                        <div>
                                            <p className="font-medium text-slate-900 dark:text-white">{file.name}</p>
                                            <p className="text-sm text-slate-500 dark:text-slate-400">{(file.size / 1024).toFixed(2)} KB</p>
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
                                    <div className="absolute inset-0 border-4 border-slate-100 dark:border-slate-700 rounded-full"></div>
                                    <div
                                        className="absolute inset-0 border-4 border-blue-600 rounded-full border-t-transparent animate-spin"
                                    ></div>
                                    <div className="absolute inset-0 flex items-center justify-center text-2xl font-bold text-slate-700 dark:text-slate-200">
                                        {Math.round(progress)}%
                                    </div>
                                </div>

                                <h3 className="text-xl font-semibold mb-2 text-slate-900 dark:text-white">Processando Auditoria...</h3>
                                <p className="text-slate-500 dark:text-slate-400 mb-8">{statusMessage}</p>

                                <div className="w-full bg-slate-100 dark:bg-slate-700 rounded-full h-2 mb-2 overflow-hidden">
                                    <div
                                        className="bg-blue-600 h-2 rounded-full transition-all duration-500 ease-out"
                                        style={{ width: `${progress}%` }}
                                    ></div>
                                </div>
                                <p className="text-xs text-slate-400">Conectado via WebSocket</p>
                            </div>
                        </div>
                    )}

                    {/* RESULTS VIEW */}
                    {activeStep === 'results' && auditResult && (
                        <div className="flex-1 p-8 animate-in fade-in flex flex-col h-full overflow-y-auto">
                            <div className="flex justify-between items-start mb-6">
                                <div>
                                    <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Resultados da Auditoria</h2>
                                    <p className="text-slate-500 dark:text-slate-400 flex items-center gap-2">
                                        <span className="font-mono bg-slate-100 dark:bg-slate-700 px-2 py-1 rounded text-xs">{auditId}</span>
                                    </p>
                                </div>
                                <div className="flex space-x-3">
                                    <button onClick={handleReset} className="px-4 py-2 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg font-medium flex items-center space-x-2 transition-colors border border-slate-200 dark:border-slate-600">
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

                            {/* Invoice Header */}
                            {auditResult.invoice_header && (
                                <InvoiceHeader header={auditResult.invoice_header} />
                            )}

                            {/* Consistency Alerts */}
                            {auditResult.consistency_errors && (
                                <ConsistencyAlert errors={auditResult.consistency_errors} />
                            )}

                            {/* Dashboard Charts */}
                            {auditResult.result && <DashboardCharts results={auditResult.result} />}

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

                    {/* HISTORY VIEW */}
                    {activeStep === 'history' && (
                        <div className="flex-1 p-8 animate-in fade-in flex flex-col">
                            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">Histórico de Auditorias</h2>

                            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
                                <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                                    <thead className="bg-slate-50 dark:bg-slate-700">
                                        <tr>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-300 uppercase tracking-wider">ID / NFe</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-300 uppercase tracking-wider">Status</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-300 uppercase tracking-wider">Data</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-300 uppercase tracking-wider">Resumo</th>
                                            <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 dark:text-slate-300 uppercase tracking-wider">Ações</th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white dark:bg-slate-800 divide-y divide-slate-200 dark:divide-slate-700">
                                        {history.map((audit) => (
                                            <tr key={audit.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <div className="text-sm font-medium text-slate-900 dark:text-white truncate max-w-xs" title={audit.nfe_key}>
                                                        {audit.nfe_key ? audit.nfe_key : audit.id}
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                                                        ${audit.status === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                                                            audit.status === 'error' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
                                                                'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'}`}>
                                                        {audit.status}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">
                                                    {new Date(audit.created_at).toLocaleDateString()} {new Date(audit.created_at).toLocaleTimeString()}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">
                                                    {audit.summary ? (
                                                        <span>{audit.summary.compliant} OK / {audit.summary.divergent} Div</span>
                                                    ) : '-'}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                    <button
                                                        onClick={() => loadAuditFromHistory(audit.id)}
                                                        className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300 mr-4"
                                                    >
                                                        Visualizar
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
};

export default AuditInterface;
