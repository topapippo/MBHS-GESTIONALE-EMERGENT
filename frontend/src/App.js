import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster, toast } from "sonner";
import { useEffect, useState } from "react";

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
import PlanningPage from "./pages/PlanningPage";
import PrepaidCardsPage from "./pages/PrepaidCardsPage";
import ReportIncassiPage from "./pages/ReportIncassiPage";
import BackupPage from "./pages/BackupPage";
import BookingPage from "./pages/BookingPage";
import LoyaltyPage from "./pages/LoyaltyPage";
import RemindersPage from "./pages/RemindersPage";
import DailySummaryPage from "./pages/DailySummaryPage";
import WebsitePage from "./pages/WebsitePage";
import WebsiteAdminPage from "./pages/WebsiteAdminPage";
import LoginPage from "./pages/LoginPage";
import { useAuth } from "./context/AuthContext";

// Offline indicator component
function OfflineIndicator() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      toast.success('Connessione ripristinata!');
    };
    const handleOffline = () => {
      setIsOnline(false);
      toast.warning('Sei offline. I dati potrebbero non essere aggiornati.');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (isOnline) return null;

  return (
    <div className="fixed top-0 left-0 right-0 bg-amber-500 text-white text-center py-2 text-sm z-50 font-medium">
      Modalità Offline - I dati mostrati potrebbero non essere aggiornati
    </div>
  );
}

// Homepage: landing page for visitors, planning for logged-in users
function HomePage() {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center"><div className="w-8 h-8 border-4 border-[#0EA5E9] border-t-transparent rounded-full animate-spin" /></div>;
  if (user) return <PlanningPage />;
  return <BookingPage />;
}

export default function App() {
  return (
    <AuthProvider>
      <OfflineIndicator />
      <BrowserRouter basename="/">
        <Routes>
          {/* LOGIN (non protetto) */}
          <Route path="/login" element={<LoginPage />} />

          {/* HOME = Landing page per visitatori, Planning per loggati */}
          <Route path="/" element={<HomePage />} />

          {/* PLANNING dedicato */}
          <Route
            path="/planning"
            element={
              <ProtectedRoute>
                <PlanningPage />
              </ProtectedRoute>
            }
          />

          {/* DASHBOARD */}
          <Route
            path="/dashboard"
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

          {/* CARD / ABBONAMENTI */}
          <Route
            path="/cards"
            element={
              <ProtectedRoute>
                <PrepaidCardsPage />
              </ProtectedRoute>
            }
          />

          {/* REPORT INCASSI */}
          <Route
            path="/incassi"
            element={
              <ProtectedRoute>
                <ReportIncassiPage />
              </ProtectedRoute>
            }
          />

          {/* BACKUP */}
          <Route
            path="/backup"
            element={
              <ProtectedRoute>
                <BackupPage />
              </ProtectedRoute>
            }
          />

          {/* PRENOTAZIONE ONLINE (pubblica) */}
          <Route path="/prenota" element={<BookingPage />} />

          {/* PROGRAMMA FEDELTÀ */}
          <Route
            path="/loyalty"
            element={
              <ProtectedRoute>
                <LoyaltyPage />
              </ProtectedRoute>
            }
          />

          {/* PROMEMORIA & RICHIAMI */}
          <Route
            path="/reminders"
            element={
              <ProtectedRoute>
                <RemindersPage />
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

          {/* RIEPILOGO GIORNALIERO */}
          <Route
            path="/daily-summary"
            element={
              <ProtectedRoute>
                <DailySummaryPage />
              </ProtectedRoute>
            }
          />

          {/* SITO WEB PUBBLICO */}
          <Route path="/sito" element={<WebsitePage />} />

          {/* GESTIONE SITO WEB (admin) */}
          <Route
            path="/gestione-sito"
            element={
              <ProtectedRoute>
                <WebsiteAdminPage />
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
