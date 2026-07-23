import { useAppContext } from '../context/AppContext';
import { ShieldCheck, UserRound, Stethoscope } from 'lucide-react';

export const Sidebar = () => {
  const { role, setRole } = useAppContext();

  return (
    <aside className="w-64 bg-surface border-r border-gray-100 flex flex-col h-full shadow-sm">
      <div className="p-6">
        <h2 className="text-2xl font-bold bg-linear-to-r from-primary to-blue-400 bg-clip-text text-transparent flex items-center gap-2">
          <ShieldCheck className="text-primary" />
          HealthAudit
        </h2>
        <p className="text-sm text-text-muted mt-1">Auditoría Inteligente</p>
      </div>

      <div className="px-6 py-4 border-t border-b border-gray-100">
        <label className="block text-sm font-medium text-text-muted mb-2">
          Seleccionar Perfil
        </label>
        <select
          value={role}
          onChange={(e) => setRole(e.target.value as any)}
          className="w-full bg-background border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary focus:outline-none transition-all"
        >
          <option value="paciente">Paciente</option>
          <option value="medico">Médico</option>
          <option value="auditor">Auditor</option>
        </select>
      </div>

      <nav className="flex-1 p-4 space-y-1">
      </nav>

      <div className="p-4 mt-auto">
        <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
          <div className="w-8 h-8 rounded-full bg-linear-to-tr from-primary to-blue-300 flex items-center justify-center text-white font-bold">
            {role === 'paciente' ? <UserRound size={16} /> : role === 'medico' ? <Stethoscope size={16} /> : <ShieldCheck size={16} />}
          </div>
          <div>
            <p className="text-sm font-semibold capitalize">{role}</p>
            <p className="text-xs text-text-muted">Activo</p>
          </div>
        </div>
      </div>
    </aside>
  );
};
