import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Users, Euro, Calendar, Clock, TrendingUp, Plus, ChevronRight,
  Scissors, UserCheck, CalendarDays, CalendarRange, BarChart3,
  CreditCard, Gift, Bell, Download, Globe, Settings
} from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const MODULES = [
  { path: '/planning', label: 'Planning', desc: 'Vista giornaliera', icon: Calendar, color: '#0EA5E9' },
  { path: '/weekly', label: 'Settimanale', desc: 'Vista settimanale', icon: CalendarDays, color: '#789F8A' },
  { path: '/monthly', label: 'Mensile', desc: 'Vista mensile', icon: CalendarRange, color: '#E9C46A' },
  { path: '/appointments', label: 'Appuntamenti', desc: 'Nuovo appuntamento', icon: Plus, color: '#0284C7' },
  { path: '/clients', label: 'Clienti', desc: 'Gestione clienti', icon: Users, color: '#334155' },
  { path: '/services', label: 'Servizi', desc: 'Listino prezzi', icon: Scissors, color: '#C084FC' },
  { path: '/operators', label: 'Operatori', desc: 'Gestione staff', icon: UserCheck, color: '#F59E0B' },
  { path: '/stats', label: 'Statistiche', desc: 'Report e grafici', icon: BarChart3, color: '#EF4444' },
  { path: '/incassi', label: 'Incassi', desc: 'Report pagamenti', icon: Euro, color: '#10B981' },
  { path: '/daily-summary', label: 'Riepilogo', desc: 'Riepilogo giornaliero', icon: BarChart3, color: '#F43F5E' },
  { path: '/prepaid', label: 'Card Prepagate', desc: 'Abbonamenti', icon: CreditCard, color: '#6366F1' },
  { path: '/loyalty', label: 'Fedeltà', desc: 'Programma punti', icon: Gift, color: '#EC4899' },
  { path: '/reminders', label: 'Promemoria', desc: 'Notifiche clienti', icon: Bell, color: '#F97316' },
  { path: '/backup', label: 'Backup', desc: 'Esporta dati', icon: Download, color: '#64748B' },
  { path: '/prenota', label: 'Booking Online', desc: 'Pagina pubblica', icon: Globe, color: '#14B8A6' },
  { path: '/settings', label: 'Impostazioni', desc: 'Configurazione', icon: Settings, color: '#78716C' },
];

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => { fetchDashboardStats(); }, []);

  const fetchDashboardStats = async () => {
    try {
      const res = await axios.get(`${API}/stats/dashboard`);
      setStats(res.data);
    } catch (err) { console.error('Error fetching stats:', err); }
    finally { setLoading(false); }
  };

  if (loading) {
    return (
      <Layout>
        <div className="space-y-6">
          <Skeleton className="h-8 w-48" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (<Skeleton key={i} className="h-32" />))}
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8" data-testid="dashboard-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="font-playfair text-3xl md:text-4xl font-medium text-[#0F172A]">Buongiorno!</h1>
            <p className="text-[#334155] mt-1 font-manrope">{format(new Date(), "EEEE d MMMM yyyy", { locale: it })}</p>
          </div>
          <Link to="/appointments">
            <Button data-testid="new-appointment-btn" className="bg-[#0EA5E9] hover:bg-[#0284C7] text-white shadow-lg shadow-[#0EA5E9]/20 transition-all active:scale-95">
              <Plus className="w-5 h-5 mr-2" /> Nuovo Appuntamento
            </Button>
          </Link>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { title: "Appuntamenti Oggi", value: stats?.today_appointments_count || 0, icon: Calendar, color: '#0EA5E9' },
            { title: "Clienti Totali", value: stats?.total_clients || 0, icon: Users, color: '#789F8A' },
            { title: "Incasso Mensile", value: `\u20AC${(stats?.monthly_revenue || 0).toFixed(0)}`, icon: Euro, color: '#E9C46A', sub: `${stats?.monthly_appointments || 0} appuntamenti` },
            { title: "Prossimi 7 Giorni", value: stats?.upcoming_appointments?.length || 0, icon: TrendingUp, color: '#334155' },
          ].map((s, i) => (
            <Card key={i} className="bg-white border-[#E2E8F0]/30 hover:border-[#0EA5E9]/30 transition-all duration-300 hover:-translate-y-1 shadow-[0_2px_15px_-3px_rgba(0,0,0,0.07)]">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-[#334155] font-manrope">{s.title}</p>
                    <p className="text-3xl font-playfair font-medium text-[#0F172A] mt-2">{s.value}</p>
                    {s.sub && <p className="text-xs text-[#334155] mt-1 font-manrope">{s.sub}</p>}
                  </div>
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ backgroundColor: `${s.color}15` }}>
                    <s.icon className="w-6 h-6" style={{ color: s.color }} strokeWidth={1.5} />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Clickable Modules Grid */}
        <div>
          <h2 className="font-playfair text-xl text-[#0F172A] mb-4">Moduli</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {MODULES.map((mod) => (
              <Card
                key={mod.path}
                data-testid={`module-${mod.path.slice(1)}`}
                onClick={() => navigate(mod.path)}
                className="bg-white border-[#E2E8F0]/30 hover:border-opacity-100 transition-all duration-300 hover:-translate-y-1 hover:shadow-lg cursor-pointer group"
                style={{ borderColor: `${mod.color}20` }}
              >
                <CardContent className="p-4 text-center">
                  <div
                    className="w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-3 transition-transform group-hover:scale-110"
                    style={{ backgroundColor: `${mod.color}12` }}
                  >
                    <mod.icon className="w-6 h-6" style={{ color: mod.color }} strokeWidth={1.5} />
                  </div>
                  <p className="font-semibold text-[#0F172A] text-sm">{mod.label}</p>
                  <p className="text-[10px] text-[#334155] mt-0.5">{mod.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Today's Appointments + Upcoming */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <Card className="lg:col-span-8 bg-white border-[#E2E8F0]/30 shadow-[0_2px_15px_-3px_rgba(0,0,0,0.07)]">
            <CardHeader className="flex flex-row items-center justify-between pb-4">
              <CardTitle className="font-playfair text-xl text-[#0F172A]">Appuntamenti di Oggi</CardTitle>
              <Link to="/planning"><Button variant="ghost" size="sm" className="text-[#0EA5E9] hover:text-[#0284C7]">Vedi tutti <ChevronRight className="w-4 h-4 ml-1" /></Button></Link>
            </CardHeader>
            <CardContent>
              {stats?.today_appointments?.length > 0 ? (
                <div className="space-y-3">
                  {stats.today_appointments.map((apt) => (
                    <div key={apt.id} data-testid={`appointment-${apt.id}`} className="flex items-center gap-4 p-4 rounded-xl bg-[#F8FAFC] hover:bg-[#FAF5F2] transition-colors">
                      <div className="flex-shrink-0 w-16 text-center">
                        <p className="text-lg font-medium text-[#0EA5E9] font-manrope">{apt.time}</p>
                        <p className="text-xs text-[#334155]">{apt.end_time}</p>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-[#0F172A] truncate">{apt.client_name}</p>
                        <p className="text-sm text-[#334155] truncate">{apt.services.map(s => s.name).join(', ')}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-medium text-[#0F172A]">{'\u20AC'}{apt.total_price}</p>
                        <p className="text-xs text-[#334155]">{apt.total_duration} min</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Calendar className="w-12 h-12 mx-auto text-[#E2E8F0] mb-4" strokeWidth={1.5} />
                  <p className="text-[#334155] font-manrope">Nessun appuntamento per oggi</p>
                  <Link to="/appointments"><Button variant="outline" className="mt-4 border-[#0EA5E9] text-[#0EA5E9] hover:bg-[#FAF5F2]">Prenota un appuntamento</Button></Link>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="lg:col-span-4 space-y-6">
            <Card className="bg-white border-[#E2E8F0]/30 shadow-[0_2px_15px_-3px_rgba(0,0,0,0.07)]">
              <CardHeader className="pb-4">
                <CardTitle className="font-playfair text-xl text-[#0F172A]">Prossimi Appuntamenti</CardTitle>
              </CardHeader>
              <CardContent>
                {stats?.upcoming_appointments?.length > 0 ? (
                  <div className="space-y-3">
                    {stats.upcoming_appointments.slice(0, 5).map((apt) => (
                      <div key={apt.id} className="flex items-center gap-3 py-2">
                        <div className="w-2 h-2 rounded-full bg-[#0EA5E9]" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-[#0F172A] truncate">{apt.client_name}</p>
                          <p className="text-xs text-[#334155]">{format(new Date(apt.date), "EEE d MMM", { locale: it })} - {apt.time}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-[#334155] text-center py-4">Nessun appuntamento in programma</p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </Layout>
  );
}
