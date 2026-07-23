import { useState, useEffect } from 'react';
import { UploadCloud, FileText, Info, CheckCircle, X, UserPlus, Users } from 'lucide-react';
import { getPatients, createPatient, getPatientDetail, uploadDocuments } from '../services/api';
import { useAppContext } from '../context/AppContext';

export const PatientView = () => {
  const [patients, setPatients] = useState<any[]>([]);
  const { selectedPatientId, setSelectedPatientId } = useAppContext();
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const [isCreatingNew, setIsCreatingNew] = useState(false);
  const [patientDocuments, setPatientDocuments] = useState<any[]>([]);

  const loadPatientDetails = async () => {
    if (selectedPatientId) {
      try {
        const details = await getPatientDetail(selectedPatientId);
        setPatientDocuments(details.documents || []);
      } catch (e) {
        console.error("Error loading patient details:", e);
        setPatientDocuments([]);
      }
    } else {
      setPatientDocuments([]);
    }
  };

  useEffect(() => {
    loadPatientDetails();
  }, [selectedPatientId]);
  const [newPatientForm, setNewPatientForm] = useState({ name: '', dni: '', age: '' });
  const [creating, setCreating] = useState(false);

  const loadPatients = () => {
    getPatients().then(setPatients);
  };

  useEffect(() => {
    loadPatients();
  }, []);

  const handleCreatePatient = async () => {
    if (!newPatientForm.name || !newPatientForm.dni) return;
    setCreating(true);
    try {
      const newPatient = await createPatient({
        name: newPatientForm.name,
        dni: newPatientForm.dni,
        age: newPatientForm.age ? parseInt(newPatientForm.age) : undefined
      });
      await loadPatients();
      setSelectedPatientId(newPatient.id);
      setIsCreatingNew(false);
      setNewPatientForm({ name: '', dni: '', age: '' });
      setFeedback(`Paciente ${newPatient.name} creado y seleccionado.`);
    } catch (error) {
      setFeedback(`Error al crear el paciente.`);
    } finally {
      setCreating(false);
    }
  };

  const handleUpload = async () => {
    if (!selectedPatientId || files.length === 0) return;
    setUploading(true);
    try {
      await uploadDocuments(selectedPatientId, files);
      setFeedback(`Se subieron y evaluaron ${files.length} archivos con éxito.`);
      await loadPatientDetails();
    } catch (error) {
      setFeedback(`Hubo un error al subir los archivos.`);
    } finally {
      setUploading(false);
      setFiles([]);
    }
  };

  return (
    <div className="space-y-6">
      <div className="premium-card">
        <h2 className="text-xl font-semibold mb-2">Carga de Documentación</h2>
        <p className="text-text-muted mb-6">Sube tu documentación médica para iniciar el trámite de renovación o solicitud.</p>

        <div className="bg-blue-50 border border-blue-100 rounded-xl p-5 mb-6">
          <div className="flex items-center gap-2 mb-3 text-blue-800">
            <Info className="w-5 h-5" />
            <h3 className="font-semibold text-sm">Documentación requerida</h3>
          </div>
          <ul className="space-y-3 text-sm text-blue-900">
            <li className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 mt-0.5 shrink-0 text-blue-600" />
              <span><strong>Formulario de Diabetes Prevención Salud</strong></span>
            </li>
            <li className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 mt-0.5 shrink-0 text-blue-600" />
              <span><strong>Formulario estructurado</strong> completado y firmado por el médico tratante.</span>
            </li>
            <li className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 mt-0.5 shrink-0 text-blue-600" />
              <span><strong>Estudios complementarios:</strong> Laboratorios. Estudios diagnósticos. Informes médicos.</span>
            </li>
            <li className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 mt-0.5 shrink-0 text-blue-600" />
              <span><strong>Prescripciones médicas:</strong> Medicación para diabetes, tiras reactivas, glucómetros.</span>
            </li>
          </ul>
        </div>

        <div className="mb-6 bg-white p-5 rounded-xl border border-gray-200">
          <div className="flex gap-4 mb-4">
            <button
              onClick={() => setIsCreatingNew(false)}
              className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${!isCreatingNew ? 'bg-primary text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
            >
              <Users className="w-4 h-4" /> Seleccionar Existente
            </button>
            <button
              onClick={() => setIsCreatingNew(true)}
              className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${isCreatingNew ? 'bg-primary text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
            >
              <UserPlus className="w-4 h-4" /> Crear Nuevo
            </button>
          </div>

          {!isCreatingNew ? (
            <div>
              <label className="block text-sm font-medium mb-2">Seleccionar Paciente:</label>
              <select
                className="w-full bg-background border border-gray-200 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
                value={selectedPatientId || ''}
                onChange={(e) => setSelectedPatientId(Number(e.target.value))}
              >
                <option value="">Seleccione un paciente...</option>
                {patients.map(p => (
                  <option key={p.id} value={p.id}>{p.name} - {p.dni}</option>
                ))}
              </select>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Nombre Completo *</label>
                <input
                  type="text"
                  value={newPatientForm.name}
                  onChange={e => setNewPatientForm(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full bg-background border border-gray-200 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary outline-none"
                  placeholder="Ej: Juan Pérez"
                />
              </div>
              <div className="flex gap-4">
                <div className="flex-1">
                  <label className="block text-sm font-medium mb-1">DNI *</label>
                  <input
                    type="text"
                    value={newPatientForm.dni}
                    onChange={e => setNewPatientForm(prev => ({ ...prev, dni: e.target.value }))}
                    className="w-full bg-background border border-gray-200 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary outline-none"
                    placeholder="Ej: 12345678"
                  />
                </div>
                <div className="w-32">
                  <label className="block text-sm font-medium mb-1">Edad</label>
                  <input
                    type="number"
                    value={newPatientForm.age}
                    onChange={e => setNewPatientForm(prev => ({ ...prev, age: e.target.value }))}
                    className="w-full bg-background border border-gray-200 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary outline-none"
                    placeholder="Ej: 45"
                  />
                </div>
              </div>
              <button
                onClick={handleCreatePatient}
                disabled={!newPatientForm.name || !newPatientForm.dni || creating}
                className="w-full py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                {creating ? 'Creando...' : 'Crear y Seleccionar Paciente'}
              </button>
            </div>
          )}
        </div>

        <div
          className="border-2 border-dashed border-gray-300 rounded-xl p-10 text-center hover:bg-gray-50 transition-colors"
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            if (e.dataTransfer.files) {
              const newFiles = Array.from(e.dataTransfer.files);
              setFiles(prev => [...prev, ...newFiles]);
            }
          }}
        >
          <UploadCloud className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <p className="text-sm text-gray-600 mb-2">Arrastra tus archivos aquí o haz clic para seleccionarlos</p>
          <input
            type="file"
            className="hidden"
            id="file-upload"
            multiple
            onChange={(e) => {
              if (e.target.files) {
                const newFiles = Array.from(e.target.files);
                setFiles(prev => [...prev, ...newFiles]);
                e.target.value = '';
              }
            }}
          />
          <label htmlFor="file-upload" className="cursor-pointer text-primary font-medium hover:underline">
            Seleccionar archivos
          </label>
          {files.length > 0 && (
            <div className="mt-4 text-sm text-left text-gray-700 bg-white p-3 rounded-lg border border-gray-100">
              <p className="font-medium mb-2 text-primary">Archivos seleccionados:</p>
              <ul className="space-y-1">
                {files.map((f, i) => (
                  <li key={i} className="flex items-center justify-between gap-2 p-1 hover:bg-gray-50 rounded">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-gray-400 shrink-0" />
                      <span className="truncate">{f.name}</span>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation(); // Evitar que dispare eventos del drag/drop area
                        setFiles(prev => prev.filter((_, index) => index !== i));
                      }}
                      className="text-red-500 hover:text-red-700 p-1 rounded-full hover:bg-red-50 shrink-0"
                      title="Eliminar archivo"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {feedback && (
          <div className="mt-4 p-4 bg-blue-50 text-blue-800 rounded-lg text-sm">
            {feedback}
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={files.length === 0 || !selectedPatientId || uploading}
          className="btn-primary mt-6 w-full flex justify-center items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploading ? 'Subiendo...' :
            (!selectedPatientId ? 'Seleccione un paciente primero' :
              (files.length === 0 ? 'Seleccione documentos' : 'Subir Documentos')
            )
          }
        </button>
      </div>

      <div className="premium-card">
        <h3 className="text-lg font-semibold mb-4">Mis Documentos Subidos</h3>
        <div className="flex flex-col gap-3">
          {patientDocuments.length === 0 ? (
            <p className="text-sm text-gray-500">No hay documentos subidos.</p>
          ) : (
            patientDocuments.map((doc: any) => (
              <div key={doc.id} className="flex items-center gap-3 p-3 border border-gray-100 rounded-lg">
                <FileText className="text-gray-400" />
                <div>
                  <p className="font-medium text-sm">{doc.filename}</p>
                  <p className="text-xs text-text-muted">Estado: {doc.status || 'CARGADO'}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
