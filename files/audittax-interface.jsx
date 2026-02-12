import React, { useState } from 'react';
import { Upload, CheckCircle, AlertCircle, FileText, BarChart3, Download, Loader2, TrendingUp, AlertTriangle, Eye, ChevronRight } from 'lucide-react';

const AuditTaxInterface = () => {
  const [currentView, setCurrentView] = useState('upload'); // upload, processing, results
  const [uploadedFile, setUploadedFile] = useState(null);
  const [auditProgress, setAuditProgress] = useState(0);
  const [auditResults, setAuditResults] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  // Mock audit results for demonstration
  const mockResults = {
    totalItems: 14,
    compliantItems: 0,
    divergentItems: 14,
    totalDivergence: 855.12,
    items: [
      { item: 1, product: '206916', status: 'divergent', issues: ['CST divergente', 'MVA divergente'], value: 31.69 },
      { item: 2, product: '201830', status: 'divergent', issues: ['CST divergente', 'Diferença > 0.05'], value: 18.86 },
      { item: 3, product: '205879', status: 'divergent', issues: ['CST divergente', 'MVA divergente'], value: 9.43 },
      { item: 4, product: '204834', status: 'divergent', issues: ['CST divergente', 'Diferença > 0.05'], value: 16.27 },
      { item: 5, product: '204033', status: 'divergent', issues: ['CST divergente', 'MVA divergente'], value: 16.26 },
      { item: 6, product: '204031', status: 'divergent', issues: ['CST divergente', 'Diferença > 0.05'], value: 22.55 },
    ]
  };

  const handleFileDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith('.xml')) {
      setUploadedFile(file);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setUploadedFile(file);
    }
  };

  const startAudit = () => {
    setCurrentView('processing');
    setAuditProgress(0);
    
    // Simulate audit progress
    const interval = setInterval(() => {
      setAuditProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(() => {
            setAuditResults(mockResults);
            setCurrentView('results');
          }, 500);
          return 100;
        }
        return prev + 10;
      });
    }, 400);
  };

  const resetAudit = () => {
    setCurrentView('upload');
    setUploadedFile(null);
    setAuditProgress(0);
    setAuditResults(null);
  };

  // Upload View
  const UploadView = () => (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl mb-6 shadow-lg">
            <BarChart3 className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-4">
            AuditTax AP
          </h1>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto">
            Auditoria Fiscal Inteligente para o Estado do Amapá
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-3 gap-6 mb-12">
          <div className="bg-white rounded-2xl p-6 shadow-lg border border-slate-200 hover:shadow-xl transition-shadow">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Precisão</p>
                <p className="text-2xl font-bold text-slate-800">99.9%</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-lg border border-slate-200 hover:shadow-xl transition-shadow">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Economia Tempo</p>
                <p className="text-2xl font-bold text-slate-800">95%</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-lg border border-slate-200 hover:shadow-xl transition-shadow">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                <FileText className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Notas Auditadas</p>
                <p className="text-2xl font-bold text-slate-800">2.847</p>
              </div>
            </div>
          </div>
        </div>

        {/* Upload Area */}
        <div className="bg-white rounded-3xl shadow-2xl p-12 border-2 border-dashed border-slate-300 hover:border-blue-500 transition-all">
          <div
            onDrop={handleFileDrop}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            className={`relative ${isDragging ? 'scale-105' : ''} transition-transform`}
          >
            <input
              type="file"
              accept=".xml"
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
            />
            
            {!uploadedFile ? (
              <label htmlFor="file-upload" className="cursor-pointer block text-center">
                <div className="mb-6">
                  <div className="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-3xl mb-6 group-hover:scale-110 transition-transform">
                    <Upload className="w-12 h-12 text-blue-600" />
                  </div>
                </div>
                <h3 className="text-2xl font-bold text-slate-800 mb-3">
                  Arraste seu arquivo XML aqui
                </h3>
                <p className="text-slate-600 mb-6 text-lg">
                  ou clique para selecionar da sua máquina
                </p>
                <div className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:shadow-lg transition-all">
                  <FileText className="w-5 h-5" />
                  <span className="font-semibold">Selecionar Arquivo XML</span>
                </div>
              </label>
            ) : (
              <div className="text-center">
                <div className="inline-flex items-center gap-4 px-8 py-6 bg-green-50 border-2 border-green-200 rounded-2xl mb-8">
                  <CheckCircle className="w-8 h-8 text-green-600" />
                  <div className="text-left">
                    <p className="font-semibold text-green-900 text-lg">{uploadedFile.name}</p>
                    <p className="text-sm text-green-600">{(uploadedFile.size / 1024).toFixed(2)} KB</p>
                  </div>
                </div>
                <div className="flex gap-4 justify-center">
                  <button
                    onClick={startAudit}
                    className="px-10 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-semibold hover:shadow-xl transition-all flex items-center gap-3 text-lg"
                  >
                    <BarChart3 className="w-6 h-6" />
                    Iniciar Auditoria
                    <ChevronRight className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => setUploadedFile(null)}
                    className="px-8 py-4 bg-slate-100 text-slate-700 rounded-xl font-semibold hover:bg-slate-200 transition-all"
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Features */}
        <div className="grid grid-cols-3 gap-8 mt-12">
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-8 h-8 text-blue-600" />
            </div>
            <h4 className="font-semibold text-slate-800 mb-2">Validação Automática</h4>
            <p className="text-sm text-slate-600">Compara XML com Memorial SEFAZ automaticamente</p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="w-8 h-8 text-purple-600" />
            </div>
            <h4 className="font-semibold text-slate-800 mb-2">Detecção de Divergências</h4>
            <p className="text-sm text-slate-600">Identifica erros de NCM, CEST, MVA e valores</p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-green-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Download className="w-8 h-8 text-green-600" />
            </div>
            <h4 className="font-semibold text-slate-800 mb-2">Relatórios Completos</h4>
            <p className="text-sm text-slate-600">Exporta análise detalhada em Excel/PDF</p>
          </div>
        </div>
      </div>
    </div>
  );

  // Processing View
  const ProcessingView = () => (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-8">
      <div className="max-w-2xl w-full">
        <div className="bg-white rounded-3xl shadow-2xl p-12 text-center">
          <div className="mb-8">
            <div className="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-full mb-6 animate-pulse">
              <Loader2 className="w-12 h-12 text-blue-600 animate-spin" />
            </div>
          </div>
          
          <h2 className="text-3xl font-bold text-slate-800 mb-4">
            Processando Auditoria
          </h2>
          <p className="text-slate-600 mb-8 text-lg">
            Comparando dados com Memorial SEFAZ...
          </p>
          
          <div className="relative w-full h-4 bg-slate-200 rounded-full overflow-hidden mb-4">
            <div 
              className="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${auditProgress}%` }}
            >
              <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
            </div>
          </div>
          <p className="text-sm font-semibold text-slate-700">{auditProgress}% Concluído</p>
          
          <div className="mt-8 space-y-3 text-left">
            <div className={`flex items-center gap-3 px-4 py-3 rounded-xl ${auditProgress > 20 ? 'bg-green-50 border border-green-200' : 'bg-slate-50 border border-slate-200'}`}>
              {auditProgress > 20 ? <CheckCircle className="w-5 h-5 text-green-600" /> : <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />}
              <span className={auditProgress > 20 ? 'text-green-800 font-medium' : 'text-slate-600'}>Leitura do XML da NFe</span>
            </div>
            <div className={`flex items-center gap-3 px-4 py-3 rounded-xl ${auditProgress > 50 ? 'bg-green-50 border border-green-200' : 'bg-slate-50 border border-slate-200'}`}>
              {auditProgress > 50 ? <CheckCircle className="w-5 h-5 text-green-600" /> : <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />}
              <span className={auditProgress > 50 ? 'text-green-800 font-medium' : 'text-slate-600'}>Extração Memorial SEFAZ</span>
            </div>
            <div className={`flex items-center gap-3 px-4 py-3 rounded-xl ${auditProgress > 80 ? 'bg-green-50 border border-green-200' : 'bg-slate-50 border border-slate-200'}`}>
              {auditProgress > 80 ? <CheckCircle className="w-5 h-5 text-green-600" /> : <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />}
              <span className={auditProgress > 80 ? 'text-green-800 font-medium' : 'text-slate-600'}>Análise de Divergências</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Results View
  const ResultsView = () => (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-slate-800 mb-2">Resultado da Auditoria</h1>
            <p className="text-slate-600">NFe: {uploadedFile?.name}</p>
          </div>
          <button
            onClick={resetAudit}
            className="px-6 py-3 bg-slate-100 text-slate-700 rounded-xl font-semibold hover:bg-slate-200 transition-all"
          >
            Nova Auditoria
          </button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-2xl p-6 shadow-lg border-l-4 border-blue-600">
            <p className="text-sm text-slate-600 mb-2">Total de Itens</p>
            <p className="text-4xl font-bold text-slate-800">{auditResults.totalItems}</p>
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-lg border-l-4 border-green-600">
            <p className="text-sm text-slate-600 mb-2">Conformes</p>
            <p className="text-4xl font-bold text-green-600">{auditResults.compliantItems}</p>
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-lg border-l-4 border-red-600">
            <p className="text-sm text-slate-600 mb-2">Divergentes</p>
            <p className="text-4xl font-bold text-red-600">{auditResults.divergentItems}</p>
          </div>
          <div className="bg-gradient-to-br from-red-600 to-rose-700 rounded-2xl p-6 shadow-lg text-white">
            <p className="text-sm text-white/80 mb-2">Valor Total Divergente</p>
            <p className="text-3xl font-bold">R$ {auditResults.totalDivergence.toFixed(2)}</p>
          </div>
        </div>

        {/* Results Table */}
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          <div className="px-8 py-6 bg-gradient-to-r from-slate-800 to-slate-700 text-white">
            <h2 className="text-2xl font-bold">Itens Analisados</h2>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b-2 border-slate-200">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">Item</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">Produto</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">Status</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">Divergências</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-slate-700">Valor (R$)</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-slate-700">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {auditResults.items.map((item, index) => (
                  <tr key={index} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4 text-slate-800 font-medium">{item.item}</td>
                    <td className="px-6 py-4 text-slate-800 font-mono text-sm">{item.product}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold ${
                        item.status === 'compliant' 
                          ? 'bg-green-100 text-green-700' 
                          : 'bg-red-100 text-red-700'
                      }`}>
                        {item.status === 'compliant' ? (
                          <><CheckCircle className="w-3 h-3" /> Conforme</>
                        ) : (
                          <><AlertCircle className="w-3 h-3" /> Divergente</>
                        )}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1">
                        {item.issues.map((issue, i) => (
                          <span key={i} className="px-2 py-1 bg-amber-100 text-amber-800 rounded text-xs font-medium">
                            {issue}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right font-semibold text-red-600">
                      {item.value.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <button className="p-2 hover:bg-slate-100 rounded-lg transition-colors">
                        <Eye className="w-4 h-4 text-slate-600" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Export Actions */}
        <div className="mt-8 flex gap-4 justify-end">
          <button className="px-8 py-4 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition-all flex items-center gap-3 shadow-lg">
            <Download className="w-5 h-5" />
            Exportar Excel
          </button>
          <button className="px-8 py-4 bg-red-600 text-white rounded-xl font-semibold hover:bg-red-700 transition-all flex items-center gap-3 shadow-lg">
            <FileText className="w-5 h-5" />
            Exportar PDF
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {currentView === 'upload' && <UploadView />}
      {currentView === 'processing' && <ProcessingView />}
      {currentView === 'results' && <ResultsView />}
    </>
  );
};

export default AuditTaxInterface;
