import React, { useState, useEffect, useRef } from 'react';
import { Upload, FileText, CheckCircle, AlertTriangle, Play, Download, RefreshCw, X, Moon, Sun, History, BarChart2, Trash2, RotateCcw, Eye } from 'lucide-react';
import { uploadXml, startAudit, getAuditResults, getDownloadUrl, getAudits, AuditSummary, deleteAudit, retryAudit } from '../api';
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

            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = window.location.hostname === 'localhost'
                ? `ws://localhost:8000/api/ws/audit/${auditId}`
                : `${protocol}//${window.location.host}/api/ws/audit/${auditId}`;
            
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
            setAuditResult({ result: results, invoice_header: results.invoice_header, consistency_errors: results.consistency_errors });
            setActiveStep('results');
        } catch (e) {
            setError("Erro ao carregar auditoria.");
        }
    };

    const handleDelete = async (id: string) => {
        if (!window.confirm("Deseja realmente excluir esta auditoria permanentemente?")) return;
        try {
            await deleteAudit(id);
            fetchHistory();
        } catch (e) {
            alert("Erro ao excluir auditoria.");
        }
    };

    const handleRetry = async (id: string) => {
        try {
            await retryAudit(id);
            setAuditId(id);
            setActiveStep('processing');
            setProgress(0);
            setStatusMessage("Reiniciando...");
        } catch (e: any) {
            alert(e.response?.data?.detail || "Erro ao reiniciar auditoria.");
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors duration-200">
            <div className="max-w-7xl mx-auto p-4 md:p-6 font-sans text-slate-800 dark:text-slate-200">
                <header className="mb-6 md:mb-10 flex flex-col sm:flex-row justify-between items-center gap-4">
                    <div className="text-center sm:text-left">
                        <h1 className="text-2xl md:text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400">
                            AuditTax AP
                        </h1>
                        <p className="text-xs md:text-sm text-slate-500 dark:text-slate-400 mt-1">Sistema de Auditoria Fiscal Automatizada</p>
                    </div>

                    <div className="flex items-center space-x-2 md:space-x-4 w-full sm:w-auto justify-center">
                        {/* Steps / Tabs */}
                        <div className="flex bg-white dark:bg-slate-800 rounded-full p-1 shadow-sm border border-slate-200 dark:border-slate-700 flex-1 sm:flex-none justify-center">
                            <button
                                onClick={() => activeStep !== 'processing' && setActiveStep('upload')}
                                className={`px-3 md:px-4 py-1.5 md:py-2 rounded-full text-xs md:text-sm font-medium transition-colors ${activeStep === 'upload' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'}`}
                            >
                                <Upload size={14} className="inline mr-1 md:mr-2" /> Novo
                            </button>
                            <button
                                onClick={() => activeStep !== 'processing' && setActiveStep('history')}
                                className={`px-3 md:px-4 py-1.5 md:py-2 rounded-full text-xs md:text-sm font-medium transition-colors ${activeStep === 'history' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'}`}
                            >
                                <History size={14} className="inline mr-1 md:mr-2" /> Histórico
                            </button>
                        </div>

                        {/* Dark Mode Toggle */}
                        <button
                            onClick={() => setDarkMode(!darkMode)}
                            className="p-2 rounded-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                        >
                            {darkMode ? <Sun size={18} /> : <Moon size={18} />}
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
                                <div className="mt-8 w-full max-w-2xl bg-slate-50 dark:bg-slate-700/50 rounded-2xl p-4 md:p-6 flex flex-col sm:flex-row items-center justify-between gap-4 border border-slate-200 dark:border-slate-600 animate-in slide-in-from-bottom-4">
                                    <div className="flex items-center space-x-4 w-full sm:w-auto">
                                        <div className="p-3 bg-white dark:bg-slate-600 rounded-xl border border-slate-100 dark:border-slate-500 shadow-sm text-blue-600 dark:text-blue-400 shrink-0">
                                            <FileText size={28} />
                                        </div>
                                        <div className="min-w-0 flex-1">
                                            <p className="font-semibold text-slate-900 dark:text-white truncate" title={file.name}>{file.name}</p>
                                            <p className="text-xs text-slate-500 dark:text-slate-400">{(file.size / 1024).toFixed(2)} KB</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={handleUploadAndStart}
                                        className="w-full sm:w-auto px-8 py-3 bg-blue-600 hover:bg-blue-700 active:scale-95 text-white rounded-xl font-bold transition-all flex items-center justify-center space-x-2 shadow-lg shadow-blue-600/30"
                                    >
                                        <Play size={20} fill="currentColor" />
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
                        <div className="flex-1 p-4 md:p-8 animate-in fade-in flex flex-col h-full overflow-y-auto">
                            <div className="flex flex-col sm:flex-row justify-between items-start gap-4 mb-6">
                                <div className="w-full sm:w-auto">
                                    <h2 className="text-xl md:text-2xl font-bold text-slate-900 dark:text-white mb-2">Resultados da Auditoria</h2>
                                    <p className="text-slate-500 dark:text-slate-400 flex items-center gap-2">
                                        <span className="font-mono bg-slate-100 dark:bg-slate-700 px-2 py-1 rounded text-[10px] md:text-xs break-all">{auditId}</span>
                                    </p>
                                </div>
                                <div className="flex flex-wrap gap-2 w-full sm:w-auto">
                                    <button onClick={handleReset} className="flex-1 sm:flex-none px-3 py-2 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg text-sm font-medium flex items-center justify-center space-x-2 transition-colors border border-slate-200 dark:border-slate-600">
                                        <RefreshCw size={16} />
                                        <span>Novo</span>
                                    </button>
                                    {auditId && (
                                        <a
                                            href={getDownloadUrl(auditId)}
                                            download
                                            className="flex-1 sm:flex-none px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium shadow-lg shadow-green-600/20 flex items-center justify-center space-x-2 transition-colors"
                                        >
                                            <Download size={16} />
                                            <span>Exportar</span>
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
                                {auditResult.result ? (
                                    <ResultsTable 
                                        results={auditResult.result} 
                                        onUpdate={() => loadAuditFromHistory(auditId!)}
                                    />
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
                                <div className="overflow-x-auto">
                                    <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                                        <thead className="bg-slate-50 dark:bg-slate-700">
                                            <tr>
                                                <th className="px-4 md:px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-300 uppercase tracking-wider">ID / NFe</th>
                                                <th className="px-4 md:px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-300 uppercase tracking-wider">Status</th>
                                                <th className="px-4 md:px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-300 uppercase tracking-wider hidden sm:table-cell">Data</th>
                                                <th className="px-4 md:px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-300 uppercase tracking-wider hidden md:table-cell">Resumo</th>
                                                <th className="px-4 md:px-6 py-3 text-right text-xs font-medium text-slate-500 dark:text-slate-300 uppercase tracking-wider">Ações</th>
                                            </tr>
                                        </thead>
                                        <tbody className="bg-white dark:bg-slate-800 divide-y divide-slate-200 dark:divide-slate-700">
                                            {history.map((audit) => (
                                                <tr key={audit.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                                                    <td className="px-4 md:px-6 py-4 whitespace-nowrap">
                                                        <div className="text-sm font-medium text-slate-900 dark:text-white truncate max-w-[120px] md:max-w-xs" title={audit.nfe_key}>
                                                            {audit.nfe_key ? audit.nfe_key : audit.id}
                                                        </div>
                                                    </td>
                                                    <td className="px-4 md:px-6 py-4 whitespace-nowrap">
                                                        <div className="flex flex-col gap-1">
                                                            <span className={`px-2 inline-flex text-[10px] md:text-xs leading-5 font-semibold rounded-full 
                                                                ${audit.status === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                                                                    audit.status === 'error' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
                                                                        'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'}`}>
                                                                {audit.status}
                                                            </span>
                                                            {audit.is_fully_reviewed && (
                                                                <span className="px-2 inline-flex text-[9px] md:text-[10px] leading-4 font-bold bg-blue-100 text-blue-700 rounded-full w-fit">
                                                                    CONFERIDA
                                                                </span>
                                                            )}
                                                        </div>
                                                    </td>
                                                    <td className="px-4 md:px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400 hidden sm:table-cell">
                                                        {new Date(audit.created_at).toLocaleDateString()}
                                                    </td>
                                                    <td className="px-4 md:px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400 hidden md:table-cell">
                                                        {audit.summary ? (
                                                            <span>{audit.summary.compliant} OK / {audit.summary.divergent} Div</span>
                                                        ) : '-'}
                                                    </td>
                                                    <td className="px-4 md:px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                        <div className="flex justify-end gap-1 md:gap-2">
                                                            <button
                                                                onClick={() => loadAuditFromHistory(audit.id)}
                                                                className="p-1.5 md:p-2 text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-900/30 rounded-lg transition-colors"
                                                                title="Visualizar"
                                                            >
                                                                <Eye className="w-4 h-4 md:w-5 md:h-5" />
                                                            </button>
                                                            <button
                                                                onClick={() => handleRetry(audit.id)}
                                                                className="p-1.5 md:p-2 text-amber-600 hover:bg-amber-50 dark:text-amber-400 dark:hover:bg-amber-900/30 rounded-lg transition-colors"
                                                                title="Re-auditar"
                                                            >
                                                                <RotateCcw className="w-4 h-4 md:w-5 md:h-5" />
                                                            </button>
                                                            <button
                                                                onClick={() => handleDelete(audit.id)}
                                                                className="p-1.5 md:p-2 text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/30 rounded-lg transition-colors"
                                                                title="Excluir"
                                                            >
                                                                <Trash2 className="w-4 h-4 md:w-5 md:h-5" />
                                                            </button>
                                                        </div>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
};

export default AuditInterface;
