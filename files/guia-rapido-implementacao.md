# 🚀 Guia Rápido de Implementação - AuditTax AP

## Setup Rápido (30 minutos)

### Passo 1: Configurar Backend FastAPI

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install fastapi uvicorn celery redis python-multipart aiofiles
```

**Criar arquivo: `backend/api/main.py`**
```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import shutil
import uuid
from pathlib import Path

app = FastAPI(title="AuditTax AP API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Diretórios
UPLOAD_DIR = Path("uploads")
REPORTS_DIR = Path("reports")
UPLOAD_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

@app.get("/")
async def root():
    return {"message": "AuditTax AP API", "version": "2.0.0"}

@app.post("/api/audit/upload")
async def upload_xml(file: UploadFile = File(...)):
    """Upload XML NFe"""
    if not file.filename.endswith('.xml'):
        raise HTTPException(400, "Apenas arquivos XML são aceitos")
    
    # Gerar ID único
    audit_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{audit_id}.xml"
    
    # Salvar arquivo
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Validar XML (integração com código existente)
    try:
        from src.infrastructure.xml_reader import XMLReader
        reader = XMLReader()
        nfe_key, items = reader.parse(str(file_path))
        
        return {
            "audit_id": audit_id,
            "nfe_key": nfe_key,
            "total_items": len(items),
            "filename": file.filename,
            "status": "ready"
        }
    except Exception as e:
        # Remover arquivo se inválido
        file_path.unlink()
        raise HTTPException(400, f"XML inválido: {str(e)}")

@app.post("/api/audit/start/{audit_id}")
async def start_audit(audit_id: str):
    """Inicia auditoria (versão síncrona simplificada)"""
    xml_path = UPLOAD_DIR / f"{audit_id}.xml"
    
    if not xml_path.exists():
        raise HTTPException(404, "Arquivo não encontrado")
    
    try:
        # Integração com código existente
        from src.services.audit_service import AuditService
        
        service = AuditService()
        report_path = service.process_audit(str(xml_path))
        
        # Mover relatório para diretório de reports
        report_final = REPORTS_DIR / f"{audit_id}_report.csv"
        shutil.move(report_path, report_final)
        
        return {
            "audit_id": audit_id,
            "status": "completed",
            "report_path": str(report_final)
        }
    except Exception as e:
        raise HTTPException(500, f"Erro na auditoria: {str(e)}")

@app.get("/api/audit/download/{audit_id}")
async def download_report(audit_id: str):
    """Download do relatório"""
    report_path = REPORTS_DIR / f"{audit_id}_report.csv"
    
    if not report_path.exists():
        raise HTTPException(404, "Relatório não encontrado")
    
    return FileResponse(
        report_path,
        media_type="text/csv",
        filename=f"auditoria_{audit_id}.csv"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Rodar servidor:**
```bash
python backend/api/main.py
```

---

### Passo 2: Configurar Frontend React (Versão Simplificada)

```bash
# Criar projeto React
npx create-react-app frontend
cd frontend
npm install axios lucide-react
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**Configurar Tailwind: `tailwind.config.js`**
```javascript
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

**Adicionar ao `src/index.css`:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

**Criar componente simplificado: `src/App.jsx`**
```javascript
import React, { useState } from 'react';
import { Upload, Download, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

function App() {
  const [file, setFile] = useState(null);
  const [auditId, setAuditId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.name.endsWith('.xml')) {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Por favor, selecione um arquivo XML válido');
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const uploadResponse = await axios.post(`${API_URL}/audit/upload`, formData);
      setAuditId(uploadResponse.data.audit_id);

      const auditResponse = await axios.post(
        `${API_URL}/audit/start/${uploadResponse.data.audit_id}`
      );
      
      setResult(auditResponse.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao processar auditoria');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!auditId) return;

    try {
      const response = await axios.get(`${API_URL}/audit/download/${auditId}`, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `auditoria_${auditId}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError('Erro ao baixar relatório');
    }
  };

  const reset = () => {
    setFile(null);
    setAuditId(null);
    setResult(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-blue-600 mb-4">
            AuditTax AP
          </h1>
          <p className="text-xl text-slate-600">
            Auditoria Fiscal Inteligente
          </p>
        </div>

        {/* Upload Card */}
        {!result && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="text-center">
              <input
                type="file"
                accept=".xml"
                onChange={handleFileSelect}
                className="hidden"
                id="file-input"
              />
              
              {!file ? (
                <label
                  htmlFor="file-input"
                  className="cursor-pointer block"
                >
                  <div className="border-2 border-dashed border-slate-300 rounded-xl p-12 hover:border-blue-500 transition-colors">
                    <Upload className="w-16 h-16 text-blue-500 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-slate-800 mb-2">
                      Selecione o arquivo XML da NFe
                    </h3>
                    <p className="text-slate-600">
                      Clique para selecionar ou arraste o arquivo aqui
                    </p>
                  </div>
                </label>
              ) : (
                <div>
                  <div className="bg-green-50 border border-green-200 rounded-xl p-6 mb-6">
                    <CheckCircle className="w-8 h-8 text-green-600 mx-auto mb-2" />
                    <p className="font-semibold text-green-900">{file.name}</p>
                    <p className="text-sm text-green-600">
                      {(file.size / 1024).toFixed(2)} KB
                    </p>
                  </div>

                  <div className="flex gap-4 justify-center">
                    <button
                      onClick={handleUpload}
                      disabled={loading}
                      className="px-8 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 disabled:bg-slate-300 transition-colors flex items-center gap-2"
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" />
                          Processando...
                        </>
                      ) : (
                        <>
                          <CheckCircle className="w-5 h-5" />
                          Iniciar Auditoria
                        </>
                      )}
                    </button>
                    
                    <button
                      onClick={reset}
                      disabled={loading}
                      className="px-8 py-3 bg-slate-100 text-slate-700 rounded-xl font-semibold hover:bg-slate-200 transition-colors"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              )}
            </div>

            {error && (
              <div className="mt-6 bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <p className="text-red-800">{error}</p>
              </div>
            )}
          </div>
        )}

        {/* Results Card */}
        {result && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="text-center mb-8">
              <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
              <h2 className="text-3xl font-bold text-slate-800 mb-2">
                Auditoria Concluída!
              </h2>
              <p className="text-slate-600">
                O relatório foi gerado com sucesso
              </p>
            </div>

            <div className="space-y-4 mb-8">
              <div className="bg-slate-50 rounded-xl p-4 flex justify-between items-center">
                <span className="text-slate-600">ID da Auditoria:</span>
                <span className="font-mono font-semibold text-slate-800">
                  {result.audit_id}
                </span>
              </div>
              <div className="bg-slate-50 rounded-xl p-4 flex justify-between items-center">
                <span className="text-slate-600">Status:</span>
                <span className="font-semibold text-green-600">
                  {result.status}
                </span>
              </div>
            </div>

            <div className="flex gap-4 justify-center">
              <button
                onClick={handleDownload}
                className="px-8 py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition-colors flex items-center gap-2"
              >
                <Download className="w-5 h-5" />
                Baixar Relatório CSV
              </button>
              
              <button
                onClick={reset}
                className="px-8 py-3 bg-slate-100 text-slate-700 rounded-xl font-semibold hover:bg-slate-200 transition-colors"
              >
                Nova Auditoria
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
```

**Rodar frontend:**
```bash
npm start
```

---

## 🎯 Testes Rápidos

### Testar API (Terminal)
```bash
# Upload
curl -X POST "http://localhost:8000/api/audit/upload" \
  -F "file=@tests/samples/nfe_sample.xml"

# Resposta esperada:
# {
#   "audit_id": "uuid-aqui",
#   "nfe_key": "chave-nfe",
#   "total_items": 2,
#   "status": "ready"
# }

# Iniciar auditoria
curl -X POST "http://localhost:8000/api/audit/start/uuid-aqui"

# Download relatório
curl "http://localhost:8000/api/audit/download/uuid-aqui" \
  --output relatorio.csv
```

---

## 🔧 Próximos Passos (Melhorias)

### 1. Adicionar Validação de NFe-Key
```python
import re

def validate_nfe_key(key: str) -> bool:
    """Valida chave NFe (44 dígitos)"""
    return bool(re.match(r'^\d{44}$', key))

@app.post("/api/audit/upload")
async def upload_xml(file: UploadFile = File(...)):
    # ... código existente ...
    
    # Validar chave
    if not validate_nfe_key(nfe_key):
        file_path.unlink()
        raise HTTPException(400, "Chave NFe inválida")
    
    return {...}
```

### 2. Adicionar Feedback de Progresso (Polling Simples)
```python
# Backend
progress_store = {}  # Em produção, usar Redis

@app.get("/api/audit/status/{audit_id}")
async def get_status(audit_id: str):
    return progress_store.get(audit_id, {"status": "not_found"})

# Frontend
const pollStatus = async (auditId) => {
  const interval = setInterval(async () => {
    const response = await axios.get(`${API_URL}/audit/status/${auditId}`);
    
    if (response.data.status === 'completed') {
      clearInterval(interval);
      setResult(response.data);
    }
  }, 2000);
};
```

### 3. Adicionar Histórico (SQLite)
```python
import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('audittax.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS audits (
            id TEXT PRIMARY KEY,
            nfe_key TEXT,
            created_at TEXT,
            status TEXT,
            total_items INTEGER
        )
    ''')
    conn.commit()
    conn.close()

@app.on_event("startup")
async def startup():
    init_db()

@app.post("/api/audit/start/{audit_id}")
async def start_audit(audit_id: str):
    # ... código existente ...
    
    # Salvar no banco
    conn = sqlite3.connect('audittax.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO audits VALUES (?, ?, ?, ?, ?)
    ''', (audit_id, nfe_key, datetime.now().isoformat(), 'completed', total_items))
    conn.commit()
    conn.close()

@app.get("/api/audits/history")
async def get_history():
    conn = sqlite3.connect('audittax.db')
    c = conn.cursor()
    c.execute('SELECT * FROM audits ORDER BY created_at DESC LIMIT 50')
    rows = c.fetchall()
    conn.close()
    
    return [
        {
            "id": row[0],
            "nfe_key": row[1],
            "created_at": row[2],
            "status": row[3],
            "total_items": row[4]
        }
        for row in rows
    ]
```

---

## 📊 Monitoramento Simples

### Logs Estruturados
```python
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/api_{datetime.now():%Y%m%d}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@app.post("/api/audit/start/{audit_id}")
async def start_audit(audit_id: str):
    logger.info(f"Iniciando auditoria: {audit_id}")
    
    try:
        # ... código ...
        logger.info(f"Auditoria concluída: {audit_id}")
        return result
    except Exception as e:
        logger.error(f"Erro na auditoria {audit_id}: {str(e)}")
        raise
```

---

## 🐳 Docker (Opcional mas Recomendado)

**Criar `docker-compose.yml`:**
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./uploads:/app/uploads
      - ./reports:/app/reports
    environment:
      - PYTHONUNBUFFERED=1
    command: uvicorn api.main:app --host 0.0.0.0 --reload

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    command: npm start

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

**Rodar tudo:**
```bash
docker-compose up
```

---

## ✅ Checklist de Implementação

- [ ] Backend FastAPI configurado
- [ ] Endpoints de upload e auditoria funcionando
- [ ] Frontend React com Tailwind
- [ ] Upload de arquivo implementado
- [ ] Download de relatório funcionando
- [ ] Tratamento de erros
- [ ] Validação de XML
- [ ] Logs estruturados
- [ ] Testes básicos
- [ ] README atualizado

---

## 🎓 Recursos de Aprendizado

- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **Tailwind CSS**: https://tailwindcss.com/docs
- **Axios**: https://axios-http.com/docs/intro

---

**Tempo estimado de implementação desta versão simplificada: 4-6 horas**

Para versão completa com Celery, WebSocket, Analytics: **~6 semanas** (conforme documento principal)
