import { AppProvider, useAppContext } from './context/AppContext';
import { Sidebar } from './components/Sidebar';
import { PatientView } from './components/PatientView';
import { DoctorView } from './components/DoctorView';
import { AuditorView } from './components/AuditorView';

function AppContent() {
  const { role } = useAppContext();

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden font-sans">
      <Sidebar />
      <main className="flex-1 flex flex-col h-full overflow-y-auto">
        <header className="bg-surface px-8 py-5 border-b border-gray-100 flex justify-between items-center sticky top-0 z-10">
          <h1 className="text-2xl font-semibold text-gray-800">Bienvenido</h1>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-100 text-primary flex items-center justify-center font-bold text-lg">
              {role.charAt(0).toUpperCase()}
            </div>
            <span className="font-medium text-gray-700 capitalize">{role}</span>
          </div>
        </header>

        <div className="p-8 max-w-7xl mx-auto w-full">
          {role === 'paciente' && <PatientView />}
          {role === 'medico' && <DoctorView />}
          {role === 'auditor' && <AuditorView />}
        </div>
      </main>
    </div>
  );
}

function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}

export default App;
