import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export interface AuditStatus {
    audit_id: string;
    status: 'ready' | 'processing' | 'completed' | 'error';
    progress: number;
    step: string;
    result?: any;
    error?: string;
    report_path?: string;
}

export const uploadXml = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post(`${API_URL}/audit/upload`, formData);
    return response.data;
};

export const startAudit = async (auditId: string) => {
    const response = await axios.post(`${API_URL}/audit/start/${auditId}`);
    return response.data;
};

export const getAuditStatus = async (auditId: string): Promise<AuditStatus> => {
    const response = await axios.get(`${API_URL}/audit/status/${auditId}`);
    return response.data;
};

export const getDownloadUrl = (auditId: string) => {
    return `${API_URL}/audit/download/${auditId}`;
};

export interface AuditItem {
    item_index: number;
    product_code: string;
    product_name: string;
    status: 'compliant' | 'divergent';
    issues: string[];
}

export interface AuditResultsResponse {
    audit_id: string;
    summary: {
        total: number;
        compliant: number;
        divergent: number;
    };
    items: AuditItem[];
}

export const getAuditResults = async (auditId: string): Promise<AuditResultsResponse> => {
    const response = await axios.get(`${API_URL}/audit/${auditId}/results`);
    return response.data;
};
