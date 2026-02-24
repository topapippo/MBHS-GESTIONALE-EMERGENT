import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Bell, MessageSquare, Clock, UserX, Check, Phone, Calendar } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function RemindersPage() {
  const [tomorrowReminders, setTomorrowReminders] = useState([]);
  const [inactiveClients, setInactiveClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sendingId, setSendingId] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [remRes, inactRes] = await Promise.all([
        axios.get(`${API}/reminders/tomorrow`),
        axios.get(`${API}/reminders/inactive-clients`)
      ]);
      setTomorrowReminders(remRes.data);
      setInactiveClients(inactRes.data);
    } catch (err) {
      console.error(err);
      toast.error('Errore nel caricamento');
    } finally {
      setLoading(false);
    }
  };

  const sendAppointmentReminder = async (apt) => {
    if (!apt.client_phone) {
      toast.error('Numero di telefono non disponibile');
      return;
    }
    setSendingId(apt.id);
    let phone = apt.client_phone.replace(/[\s\-\+]/g, '');
    if (!phone.startsWith('39')) phone = '39' + phone;

    const serviceNames = apt.services?.map(s => s.name).join(', ') || '';
    const message = encodeURIComponent(
      `Ciao ${apt.client_name}! Ti ricordiamo il tuo appuntamento domani alle ${apt.time} presso MBHS SALON. Servizi: ${serviceNames}. Ti aspettiamo!`
    );
    window.open(`https://wa.me/${phone}?text=${message}`, '_blank');

    try {
      await axios.post(`${API}/reminders/appointment/${apt.id}/mark-sent`);
      setTomorrowReminders(prev =>
        prev.map(r => r.id === apt.id ? { ...r, reminded: true } : r)
      );
      toast.success(`Promemoria inviato a ${apt.client_name}`);
    } catch (err) {
      console.error(err);
    }
    setSendingId(null);
  };

  const sendInactiveRecall = async (client) => {
    if (!client.client_phone) {
      toast.error('Numero di telefono non disponibile');
      return;
    }
    setSendingId(client.client_id);
    let phone = client.client_phone.replace(/[\s\-\+]/g, '');
    if (!phone.startsWith('39')) phone = '39' + phone;

    const message = encodeURIComponent(
      `Ciao ${client.client_name}! Sono passati ${client.days_ago} giorni dalla tua ultima visita presso MBHS SALON. Torna entro 7 giorni e avrai uno sconto del 10%! Prenota il tuo appuntamento!`
    );
    window.open(`https://wa.me/${phone}?text=${message}`, '_blank');

    try {
      await axios.post(`${API}/reminders/inactive/${client.client_id}/mark-sent`);
      setInactiveClients(prev =>
        prev.map(c => c.client_id === client.client_id ? { ...c, already_recalled: true } : c)
      );
      toast.success(`Richiamo inviato a ${client.client_name}`);
    } catch (err) {
      console.error(err);
    }
    setSendingId(null);
  };

  const pendingReminders = tomorrowReminders.filter(r => !r.reminded);
  const pendingRecalls = inactiveClients.filter(c => !c.already_recalled);

  if (loading) {
    return (
      <Layout>
        <div className="space-y-4">
          <Skeleton className="h-12 w-64" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6" data-testid="reminders-page">
        {/* Header */}
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-[#0F172A] flex items-center gap-3">
            <Bell className="w-7 h-7 text-[#0EA5E9]" />
            Promemoria & Richiami
          </h1>
          <p className="text-[#334155] mt-1">Invia promemoria appuntamenti e richiama clienti inattivi</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
            <CardContent className="p-5">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-[#0EA5E9] rounded-xl">
                  <Calendar className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-sm text-blue-700 font-semibold">Promemoria Domani</p>
                  <p className="text-3xl font-black text-[#0EA5E9]" data-testid="pending-reminders-count">
                    {pendingReminders.length}
                    <span className="text-sm font-semibold text-blue-600 ml-1">/ {tomorrowReminders.length}</span>
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
            <CardContent className="p-5">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-orange-500 rounded-xl">
                  <UserX className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-sm text-orange-700 font-semibold">Clienti Inattivi (60+ giorni)</p>
                  <p className="text-3xl font-black text-orange-600" data-testid="inactive-clients-count">
                    {pendingRecalls.length}
                    <span className="text-sm font-semibold text-orange-500 ml-1">/ {inactiveClients.length}</span>
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tomorrow's Appointments */}
        <Card className="border-[#E2E8F0]/30">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-bold text-[#0F172A] flex items-center gap-2">
              <Calendar className="w-5 h-5 text-[#0EA5E9]" />
              Appuntamenti di Domani
              {pendingReminders.length > 0 && (
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-semibold">
                  {pendingReminders.length} da inviare
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {tomorrowReminders.length > 0 ? (
              <div className="space-y-3">
                {tomorrowReminders.map((apt) => (
                  <div
                    key={apt.id}
                    className={`p-4 rounded-xl border-2 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 ${
                      apt.reminded ? 'border-green-200 bg-green-50' : 'border-[#E2E8F0] bg-white'
                    }`}
                    data-testid={`reminder-apt-${apt.id}`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="font-bold text-[#0F172A] truncate">{apt.client_name}</p>
                        {apt.reminded && (
                          <span className="text-xs bg-green-200 text-green-800 px-2 py-0.5 rounded-full font-semibold flex items-center gap-1">
                            <Check className="w-3 h-3" /> Inviato
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 text-sm text-[#334155] mt-1">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" /> {apt.time}
                        </span>
                        {apt.client_phone && (
                          <span className="flex items-center gap-1">
                            <Phone className="w-3.5 h-3.5" /> {apt.client_phone}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-[#64748B] mt-1">
                        {apt.services?.map(s => s.name).join(', ')}
                      </p>
                    </div>
                    {!apt.reminded && (
                      <Button
                        onClick={() => sendAppointmentReminder(apt)}
                        disabled={sendingId === apt.id || !apt.client_phone}
                        className="bg-green-500 hover:bg-green-600 text-white font-bold shrink-0"
                        data-testid={`send-reminder-${apt.id}`}
                      >
                        <MessageSquare className="w-4 h-4 mr-2" />
                        WhatsApp
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-[#334155]">
                <Calendar className="w-12 h-12 mx-auto text-[#E2E8F0] mb-3" strokeWidth={1.5} />
                <p className="font-semibold">Nessun appuntamento domani</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Inactive Clients */}
        <Card className="border-[#E2E8F0]/30">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-bold text-[#0F172A] flex items-center gap-2">
              <UserX className="w-5 h-5 text-orange-500" />
              Clienti Inattivi — Offri 10% di Sconto
              {pendingRecalls.length > 0 && (
                <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full font-semibold">
                  {pendingRecalls.length} da richiamare
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {inactiveClients.length > 0 ? (
              <div className="space-y-3">
                {inactiveClients.map((client) => (
                  <div
                    key={client.client_id}
                    className={`p-4 rounded-xl border-2 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 ${
                      client.already_recalled ? 'border-green-200 bg-green-50' : 'border-orange-200 bg-orange-50'
                    }`}
                    data-testid={`inactive-client-${client.client_id}`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="font-bold text-[#0F172A] truncate">{client.client_name}</p>
                        {client.already_recalled && (
                          <span className="text-xs bg-green-200 text-green-800 px-2 py-0.5 rounded-full font-semibold flex items-center gap-1">
                            <Check className="w-3 h-3" /> Richiamato
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 text-sm mt-1">
                        <span className="text-orange-700 font-semibold flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" /> {client.days_ago} giorni fa
                        </span>
                        {client.client_phone && (
                          <span className="text-[#334155] flex items-center gap-1">
                            <Phone className="w-3.5 h-3.5" /> {client.client_phone}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-[#64748B] mt-1">
                        Ultima visita: {client.last_visit} — {client.last_services?.join(', ')}
                      </p>
                    </div>
                    {!client.already_recalled && (
                      <Button
                        onClick={() => sendInactiveRecall(client)}
                        disabled={sendingId === client.client_id || !client.client_phone}
                        className="bg-orange-500 hover:bg-orange-600 text-white font-bold shrink-0"
                        data-testid={`send-recall-${client.client_id}`}
                      >
                        <MessageSquare className="w-4 h-4 mr-2" />
                        Richiama
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-[#334155]">
                <UserX className="w-12 h-12 mx-auto text-[#E2E8F0] mb-3" strokeWidth={1.5} />
                <p className="font-semibold">Nessun cliente inattivo da 60+ giorni</p>
                <p className="text-sm">Ottimo lavoro!</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
