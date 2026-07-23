import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Eye, ShieldCheck, FileText, CheckCircle2, AlertCircle } from 'lucide-react';
import { getPatients, getPatientDetail, auditPatient } from '../services/api';

export const AuditorView = () => {
  const [patients, setPatients] = useState<any[]>([]);
  const [selectedFilter, setSelectedFilter] = useState<string>('');
  const [selectedPatientId, setSelectedPatientId] = useState<number | null>(null);
  const [patientDetail, setPatientDetail] = useState<any>(null);
  const [auditorNotes, setAuditorNotes] = useState('');

  const fetchPatients = () => {
    getPatients(selectedFilter || undefined).then(setPatients);
  };

  useEffect(() => {
    fetchPatients();
  }, [selectedFilter]);

  useEffect(() => {
    if (selectedPatientId) {
      getPatientDetail(selectedPatientId).then(setPatientDetail);
    } else {
      setPatientDetail(null);
    }
  }, [selectedPatientId]);

  const handleAudit = async (action: string) => {
    if (!selectedPatientId) return;
    await auditPatient(selectedPatientId, action, auditorNotes);
    alert(`Paciente auditado con acción: ${action}`);
    setSelectedPatientId(null);
    setAuditorNotes('');
    fetchPatients();
  };

  return (
    <div className="space-y-6">
      {/* Metrics */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="premium-card text-center p-4">
          <p className="text-sm text-text-muted font-medium mb-1">Total</p>
          <p className="text-2xl font-bold">{patients.length}</p>
        </div>
        <div className="premium-card text-center p-4">
          <p className="text-sm text-text-muted font-medium mb-1">Pendientes</p>
          <p className="text-2xl font-bold text-yellow-600">
            {patients.filter(p => p.status === 'PENDIENTE' || p.status === 'RENOVACION_PENDIENTE').length}
          </p>
        </div>
        <div className="premium-card text-center p-4">
          <p className="text-sm text-text-muted font-medium mb-1">Aprobados</p>
          <p className="text-2xl font-bold text-green-600">
            {patients.filter(p => p.status?.includes('APROBADO')).length}
          </p>
        </div>
        <div className="premium-card text-center p-4">
          <p className="text-sm text-text-muted font-medium mb-1">Rechazados</p>
          <p className="text-2xl font-bold text-red-600">
            {patients.filter(p => p.status === 'RECHAZADO').length}
          </p>
        </div>
      </div>

      <div className="flex gap-2 mb-4">
        {['', 'PENDIENTE', 'RENOVACION_PENDIENTE', 'APROBADO', 'RECHAZADO'].map(f => (
          <button
            key={f}
            onClick={() => setSelectedFilter(f)}
            className={`px-4 py-2 text-sm font-medium rounded-full transition-colors ${selectedFilter === f ? 'bg-primary text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
          >
            {f === '' ? 'Todos' : (f === 'RENOVACION_PENDIENTE' ? 'RENOVACIÓN' : f)}
          </button>
        ))}
      </div>

      <div className="premium-card p-0 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-100 text-sm font-semibold text-gray-600">
              <th className="p-4">Paciente</th>
              <th className="p-4">DNI</th>
              <th className="p-4">Estado</th>
              <th className="p-4 text-center">Acción</th>
            </tr>
          </thead>
          <tbody>
            {patients.map(p => (
              <tr key={p.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                <td className="p-4 font-medium">{p.name}</td>
                <td className="p-4 text-text-muted">{p.dni}</td>
                <td className="p-4">
                  <span className="text-xs px-2 py-1 bg-gray-100 rounded-md font-semibold">{p.status}</span>
                </td>
                <td className="p-4 text-center">
                  <button
                    onClick={() => setSelectedPatientId(p.id)}
                    className="text-primary hover:text-blue-700 p-2 rounded-lg hover:bg-blue-50 transition-colors"
                  >
                    <Eye size={18} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal / Detail View for Audit */}
      {selectedPatientId && patientDetail && (
        <div className="fixed inset-0 bg-gray-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-surface w-full max-w-4xl max-h-[90vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="p-6 border-b flex justify-between items-center bg-gray-50">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <ShieldCheck className="text-primary" /> Auditoría: {patientDetail.name}
              </h2>
              <button onClick={() => setSelectedPatientId(null)} className="text-gray-400 hover:text-gray-700 text-2xl font-bold">
                &times;
              </button>
            </div>

            <div className="p-6 overflow-y-auto flex-1 grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold text-gray-700 mb-3">Documentos Activos</h3>
                <div className="space-y-3 mb-6">
                  {patientDetail.documents?.filter((d: any) => !d.isArchived).map((d: any) => (
                    <div key={d.id} className="p-3 border rounded-lg flex items-center justify-between">
                      <div className="flex items-start gap-3">
                        <FileText className="text-gray-400 mt-1" size={20} />
                        <div>
                          <p className="font-medium text-sm">{d.filename}</p>
                          <p className="text-xs text-gray-500">Tipo: {d.docType}</p>
                          <p className="text-xs font-semibold text-blue-600 mt-1">Confiabilidad: {((d.reliabilityScore || 0) * 100).toFixed(1)}%</p>
                        </div>
                      </div>
                      <a href={`http://localhost:5000/${d.filePath.replace(/\\/g, '/')}`} target="_blank" rel="noopener noreferrer" className="p-2 text-primary hover:bg-blue-50 rounded-lg transition-colors" title="Abrir Documento">
                        <Eye size={18} />
                      </a>
                    </div>
                  ))}
                  {(!patientDetail.documents || patientDetail.documents.filter((d: any) => !d.isArchived).length === 0) && (
                    <p className="text-sm text-gray-500 italic">No hay documentos cargados.</p>
                  )}
                </div>

                {patientDetail.documents?.some((d: any) => d.isArchived) && (
                  <>
                    <h3 className="font-semibold text-gray-700 mb-3 border-t pt-4">Historial de Documentos</h3>
                    <div className="space-y-3">
                      {patientDetail.documents?.filter((d: any) => d.isArchived).map((d: any) => (
                        <div key={d.id} className="p-2 border border-gray-100 bg-gray-50 rounded-lg flex items-center justify-between opacity-80">
                          <div className="flex items-center gap-2">
                            <FileText className="text-gray-400" size={16} />
                            <p className="font-medium text-xs text-gray-600">{d.filename}</p>
                          </div>
                          <a href={`http://localhost:5000/${d.filePath.replace(/\\/g, '/')}`} target="_blank" rel="noopener noreferrer" className="p-1 text-primary hover:bg-blue-50 rounded-lg transition-colors" title="Abrir Documento">
                            <Eye size={16} />
                          </a>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>

              <div className="flex flex-col h-full max-h-full">
                <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <CheckCircle2 className="text-green-500" size={18} /> Sugerencia IA (Agente)
                </h3>
                <div className="flex-1 bg-white border border-blue-100 shadow-sm rounded-xl p-6 text-sm text-gray-800 overflow-y-auto">
                  {(() => {
                    const activeReview = patientDetail.auditReviews?.find((r: any) => !r.isArchived);
                    if (activeReview?.aiSuggestion) {
                      return (
                        <ReactMarkdown
                          components={{
                            h1: ({node, ...props}) => <h1 className="text-xl font-bold text-blue-900 mt-6 mb-3 pb-2 border-b border-blue-100 first:mt-0" {...props} />,
                            h2: ({node, ...props}) => <h2 className="text-lg font-semibold text-blue-800 mt-5 mb-2 first:mt-0" {...props} />,
                            h3: ({node, ...props}) => <h3 className="text-md font-semibold text-blue-700 mt-4 mb-2 first:mt-0" {...props} />,
                            p: ({node, ...props}) => <p className="mb-3 leading-relaxed text-gray-700" {...props} />,
                            ul: ({node, ...props}) => <ul className="mb-4 space-y-2 ml-1" {...props} />,
                            ol: ({node, ...props}) => <ol className="list-decimal pl-5 mb-4 space-y-2" {...props} />,
                            li: ({node, ...props}) => (
                              <li className="flex flex-wrap items-start">
                                <span className="text-blue-500 mr-2 mt-0.5">•</span>
                                <span className="flex-1 text-gray-700" {...props} />
                              </li>
                            ),
                            strong: ({node, ...props}) => <strong className="font-semibold text-gray-900" {...props} />,
                            em: ({node, ...props}) => <em className="italic text-gray-600" {...props} />,
                          }}
                        >
                          {activeReview.aiSuggestion}
                        </ReactMarkdown>
                      );
                    }
                    return <p className="text-gray-500 italic text-center mt-10">No hay evaluación de IA disponible.</p>;
                  })()}
                </div>
              </div>
            </div>

            <div className="p-6 border-t bg-gray-50">
              <textarea
                className="w-full bg-white border border-gray-200 rounded-lg p-3 text-sm focus:ring-2 focus:ring-primary focus:outline-none mb-4"
                rows={3}
                placeholder="Notas internas de auditoría..."
                value={auditorNotes}
                onChange={(e) => setAuditorNotes(e.target.value)}
              />

              <div className="flex flex-wrap gap-2 justify-end">
                <button onClick={() => handleAudit('REQUIERE_INFO')} className="px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-white font-medium rounded-lg text-sm transition-colors flex items-center gap-2">
                  <AlertCircle size={16} /> Solicitar Info
                </button>
                <button onClick={() => handleAudit('RECHAZAR')} className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white font-medium rounded-lg text-sm transition-colors">
                  Rechazo
                </button>
                <button onClick={() => handleAudit('APROBAR_PARCIAL')} className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-lg text-sm transition-colors">
                  Aprobación Parcial
                </button>
                <button onClick={() => handleAudit('APROBAR')} className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white font-medium rounded-lg text-sm transition-colors flex items-center gap-2">
                  <CheckCircle2 size={16} /> Aprobación Completa
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
