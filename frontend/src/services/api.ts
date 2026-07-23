import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/api',
});

export const getPatients = async (status?: string) => {
  const res = await api.get('/patients', { params: { status } });
  return res.data;
};

export const createPatient = async (data: { name: string; dni: string; age?: number; clinical_history?: string }) => {
  const res = await api.post('/patients', data);
  return res.data;
};

export const getPatientDetail = async (id: number) => {
  const res = await api.get(`/patients/${id}`);
  return res.data;
};

export const uploadDocuments = async (patientId: number, files: File[]) => {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('documents', file);
  });
  
  const res = await api.post(`/patients/${patientId}/documents`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

export const addComment = async (patientId: number, text: string, role: string) => {
  const res = await api.post(`/patients/${patientId}/comments`, { text, role });
  return res.data;
};

export const auditPatient = async (patientId: number, action: string, notes: string) => {
  const res = await api.post(`/patients/${patientId}/audit`, { action, notes });
  return res.data;
};
