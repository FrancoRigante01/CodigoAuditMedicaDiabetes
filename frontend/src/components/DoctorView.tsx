import { useState, useEffect } from 'react';
import { FileText, Send, UserRound, Eye } from 'lucide-react';
import { getPatients, getPatientDetail, addComment } from '../services/api';
import { useAppContext } from '../context/AppContext';

export const DoctorView = () => {
  const [patients, setPatients] = useState<any[]>([]);
  const { selectedPatientId, setSelectedPatientId } = useAppContext();
  const [patientDetail, setPatientDetail] = useState<any>(null);
  const [newComment, setNewComment] = useState('');

  useEffect(() => {
    getPatients().then(setPatients);
  }, []);

  useEffect(() => {
    if (selectedPatientId) {
      getPatientDetail(selectedPatientId).then(setPatientDetail);
    } else {
      setPatientDetail(null);
    }
  }, [selectedPatientId]);

  const handleSendComment = async () => {
    if (!selectedPatientId || !newComment.trim()) return;
    await addComment(selectedPatientId, newComment, 'MEDICO');
    setNewComment('');
    // Refresh details
    const refreshed = await getPatientDetail(selectedPatientId);
    setPatientDetail(refreshed);
  };

  return (
    <div className="space-y-6">
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">Seleccionar Paciente:</label>
        <select
          className="w-full bg-surface border border-gray-200 rounded-lg px-4 py-2"
          value={selectedPatientId || ''}
          onChange={(e) => setSelectedPatientId(Number(e.target.value))}
        >
          <option value="">Seleccione un paciente...</option>
          {patients.map(p => (
            <option key={p.id} value={p.id}>{p.name} - {p.dni}</option>
          ))}
        </select>
      </div>

      {patientDetail ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="premium-card flex flex-col">
            <h3 className="text-lg font-semibold mb-4 border-b pb-2 flex items-center gap-2">
              <UserRound className="text-primary" /> Resumen del Paciente
            </h3>
            <div className="space-y-3 flex-1">
              <p><span className="font-medium text-gray-500">Nombre:</span> {patientDetail.name}</p>
              <p><span className="font-medium text-gray-500">DNI:</span> {patientDetail.dni}</p>
              <p><span className="font-medium text-gray-500">Edad:</span> {patientDetail.age || 'N/A'}</p>
              <p><span className="font-medium text-gray-500">Historia Clínica:</span> {patientDetail.clinical_history || 'N/A'}</p>
              <p><span className="font-medium text-gray-500">Estado Actual:</span>
                <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-semibold">
                  {patientDetail.status}
                </span>
              </p>
            </div>
          </div>

          <div className="premium-card flex flex-col">
            <h3 className="text-lg font-semibold mb-4 border-b pb-2">Documentación Subida</h3>
            <div className="space-y-3 overflow-y-auto max-h-62.5">
              {patientDetail.documents?.length > 0 ? (
                patientDetail.documents.map((doc: any) => (
                  <div key={doc.id} className="flex items-center gap-3 p-3 border border-gray-100 rounded-lg">
                    <FileText className="text-gray-400" />
                    <div className="flex-1">
                      <p className="font-medium text-sm">{doc.filename}</p>
                      <p className="text-xs text-text-muted">Tipo: {doc.docType || 'Desconocido'}</p>
                    </div>
                    <span className="text-xs px-2 py-1 bg-gray-100 rounded">{doc.status}</span>
                    <a href={`http://localhost:5000/${doc.filePath.replace(/\\/g, '/')}`} target="_blank" rel="noopener noreferrer" className="ml-2 p-2 text-primary hover:bg-blue-50 rounded-lg transition-colors" title="Abrir Documento">
                      <Eye size={18} />
                    </a>
                  </div>
                ))
              ) : (
                <p className="text-sm text-text-muted">No hay documentos subidos.</p>
              )}
            </div>
          </div>

          <div className="premium-card md:col-span-2">
            <h3 className="text-lg font-semibold mb-4 border-b pb-2">Comentarios y Solicitudes</h3>
            <div className="space-y-4 mb-4 max-h-75 overflow-y-auto">
              {patientDetail.comments?.length > 0 ? (
                patientDetail.comments.map((c: any) => (
                  <div key={c.id} className="p-3 bg-gray-50 rounded-lg border border-gray-100">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold bg-gray-200 px-2 py-1 rounded capitalize">{c.authorRole}</span>
                      <span className="text-xs text-gray-400">{new Date(c.createdAt).toLocaleString()}</span>
                    </div>
                    <p className="text-sm text-gray-700">{c.text}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-text-muted">No hay comentarios aún.</p>
              )}
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Escriba un comentario o solicite más información..."
                className="flex-1 bg-background border border-gray-200 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <button
                onClick={handleSendComment}
                className="btn-primary flex items-center gap-2"
                disabled={!newComment.trim()}
              >
                <Send size={16} /> Enviar
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="premium-card py-12 text-center text-text-muted">
          Seleccione un paciente para ver sus detalles.
        </div>
      )}
    </div>
  );
};
