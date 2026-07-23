import { createContext, useContext, useState, ReactNode } from 'react';

type Role = 'paciente' | 'medico' | 'auditor';

interface AppContextType {
  role: Role;
  setRole: (role: Role) => void;
  selectedPatientId: number | null;
  setSelectedPatientId: (id: number | null) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider = ({ children }: { children: ReactNode }) => {
  const [role, setRole] = useState<Role>('paciente');
  const [selectedPatientId, setSelectedPatientId] = useState<number | null>(null);

  return (
    <AppContext.Provider value={{ role, setRole, selectedPatientId, setSelectedPatientId }}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};
