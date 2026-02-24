import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";

// CONTEXT LOGIN
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";

// PAGINE
import Dashboard from "./pages/Dashboard";
import StatsPage from "./pages/StatsPage";
import ClientsPage from "./pages/ClientsPage";
import ServicesPage from "./pages/ServicesPage";
import HistoryPage from "./pages/HistoryPage";
import SettingsPage from "./pages/SettingsPage";
import MonthlyView from "./pages/MonthlyView";
import WeeklyView from "./pages/WeeklyView";
import AppointmentsPage from "./pages/AppointmentsPage";
import OperatorsPage from "./pages/OperatorsPage";
import LoginPage from "./pages/LoginPage";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter basename="/">
        <Routes>
          {/* LOGIN (non protetto) */}
          <Route path="/login" element={<LoginPage />} />

          {/* HOME = DASHBOARD */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />

          {/* AGENDA */}
          <Route
            path="/appointments"
            element={
              <ProtectedRoute>
                <AppointmentsPage />
              </ProtectedRoute>
            }
          />

          {/* VISTA MENSILE */}
          <Route
            path="/month"
            element={
              <ProtectedRoute>
                <MonthlyView />
              </ProtectedRoute>
            }
          />

          {/* VISTA SETTIMANALE */}
          <Route
            path="/week"
            element={
              <ProtectedRoute>
                <WeeklyView />
              </ProtectedRoute>
            }
          />

          {/* STATISTICHE */}
          <Route
            path="/stats"
            element={
              <ProtectedRoute>
                <StatsPage />
              </ProtectedRoute>
            }
          />

          {/* CLIENTI */}
          <Route
            path="/clients"
            element={
              <ProtectedRoute>
                <ClientsPage />
              </ProtectedRoute>
            }
          />

          {/* SERVIZI */}
          <Route
            path="/services"
            element={
              <ProtectedRoute>
                <ServicesPage />
              </ProtectedRoute>
            }
          />

          {/* OPERATORI */}
          <Route
            path="/operators"
            element={
              <ProtectedRoute>
                <OperatorsPage />
              </ProtectedRoute>
            }
          />

          {/* STORICO */}
          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <HistoryPage />
              </ProtectedRoute>
            }
          />

          {/* IMPOSTAZIONI */}
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <SettingsPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
      <Toaster 
        position="top-right" 
        toastOptions={{
          style: {
            background: '#fff',
            border: '1px solid #E6CCB2',
            color: '#44403C',
          },
        }}
      />
    </AuthProvider>
  );
}
