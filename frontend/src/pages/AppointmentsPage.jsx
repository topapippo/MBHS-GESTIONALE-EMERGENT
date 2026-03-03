import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Calendar, Plus, Clock, Loader2, CheckCircle, XCircle, Trash2, MessageSquare, Send, UserCircle } from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { Calendar as CalendarComponent } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState([]);
  const [clients, setClients] = useState([]);
  const [services, setServices] = useState([]);
  const [operators, setOperators] = useState([]);
  const [smsStatus, setSmsStatus] = useState({ configured: false });
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [dialogOpen, setDialogOpen] = useState(false);
  const [smsDialogOpen, setSmsDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [appointmentToDelete, setAppointmentToDelete] = useState(null);
  const [appointmentForSms, setAppointmentForSms] = useState(null);
  const [saving, setSaving] = useState(false);
  const [sendingSms, setSendingSms] = useState(false);
  
  const [formData, setFormData] = useState({
    client_id: '',
    service_ids: [],
    operator_id: '',
    date: format(new Date(), 'yyyy-MM-dd'),
    time: '09:00',
    notes: ''
  });

  const [smsMessage, setSmsMessage] = useState('');
  const [cardAlerts, setCardAlerts] = useState({ expiring_cards: [], low_balance_cards: [], total_alerts: 0 });
  const [upcomingAppointments, setUpcomingAppointments] = useState([]);

  useEffect(() => {
    fetchData();
    checkSmsStatus();
    fetchAlerts();
  }, [selectedDate]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const dateStr = format(selectedDate, 'yyyy-MM-dd');
      const [appointmentsRes, clientsRes, servicesRes, operatorsRes] = await Promise.all([
        axios.get(`${API}/appointments?date=${dateStr}`),
        axios.get(`${API}/clients`),
        axios.get(`${API}/services`),
        axios.get(`${API}/operators`)
      ]);
      setAppointments(appointmentsRes.data);
      setClients(clientsRes.data);
      setServices(servicesRes.data);
      setOperators(operatorsRes.data.filter(op => op.active));
      
      // Fetch upcoming 7 days of appointments
      const upcoming = [];
      for (let i = 1; i <= 7; i++) {
        const d = new Date(selectedDate);
        d.setDate(d.getDate() + i);
        const ds = format(d, 'yyyy-MM-dd');
        try {
          const res = await axios.get(`${API}/appointments?date=${ds}`);
          if (res.data.length > 0) {
            upcoming.push({ date: ds, dateObj: d, appointments: res.data });
          }
        } catch (e) { /* skip */ }
      }
      setUpcomingAppointments(upcoming);
    } catch (err) {
      console.error('Error fetching data:', err);
      toast.error('Errore nel caricamento dei dati');
    } finally {
      setLoading(false);
    }
  };

  const fetchAlerts = async () => {
    try {
      const res = await axios.get(`${API}/cards/alerts/all?days=30&threshold_percent=20`);
      setCardAlerts(res.data);
    } catch (e) { /* alerts not critical */ }
  };

  const checkSmsStatus = async () => {
    try {
      const res = await axios.get(`${API}/sms/status`);
      setSmsStatus(res.data);
    } catch (err) {
      console.error('Error checking SMS status:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.client_id || formData.service_ids.length === 0) {
      toast.error('Seleziona un cliente e almeno un servizio');
      return;
    }
    
    setSaving(true);
    try {
      await axios.post(`${API}/appointments`, {
        ...formData,
        date: format(selectedDate, 'yyyy-MM-dd'),
        operator_id: formData.operator_id || null
      });
      toast.success('Appuntamento creato!');
      setDialogOpen(false);
      setFormData({ client_id: '', service_ids: [], operator_id: '', date: '', time: '09:00', notes: '' });
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore nella creazione');
    } finally {
      setSaving(false);
    }
  };

  const handleStatusChange = async (id, status) => {
    try {
      await axios.put(`${API}/appointments/${id}`, { status });
      toast.success(status === 'completed' ? 'Appuntamento completato!' : 'Appuntamento annullato');
      fetchData();
    } catch (err) {
      toast.error('Errore nell\'aggiornamento');
    }
  };

  const handleDelete = async () => {
    if (!appointmentToDelete) return;
    try {
      await axios.delete(`${API}/appointments/${appointmentToDelete}`);
      toast.success('Appuntamento eliminato');
      setDeleteDialogOpen(false);
      setAppointmentToDelete(null);
      fetchData();
    } catch (err) {
      toast.error('Errore nell\'eliminazione');
    }
  };

  const handleSendSms = async () => {
    if (!appointmentForSms) return;
    setSendingSms(true);
    try {
      const res = await axios.post(`${API}/sms/send-reminder`, {
        appointment_id: appointmentForSms.id,
        message: smsMessage || null
      });
      if (res.data.success) {
        toast.success('SMS inviato con successo!');
        setSmsDialogOpen(false);
        setAppointmentForSms(null);
        setSmsMessage('');
        fetchData();
      } else {
        toast.error(res.data.error || 'Errore nell\'invio SMS');
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore nell\'invio SMS');
    } finally {
      setSendingSms(false);
    }
  };

  const openSmsDialog = (apt) => {
    setAppointmentForSms(apt);
    const servicesText = apt.services.map(s => s.name).join(', ');
    setSmsMessage(`Promemoria: hai un appuntamento il ${apt.date} alle ${apt.time} per ${servicesText}. Ti aspettiamo!`);
    setSmsDialogOpen(true);
  };

  const toggleService = (serviceId) => {
    setFormData(prev => ({
      ...prev,
      service_ids: prev.service_ids.includes(serviceId)
        ? prev.service_ids.filter(id => id !== serviceId)
        : [...prev.service_ids, serviceId]
    }));
  };

  // Time slots from 8:00 to 20:00
  const timeSlots = Array.from({ length: 25 }, (_, i) => {
    const hour = Math.floor(i / 2) + 8;
    const minute = (i % 2) * 30;
    return `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
  });

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-[#789F8A]/10 border-[#789F8A] text-[#789F8A]';
      case 'cancelled': return 'bg-[#E76F51]/10 border-[#E76F51] text-[#E76F51]';
      default: return 'bg-[#0EA5E9]/10 border-[#0EA5E9] text-[#0EA5E9]';
    }
  };

  return (
    <Layout>
      <div className="space-y-6" data-testid="appointments-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="font-playfair text-3xl font-medium text-[#0F172A]">Agenda</h1>
            <p className="text-[#334155] mt-1 font-manrope">
              {format(selectedDate, "EEEE d MMMM yyyy", { locale: it })}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" className="border-[#E2E8F0] text-[#0F172A]">
                  <Calendar className="w-4 h-4 mr-2" />
                  Cambia Data
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="end">
                <CalendarComponent
                  mode="single"
                  selected={selectedDate}
                  onSelect={(date) => date && setSelectedDate(date)}
                  locale={it}
                />
              </PopoverContent>
            </Popover>

            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <Button 
                onClick={() => setDialogOpen(true)}
                data-testid="new-appointment-btn"
                className="bg-[#0EA5E9] hover:bg-[#0284C7] text-white shadow-lg shadow-[#0EA5E9]/20"
              >
                <Plus className="w-5 h-5 mr-2" />
                Nuovo
              </Button>
              <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                  <DialogTitle className="font-playfair text-2xl text-[#0F172A]">Nuovo Appuntamento</DialogTitle>
                  <DialogDescription>
                    {format(selectedDate, "EEEE d MMMM yyyy", { locale: it })}
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label>Cliente</Label>
                    <Select
                      value={formData.client_id}
                      onValueChange={(val) => setFormData({ ...formData, client_id: val })}
                    >
                      <SelectTrigger data-testid="select-client">
                        <SelectValue placeholder="Seleziona cliente" />
                      </SelectTrigger>
                      <SelectContent>
                        {clients.map((client) => (
                          <SelectItem key={client.id} value={client.id}>
                            {client.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Orario</Label>
                      <Select
                        value={formData.time}
                        onValueChange={(val) => setFormData({ ...formData, time: val })}
                      >
                        <SelectTrigger data-testid="select-time">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="max-h-[200px]">
                          {timeSlots.map((time) => (
                            <SelectItem key={time} value={time} data-testid={`time-option-${time.replace(':', '-')}`}>
                              {time}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>Operatore</Label>
                      <Select
                        value={formData.operator_id || "none"}
                        onValueChange={(val) => setFormData({ ...formData, operator_id: val === "none" ? "" : val })}
                      >
                        <SelectTrigger data-testid="select-operator">
                          <SelectValue placeholder="Seleziona..." />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">Non assegnato</SelectItem>
                          {operators.map((op) => (
                            <SelectItem key={op.id} value={op.id}>
                              <div className="flex items-center gap-2">
                                <div 
                                  className="w-3 h-3 rounded-full"
                                  style={{ backgroundColor: op.color }}
                                />
                                {op.name}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Servizi</Label>
                    <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
                      {services.map((service) => (
                        <Button
                          key={service.id}
                          type="button"
                          variant="outline"
                          data-testid={`service-${service.id}`}
                          className={`justify-start h-auto py-2 px-3 ${
                            formData.service_ids.includes(service.id)
                              ? 'bg-[#0EA5E9]/10 border-[#0EA5E9] text-[#0EA5E9]'
                              : 'border-[#E2E8F0]'
                          }`}
                          onClick={() => toggleService(service.id)}
                        >
                          <div className="text-left">
                            <p className="font-medium text-sm">{service.name}</p>
                            <p className="text-xs opacity-70">{service.duration} min - €{service.price}</p>
                          </div>
                        </Button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Note (opzionale)</Label>
                    <Input
                      value={formData.notes}
                      onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                      placeholder="Note aggiuntive..."
                      className="bg-[#F8FAFC]"
                    />
                  </div>

                  <DialogFooter>
                    <Button
                      type="submit"
                      disabled={saving}
                      data-testid="save-appointment-btn"
                      className="bg-[#0EA5E9] hover:bg-[#0284C7] text-white"
                    >
                      {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Salva Appuntamento'}
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Card Alerts / Scadenze */}
        {cardAlerts.total_alerts > 0 && (
          <Card className="bg-amber-50 border-amber-200 shadow-sm" data-testid="card-alerts-section">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center">
                  <Calendar className="w-4 h-4 text-amber-600" />
                </div>
                <h3 className="font-semibold text-amber-800">Scadenze Card ({cardAlerts.total_alerts})</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {cardAlerts.expiring_cards.map((card) => (
                  <div key={card.id} className="flex items-center justify-between p-2 bg-white rounded-lg border border-amber-100">
                    <div>
                      <p className="font-medium text-sm text-[#0F172A]">{card.client_name}</p>
                      <p className="text-xs text-amber-700">{card.name} — scade {card.expiry_date ? new Date(card.expiry_date).toLocaleDateString('it-IT') : 'presto'}</p>
                    </div>
                    <span className="text-xs bg-amber-100 text-amber-700 px-2 py-1 rounded-full font-semibold">
                      {card.days_until_expiry != null ? `${card.days_until_expiry}g` : '!'}
                    </span>
                  </div>
                ))}
                {cardAlerts.low_balance_cards.map((card) => (
                  <div key={card.id} className="flex items-center justify-between p-2 bg-white rounded-lg border border-red-100">
                    <div>
                      <p className="font-medium text-sm text-[#0F172A]">{card.client_name}</p>
                      <p className="text-xs text-red-600">{card.name} — credito basso: €{card.remaining_value?.toFixed(2)}</p>
                    </div>
                    <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full font-semibold">
                      {card.usage_percent != null ? `${Math.round(card.usage_percent)}%` : '!'}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Upcoming Appointments / Prossimi giorni */}
        {upcomingAppointments.length > 0 && (
          <Card className="bg-blue-50/50 border-blue-100 shadow-sm" data-testid="upcoming-section">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Clock className="w-4 h-4 text-blue-600" />
                </div>
                <h3 className="font-semibold text-blue-800">Prossimi Appuntamenti (7 giorni)</h3>
              </div>
              <div className="space-y-2">
                {upcomingAppointments.map((day) => (
                  <div key={day.date} className="p-2 bg-white rounded-lg border border-blue-100 cursor-pointer hover:bg-blue-50 transition-colors"
                    onClick={() => setSelectedDate(day.dateObj)}>
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-sm text-[#0F172A]">
                        {format(day.dateObj, "EEEE d MMMM", { locale: it })}
                      </p>
                      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full font-semibold">
                        {day.appointments.length} appuntament{day.appointments.length === 1 ? 'o' : 'i'}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {day.appointments.slice(0, 4).map((a) => (
                        <span key={a.id} className="text-xs text-[#334155] bg-gray-100 px-2 py-0.5 rounded">
                          {a.time} {a.client_name}
                        </span>
                      ))}
                      {day.appointments.length > 4 && (
                        <span className="text-xs text-[#334155]">+{day.appointments.length - 4} altri</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Appointments List */}
        <Card className="bg-white border-[#E2E8F0]/30 shadow-[0_2px_15px_-3px_rgba(0,0,0,0.07)]">
          <CardContent className="p-6">
            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-24 w-full" />
                ))}
              </div>
            ) : appointments.length > 0 ? (
              <div className="space-y-4">
                {appointments.map((apt) => (
                  <div
                    key={apt.id}
                    data-testid={`appointment-card-${apt.id}`}
                    className={`p-4 rounded-xl border-l-4 transition-all hover:shadow-md ${
                      getStatusColor(apt.status)
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex gap-4">
                        <div className="text-center min-w-[60px]">
                          <p className="text-lg font-semibold font-manrope">{apt.time}</p>
                          <p className="text-xs opacity-70">{apt.end_time}</p>
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-medium text-[#0F172A] text-lg">{apt.client_name}</h3>
                            {apt.operator_name && (
                              <span 
                                className="text-xs px-2 py-0.5 rounded-full text-white"
                                style={{ backgroundColor: apt.operator_color || '#334155' }}
                              >
                                {apt.operator_name}
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-[#334155] mt-1">
                            {apt.services.map(s => s.name).join(' + ')}
                          </p>
                          <div className="flex items-center gap-4 mt-2 text-sm text-[#334155]">
                            <span className="flex items-center gap-1">
                              <Clock className="w-4 h-4" /> {apt.total_duration} min
                            </span>
                            <span className="font-medium text-[#0F172A]">€{apt.total_price}</span>
                            {apt.sms_sent && (
                              <span className="text-[#789F8A] flex items-center gap-1">
                                <MessageSquare className="w-4 h-4" /> SMS inviato
                              </span>
                            )}
                          </div>
                          {apt.notes && (
                            <p className="text-sm text-[#334155] mt-2 italic">"{apt.notes}"</p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {apt.status === 'scheduled' && (
                          <>
                            {smsStatus.configured && apt.client_phone && !apt.sms_sent && (
                              <Button
                                size="icon"
                                variant="ghost"
                                onClick={() => openSmsDialog(apt)}
                                className="text-[#3498DB] hover:bg-[#3498DB]/10"
                                title="Invia SMS promemoria"
                              >
                                <Send className="w-5 h-5" />
                              </Button>
                            )}
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => handleStatusChange(apt.id, 'completed')}
                              className="text-[#789F8A] hover:bg-[#789F8A]/10"
                              title="Completa"
                            >
                              <CheckCircle className="w-5 h-5" />
                            </Button>
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => handleStatusChange(apt.id, 'cancelled')}
                              className="text-[#E76F51] hover:bg-[#E76F51]/10"
                              title="Annulla"
                            >
                              <XCircle className="w-5 h-5" />
                            </Button>
                          </>
                        )}
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => {
                            setAppointmentToDelete(apt.id);
                            setDeleteDialogOpen(true);
                          }}
                          className="text-[#334155] hover:text-[#E76F51] hover:bg-[#E76F51]/10"
                          title="Elimina"
                        >
                          <Trash2 className="w-5 h-5" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-16">
                <Calendar className="w-16 h-16 mx-auto text-[#E2E8F0] mb-4" strokeWidth={1.5} />
                <h3 className="font-playfair text-xl text-[#0F172A] mb-2">Nessun appuntamento</h3>
                <p className="text-[#334155] mb-4">Non ci sono appuntamenti per questa data</p>
                <Button
                  onClick={() => setDialogOpen(true)}
                  className="bg-[#0EA5E9] hover:bg-[#0284C7] text-white"
                >
                  <Plus className="w-4 h-4 mr-2" /> Aggiungi Appuntamento
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Delete Confirmation */}
        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Elimina Appuntamento</AlertDialogTitle>
              <AlertDialogDescription>
                Sei sicura di voler eliminare questo appuntamento? L'azione non può essere annullata.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Annulla</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleDelete}
                className="bg-[#E76F51] hover:bg-[#D55F41]"
              >
                Elimina
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {/* SMS Dialog */}
        <Dialog open={smsDialogOpen} onOpenChange={setSmsDialogOpen}>
          <DialogContent className="sm:max-w-[450px]">
            <DialogHeader>
              <DialogTitle className="font-playfair text-2xl text-[#0F172A]">Invia Promemoria SMS</DialogTitle>
              <DialogDescription>
                Invia un SMS al cliente per ricordargli l'appuntamento
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              {appointmentForSms && (
                <div className="p-3 bg-[#F8FAFC] rounded-lg">
                  <p className="font-medium text-[#0F172A]">{appointmentForSms.client_name}</p>
                  <p className="text-sm text-[#334155]">{appointmentForSms.client_phone}</p>
                </div>
              )}
              <div className="space-y-2">
                <Label>Messaggio</Label>
                <textarea
                  value={smsMessage}
                  onChange={(e) => setSmsMessage(e.target.value)}
                  className="w-full min-h-[100px] p-3 rounded-lg bg-[#F8FAFC] border-transparent focus:border-[#0EA5E9] focus:ring-1 focus:ring-[#0EA5E9] resize-none"
                  placeholder="Scrivi il messaggio..."
                />
              </div>
              <DialogFooter>
                <Button
                  onClick={handleSendSms}
                  disabled={sendingSms}
                  className="bg-[#0EA5E9] hover:bg-[#0284C7] text-white"
                >
                  {sendingSms ? (
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  ) : (
                    <Send className="w-4 h-4 mr-2" />
                  )}
                  Invia SMS
                </Button>
              </DialogFooter>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
