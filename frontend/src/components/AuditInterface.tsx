import React, { useState, useEffect, useRef } from 'react';
import { Upload, FileText, CheckCircle, AlertTriangle, Play, Download, RefreshCw, X, Moon, Sun, History, BarChart2, Trash2, RotateCcw, Eye, Search, ChevronUp } from 'lucide-react';
import { uploadXml, startAudit, getAuditResults, getDownloadUrl, getAudits, AuditSummary, deleteAudit, retryAudit } from '../api';
import ResultsTable from './ResultsTable';
import { DashboardCharts } from './DashboardCharts';
import InvoiceHeader from './InvoiceHeader';
import ConsistencyAlert from './ConsistencyAlert';

const AuditInterface: React.FC = () => {
    const [activeStep, setActiveStep] = useState<'upload' | 'processing' | 'results' | 'history'>('upload');
    const [showScrollTop, setShowScrollTop] = useState(false);
    const [file, setFile] = useState<File | null>(null);
    const [dragActive, setDragActive] = useState(false);
    const [auditId, setAuditId] = useState<string | null>(null);
    const [progress, setProgress] = useState(0);
    const [statusMessage, setStatusMessage] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [auditResult, setAuditResult] = useState<any>(null);
    const [darkMode, setDarkMode] = useState(localStorage.getItem('theme') === 'dark');
    const [history, setHistory] = useState<AuditSummary[]>([]);

    const ws = useRef<WebSocket | null>(null);

    // Scroll listener for "Back to Top" button
    useEffect(() => {
        const handleScroll = () => {
            setShowScrollTop(window.scrollY > 400);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const scrollToTop = () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    useEffect(() => {
        if (darkMode) {
            document.documentElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        }
    }, [darkMode]);

    useEffect(() => {
        if (activeStep === 'processing' && auditId) {
            if (ws.current) ws.current.close();
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = window.location.hostname === 'localhost'
                ? `ws://localhost:8000/api/ws/audit/${auditId}`
                : `${protocol}//${window.location.host}/api/ws/audit/${auditId}`;
            
            const socket = new WebSocket(wsUrl);
            ws.current = socket;

            socket.onmessage = async (event) => {
                try {
                    const data = JSON.parse(event.data);
                    setProgress(data.progress);
                    setStatusMessage(data.step);

                    if (data.status === 'completed') {
                        const results = await getAuditResults(auditId);
                        const finalHeader = results.invoice_header || (data.result && data.result.invoice_header);
                        const finalConsistency = results.consistency_errors || (data.result && data.result.consistency_errors);
                        setAuditResult({ ...data, result: results, invoice_header: finalHeader, consistency_errors: finalConsistency });
                        setActiveStep('results');
                        socket.close();
                    } else if (data.status === 'error') {
                        setError(data.error || 'Erro no processamento');
                        setActiveStep('upload');
                        socket.close();
                    }
                } catch (e) {
                    console.error("Error parsing WS message", e);
                }
            };
            return () => socket.close();
        }
    }, [activeStep, auditId]);

    const fetchHistory = async () => {
        try {
            const data = await getAudits();
            setHistory(data);
        } catch (e) { console.error(e); }
    };

    useEffect(() => {
        if (activeStep === 'history') fetchHistory();
    }, [activeStep]);

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

    const loadAuditFromHistory = async (id: string) => {
        try {
            setAuditId(id);
            const results = await getAuditResults(id);
            setAuditResult({ result: results, invoice_header: results.invoice_header, consistency_errors: results.consistency_errors });
            setActiveStep('results');
        } catch (e) { setError("Erro ao carregar auditoria."); }
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-950 transition-colors duration-500 overflow-x-hidden">
            <div className="max-w-7xl mx-auto p-4 md:p-8">
                <header className="mb-8 md:mb-12 flex flex-col sm:flex-row justify-between items-center gap-6">
                    <div className="text-center sm:text-left">
                        <div className="flex items-center justify-center sm:justify-start gap-3 mb-1">
                            <div className="p-2 bg-indigo-600 rounded-xl shadow-lg shadow-indigo-600/20">
                                <BarChart2 size={24} className="text-white" />
                            </div>
                            <h1 className="text-2xl md:text-3xl font-black text-slate-900 dark:text-white uppercase tracking-tighter">
                                AuditTax<span className="text-indigo-600 dark:text-indigo-400">AP</span>
                            </h1>
                        </div>
                        <p className="text-[10px] md:text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest ml-1">Sistema Profissional de Auditoria Fiscal</p>
                    </div>

                    <div className="flex items-center gap-3 w-full sm:w-auto">
                        <nav className="flex bg-white dark:bg-slate-900 rounded-2xl p-1.5 shadow-sm border border-slate-200 dark:border-slate-800 flex-1 sm:flex-none">
                            <button
                                onClick={() => activeStep !== 'processing' && setActiveStep('upload')}
                                className={`px-5 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider transition-all flex items-center gap-2 ${activeStep === 'upload' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'}`}
                            >
                                <Upload size={14} /> Novo
                            </button>
                            <button
                                onClick={() => activeStep !== 'processing' && setActiveStep('history')}
                                className={`px-5 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider transition-all flex items-center gap-2 ${activeStep === 'history' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'}`}
                            >
                                <History size={14} /> Histórico
                            </button>
                        </nav>

                        <button
                            onClick={() => setDarkMode(!darkMode)}
                            className="p-3 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all shadow-sm"
                        >
                            {darkMode ? <Sun size={20} /> : <Moon size={20} />}
                        </button>
                    </div>
                </header>

                <main className="relative">
                    {error && (
                        <div className="mb-6 bg-red-50 dark:bg-red-950/30 p-4 rounded-2xl border border-red-100 dark:border-red-900/50 flex items-center justify-between text-red-700 dark:text-red-300 animate-in slide-in-from-top-4">
                            <div className="flex items-center space-x-3">
                                <AlertTriangle size={20} className="shrink-0" />
                                <span className="text-sm font-bold">{error}</span>
                            </div>
                            <button onClick={() => setError(null)} className="p-1 hover:bg-red-100 dark:hover:bg-red-900 rounded-lg"><X size={18} /></button>
                        </div>
                    )}

                    {/* UPLOAD VIEW */}
                    {activeStep === 'upload' && (
                        <div className="flex flex-col items-center justify-center p-4 md:p-20 bg-white dark:bg-slate-900 rounded-[2.5rem] border border-slate-200 dark:border-slate-800 shadow-xl transition-all duration-500">
                            <div
                                className={`w-full max-w-2xl border-2 border-dashed rounded-[2rem] p-12 md:p-20 flex flex-col items-center justify-center text-center transition-all duration-300 ${dragActive ? 'border-indigo-500 bg-indigo-50/50 dark:bg-indigo-900/10 scale-105 shadow-2xl shadow-indigo-600/10' : 'border-slate-200 dark:border-slate-800 hover:border-indigo-400 dark:hover:border-indigo-600'}`}
                                onDragEnter={(e) => { e.preventDefault(); setDragActive(true); }}
                                onDragLeave={() => setDragActive(false)}
                                onDragOver={(e) => e.preventDefault()}
                                onDrop={(e) => { e.preventDefault(); setDragActive(false); if(e.dataTransfer.files[0]) validateAndSetFile(e.dataTransfer.files[0]); }}
                            >
                                <div className="w-24 h-24 bg-indigo-100 dark:bg-indigo-950/50 rounded-3xl flex items-center justify-center mb-8 text-indigo-600 dark:text-indigo-400 shadow-inner">
                                    <Upload size={40} />
                                </div>
                                <h3 className="text-2xl font-black mb-3 text-slate-900 dark:text-white uppercase tracking-tight">Deposite seu XML</h3>
                                <p className="text-slate-500 dark:text-slate-400 mb-10 text-sm font-medium">Arraste o arquivo aqui ou clique para buscar</p>

                                <input id="file-upload" type="file" className="hidden" accept=".xml" onChange={(e) => e.target.files?.[0] && validateAndSetFile(e.target.files[0])} />
                                <label htmlFor="file-upload" className="px-10 py-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-lg rounded-2xl font-black uppercase text-xs tracking-widest text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer transition-all active:scale-95">
                                    Explorar Arquivos
                                </label>
                            </div>

                            {file && (
                                <div className="mt-12 w-full max-w-2xl bg-indigo-600 dark:bg-indigo-600 rounded-3xl p-6 md:p-8 flex flex-col sm:flex-row items-center justify-between gap-6 shadow-2xl shadow-indigo-600/30 animate-in zoom-in-95 duration-300">
                                    <div className="flex items-center space-x-5 min-w-0">
                                        <div className="p-4 bg-white/10 rounded-2xl border border-white/20 text-white shrink-0 backdrop-blur-sm">
                                            <FileText size={32} />
                                        </div>
                                        <div className="min-w-0 text-white">
                                            <p className="font-black uppercase tracking-tight truncate text-lg" title={file.name}>{file.name}</p>
                                            <p className="text-xs font-bold opacity-70 tracking-widest uppercase">{(file.size / 1024).toFixed(1)} KB • XML Fiscal</p>
                                        </div>
                                    </div>
                                    <button onClick={handleUploadAndStart} className="w-full sm:w-auto px-10 py-4 bg-white text-indigo-600 rounded-2xl font-black uppercase text-xs tracking-[0.2em] transition-all hover:bg-slate-50 active:scale-95 shadow-xl">
                                        Auditar Agora
                                    </button>
                                </div>
                            )}
                        </div>
                    )}

                    {/* PROCESSING VIEW */}
                    {activeStep === 'processing' && (
                        <div className="bg-white dark:bg-slate-900 rounded-[2.5rem] border border-slate-200 dark:border-slate-800 p-20 flex flex-col items-center justify-center min-h-[500px]">
                            <div className="w-full max-w-md text-center">
                                <div className="relative w-40 h-40 mx-auto mb-10">
                                    <div className="absolute inset-0 border-[6px] border-slate-100 dark:border-slate-800 rounded-full"></div>
                                    <div className="absolute inset-0 border-[6px] border-indigo-600 rounded-full border-t-transparent animate-spin"></div>
                                    <div className="absolute inset-0 flex items-center justify-center text-3xl font-black text-slate-900 dark:text-white tracking-tighter">
                                        {Math.round(progress)}%
                                    </div>
                                </div>
                                <h3 className="text-2xl font-black mb-2 text-slate-900 dark:text-white uppercase tracking-tight italic">Analisando Dados...</h3>
                                <p className="text-slate-500 dark:text-slate-400 mb-10 text-sm font-bold uppercase tracking-widest">{statusMessage}</p>
                                <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-3 mb-4 overflow-hidden shadow-inner">
                                    <div className="bg-indigo-600 h-full rounded-full transition-all duration-700 ease-out shadow-[0_0_15px_rgba(79,70,229,0.5)]" style={{ width: `${progress}%` }}></div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* RESULTS VIEW */}
                    {activeStep === 'results' && auditResult && (
                        <div className="space-y-6 animate-in fade-in duration-700">
                            {/* Invoice Header */}
                            {auditResult.invoice_header && <InvoiceHeader header={auditResult.invoice_header} />}
                            
                            {/* Consistency Alerts */}
                            {auditResult.consistency_errors && auditResult.consistency_errors.length > 0 && (
                                <ConsistencyAlert errors={auditResult.consistency_errors} />
                            )}

                            {/* Charts Dashboard */}
                            {auditResult.result && <DashboardCharts results={auditResult.result} />}

                            {/* Main Table */}
                            {auditResult.result && (
                                <ResultsTable 
                                    results={auditResult.result} 
                                    onUpdate={() => loadAuditFromHistory(auditId!)} 
                                />
                            )}
                        </div>
                    )}

                    {/* HISTORY VIEW */}
                    {activeStep === 'history' && (
                        <div className="bg-white dark:bg-slate-900 rounded-[2.5rem] border border-slate-200 dark:border-slate-800 p-8 shadow-xl min-h-[600px] animate-in slide-in-from-right-8 duration-500">
                            <div className="flex items-center justify-between mb-8 px-4">
                                <h2 className="text-2xl font-black text-slate-900 dark:text-white uppercase tracking-tight">Histórico Fiscal</h2>
                                <div className="p-2 bg-slate-100 dark:bg-slate-800 rounded-xl text-slate-400">
                                    <History size={20} />
                                </div>
                            </div>

                            <div className="grid grid-cols-1 gap-4">
                                {history.map((audit) => (
                                    <div key={audit.id} className="group bg-slate-50 dark:bg-slate-800/50 hover:bg-white dark:hover:bg-slate-800 rounded-3xl p-6 border border-slate-200 dark:border-slate-700 transition-all flex flex-col md:flex-row items-center justify-between gap-6 hover:shadow-xl hover:shadow-slate-200/50 dark:hover:shadow-none">
                                        <div className="flex items-center gap-6 w-full md:w-auto">
                                            <div className={`w-14 h-14 rounded-2xl flex items-center justify-center shrink-0 shadow-sm ${audit.status === 'completed' ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600' : 'bg-amber-100 dark:bg-amber-900/30 text-amber-600'}`}>
                                                <FileText size={24} />
                                            </div>
                                            <div className="min-w-0">
                                                <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Chave da Nota</p>
                                                <p className="font-bold text-slate-900 dark:text-white truncate max-w-xs md:max-w-md" title={audit.nfe_key}>{audit.nfe_key || audit.id}</p>
                                                <div className="flex gap-4 mt-2">
                                                    <span className="text-[10px] font-bold text-slate-500 uppercase">{new Date(audit.created_at).toLocaleDateString()}</span>
                                                    {audit.summary && (
                                                        <span className="text-[10px] font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-tight">{audit.summary.compliant} OK • {audit.summary.divergent} Divergentes</span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-3 w-full md:w-auto justify-end">
                                            <button onClick={() => loadAuditFromHistory(audit.id)} className="flex-1 md:flex-none px-6 py-3 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-2xl text-[10px] font-black uppercase tracking-widest text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-600 transition-all shadow-sm">
                                                Visualizar
                                            </button>
                                            <button onClick={() => retryAudit(audit.id)} className="p-3 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-2xl text-amber-600 hover:bg-amber-50 dark:hover:bg-slate-600 transition-all shadow-sm">
                                                <RotateCcw size={18} />
                                            </button>
                                            <button onClick={() => deleteAudit(audit.id)} className="p-3 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-2xl text-red-500 hover:bg-red-50 dark:hover:bg-slate-600 transition-all shadow-sm">
                                                <Trash2 size={18} />
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </main>
            </div>

            {/* Floating Back to Top Button */}
            <button
                onClick={scrollToTop}
                className={`fixed bottom-8 right-8 p-4 rounded-2xl bg-indigo-600/80 dark:bg-indigo-500/80 backdrop-blur-md text-white shadow-2xl transition-all duration-300 transform z-50 hover:bg-indigo-700 active:scale-90 border border-white/20 ${
                    showScrollTop ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10 pointer-events-none'
                }`}
                title="Voltar ao Topo"
            >
                <ChevronUp size={24} />
            </button>
        </div>
    );
};

export default AuditInterface;
