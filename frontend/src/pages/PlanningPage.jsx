import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
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
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { ChevronLeft, ChevronRight, Plus, Clock, Loader2, Search, X, Repeat, Check } from 'lucide-react';
import { format, addDays, subDays } from 'date-fns';
import { it } from 'date-fns/locale';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Time slots from 08:00 to 20:00 every 15 minutes
const generateTimeSlots = () => {
  const slots = [];
  for (let hour = 8; hour <= 20; hour++) {
    for (let min = 0; min < 60; min += 15) {
      if (hour === 20 && min > 0) break;
      slots.push(`${hour.toString().padStart(2, '0')}:${min.toString().padStart(2, '0')}`);
    }
  }
  return slots;
};

const TIME_SLOTS = generateTimeSlots();

export default function PlanningPage() {
  const [appointments, setAppointments] = useState([]);
  const [operators, setOperators] = useState([]);
  const [clients, setClients] = useState([]);
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [dialogOpen, setDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [selectedOperator, setSelectedOperator] = useState(null);
  const scrollRef = useRef(null);

  const [formData, setFormData] = useState({
    client_id: '',
    service_ids: [],
    operator_id: '',
    time: '09:00',
    notes: ''
  });

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState({ clients: [], appointments: [] });
  const [searchOpen, setSearchOpen] = useState(false);
  const [searching, setSearching] = useState(false);
  const [highlightedClientId, setHighlightedClientId] = useState(null);

  // Recurring appointment state
  const [recurringDialogOpen, setRecurringDialogOpen] = useState(false);
  const [selectedAppointment, setSelectedAppointment] = useState(null);
  const [recurringData, setRecurringData] = useState({ repeat_weeks: 3, repeat_count: 4 });
  const [creatingRecurring, setCreatingRecurring] = useState(false);

  useEffect(() => {
    fetchData();
  }, [selectedDate]);

  useEffect(() => {
    // Scroll to 8:00 on load
    if (scrollRef.current) {
      const currentHour = new Date().getHours();
      const targetHour = currentHour >= 8 && currentHour <= 20 ? currentHour : 9;
      const slotIndex = (targetHour - 8) * 4;
      const scrollPosition = slotIndex * 48; // 48px per slot
      scrollRef.current.scrollTop = scrollPosition;
    }
  }, [loading]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const dateStr = format(selectedDate, 'yyyy-MM-dd');
      const [appointmentsRes, operatorsRes, clientsRes, servicesRes] = await Promise.all([
        axios.get(`${API}/appointments?date=${dateStr}`),
        axios.get(`${API}/operators`),
        axios.get(`${API}/clients`),
        axios.get(`${API}/services`)
      ]);
      setAppointments(appointmentsRes.data);
      setOperators(operatorsRes.data.filter(op => op.active));
      setClients(clientsRes.data);
      setServices(servicesRes.data);
    } catch (err) {
      console.error('Error fetching data:', err);
      toast.error('Errore nel caricamento dei dati');
    } finally {
      setLoading(false);
    }
  };

  const handleSlotClick = (time, operatorId) => {
    setSelectedSlot(time);
    setSelectedOperator(operatorId);
    setFormData({
      ...formData,
      time: time,
      operator_id: operatorId || ''
    });
    setDialogOpen(true);
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
      setFormData({ client_id: '', service_ids: [], operator_id: '', time: '09:00', notes: '' });
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore nella creazione');
    } finally {
      setSaving(false);
    }
  };

  const toggleService = (serviceId) => {
    setFormData(prev => ({
      ...prev,
      service_ids: prev.service_ids.includes(serviceId)
        ? prev.service_ids.filter(id => id !== serviceId)
        : [...prev.service_ids, serviceId]
    }));
  };

  // Search handler
  const handleSearch = async (query) => {
    setSearchQuery(query);
    if (query.length < 2) {
      setSearchResults({ clients: [], appointments: [] });
      return;
    }
    
    setSearching(true);
    try {
      const res = await axios.get(`${API}/clients/search/appointments?query=${encodeURIComponent(query)}`);
      setSearchResults(res.data);
    } catch (err) {
      console.error('Search error:', err);
    } finally {
      setSearching(false);
    }
  };

  const highlightClient = (clientId) => {
    setHighlightedClientId(clientId);
    setSearchOpen(false);
    setSearchQuery('');
    setSearchResults({ clients: [], appointments: [] });
    
    // Auto-clear highlight after 5 seconds
    setTimeout(() => setHighlightedClientId(null), 5000);
  };

  const clearHighlight = () => {
    setHighlightedClientId(null);
  };

  // Recurring appointments handler
  const openRecurringDialog = (apt) => {
    setSelectedAppointment(apt);
    setRecurringData({ repeat_weeks: 3, repeat_count: 4 });
    setRecurringDialogOpen(true);
  };

  const handleCreateRecurring = async () => {
    if (!selectedAppointment) return;
    
    setCreatingRecurring(true);
    try {
      const res = await axios.post(`${API}/appointments/recurring`, {
        appointment_id: selectedAppointment.id,
        repeat_weeks: recurringData.repeat_weeks,
        repeat_count: recurringData.repeat_count
      });
      toast.success(`Creati ${res.data.created} appuntamenti ricorrenti!`);
      setRecurringDialogOpen(false);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore nella creazione');
    } finally {
      setCreatingRecurring(false);
    }
  };

  // Calculate appointment position and height
  const getAppointmentStyle = (apt) => {
    const [startHour, startMin] = apt.time.split(':').map(Number);
    const startSlotIndex = (startHour - 8) * 4 + Math.floor(startMin / 15);
    const slotsCount = Math.ceil(apt.total_duration / 15);
    
    return {
      top: `${startSlotIndex * 48}px`,
      height: `${slotsCount * 48 - 4}px`,
    };
  };

  // Get appointments for a specific operator
  const getOperatorAppointments = (operatorId) => {
    if (operatorId === null) {
      return appointments.filter(apt => !apt.operator_id);
    }
    return appointments.filter(apt => apt.operator_id === operatorId);
  };

  // Check if slot is occupied
  const isSlotOccupied = (time, operatorId) => {
    const [slotHour, slotMin] = time.split(':').map(Number);
    const slotMinutes = slotHour * 60 + slotMin;
    
    const operatorApts = getOperatorAppointments(operatorId);
    
    return operatorApts.some(apt => {
      const [aptHour, aptMin] = apt.time.split(':').map(Number);
      const aptStart = aptHour * 60 + aptMin;
      const aptEnd = aptStart + apt.total_duration;
      return slotMinutes >= aptStart && slotMinutes < aptEnd;
    });
  };

  // Create columns: one for unassigned + one per operator
  const columns = [
    { id: null, name: 'Non assegnato', color: '#78716C' },
    ...operators.map(op => ({ id: op.id, name: op.name, color: op.color }))
  ];

  return (
    <Layout>
      <div className="space-y-4" data-testid="planning-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="font-playfair text-3xl font-medium text-[#44403C]">Planning</h1>
            <p className="text-[#78716C] mt-1 font-manrope">
              {format(selectedDate, "EEEE d MMMM yyyy", { locale: it })}
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {/* Search Bar */}
            <div className="relative">
              <div className="flex items-center">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[#78716C]" />
                  <Input
                    placeholder="Cerca cliente..."
                    value={searchQuery}
                    onChange={(e) => handleSearch(e.target.value)}
                    onFocus={() => setSearchOpen(true)}
                    className="pl-9 w-48 md:w-56 bg-white border-[#E6CCB2] focus:border-[#C58970]"
                    data-testid="search-client-input"
                  />
                  {searchQuery && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6"
                      onClick={() => {
                        setSearchQuery('');
                        setSearchResults({ clients: [], appointments: [] });
                      }}
                    >
                      <X className="w-3 h-3" />
                    </Button>
                  )}
                </div>
              </div>
              
              {/* Search Results Dropdown */}
              {searchOpen && searchQuery.length >= 2 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-[#E6CCB2] rounded-lg shadow-lg z-50 max-h-80 overflow-auto">
                  {searching ? (
                    <div className="p-4 text-center">
                      <Loader2 className="w-5 h-5 animate-spin mx-auto text-[#C58970]" />
                    </div>
                  ) : searchResults.clients.length === 0 ? (
                    <div className="p-4 text-center text-[#78716C] text-sm">
                      Nessun cliente trovato
                    </div>
                  ) : (
                    <div className="py-2">
                      {searchResults.clients.map((client) => {
                        const clientApts = searchResults.appointments.filter(a => a.client_id === client.id);
                        return (
                          <div key={client.id} className="border-b border-[#E6CCB2]/30 last:border-0">
                            <button
                              className="w-full px-4 py-2 text-left hover:bg-[#FAFAF9] flex items-center justify-between"
                              onClick={() => highlightClient(client.id)}
                              data-testid={`search-result-${client.id}`}
                            >
                              <div>
                                <p className="font-medium text-[#44403C]">{client.name}</p>
                                <p className="text-xs text-[#78716C]">{client.phone}</p>
                              </div>
                              <span className="text-xs bg-[#C58970]/10 text-[#C58970] px-2 py-1 rounded">
                                {clientApts.length} app.
                              </span>
                            </button>
                            {clientApts.slice(0, 3).map((apt) => (
                              <div
                                key={apt.id}
                                className="px-4 py-1 pl-8 text-xs text-[#78716C] bg-[#FAFAF9]/50"
                              >
                                {apt.date} {apt.time} - {apt.services?.map(s => s.name).join(', ')}
                              </div>
                            ))}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Highlighted client indicator */}
            {highlightedClientId && (
              <div className="flex items-center gap-2 bg-[#C58970]/10 px-3 py-1.5 rounded-lg">
                <span className="text-sm text-[#C58970] font-medium">
                  Filtro attivo
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-5 w-5"
                  onClick={clearHighlight}
                >
                  <X className="w-3 h-3 text-[#C58970]" />
                </Button>
              </div>
            )}

            {/* Date Navigation */}
            <Button
              variant="outline"
              size="icon"
              onClick={() => setSelectedDate(subDays(selectedDate, 1))}
              className="border-[#E6CCB2]"
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              onClick={() => setSelectedDate(new Date())}
              className="border-[#E6CCB2] text-[#44403C]"
            >
              Oggi
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={() => setSelectedDate(addDays(selectedDate, 1))}
              className="border-[#E6CCB2]"
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Planning Grid */}
        {loading ? (
          <Skeleton className="h-[600px] w-full" />
        ) : (
          <Card className="bg-white border-[#E6CCB2]/30 shadow-[0_2px_15px_-3px_rgba(0,0,0,0.07)] overflow-hidden">
            <CardContent className="p-0">
              {/* Header with operator names */}
              <div className="flex border-b border-[#E6CCB2]/30 bg-[#FAFAF9] sticky top-0 z-10">
                <div className="w-16 flex-shrink-0 p-2 border-r border-[#E6CCB2]/30">
                  <Clock className="w-5 h-5 text-[#78716C] mx-auto" />
                </div>
                {columns.map((col) => (
                  <div
                    key={col.id || 'unassigned'}
                    className="flex-1 min-w-[150px] p-3 border-r border-[#E6CCB2]/30 last:border-r-0"
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full flex-shrink-0"
                        style={{ backgroundColor: col.color }}
                      />
                      <span className="font-medium text-[#44403C] text-sm truncate">
                        {col.name}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Time slots grid */}
              <div 
                ref={scrollRef}
                className="overflow-auto"
                style={{ maxHeight: 'calc(100vh - 280px)' }}
              >
                <div className="flex relative">
                  {/* Time column */}
                  <div className="w-16 flex-shrink-0 bg-[#FAFAF9]">
                    {TIME_SLOTS.map((time, idx) => (
                      <div
                        key={time}
                        className={`h-12 flex items-center justify-center text-xs text-[#78716C] border-b border-[#E6CCB2]/20 ${
                          time.endsWith(':00') ? 'font-medium' : 'text-[10px]'
                        }`}
                      >
                        {time.endsWith(':00') || time.endsWith(':30') ? time : ''}
                      </div>
                    ))}
                  </div>

                  {/* Operator columns */}
                  {columns.map((col) => {
                    const colAppointments = getOperatorAppointments(col.id);
                    
                    return (
                      <div
                        key={col.id || 'unassigned'}
                        className="flex-1 min-w-[150px] relative border-r border-[#E6CCB2]/20 last:border-r-0"
                      >
                        {/* Time slot backgrounds */}
                        {TIME_SLOTS.map((time) => (
                          <div
                            key={time}
                            onClick={() => !isSlotOccupied(time, col.id) && handleSlotClick(time, col.id)}
                            className={`h-12 border-b border-[#E6CCB2]/20 transition-colors ${
                              time.endsWith(':00') ? 'bg-white' : 'bg-[#FAFAF9]/50'
                            } ${
                              !isSlotOccupied(time, col.id) 
                                ? 'hover:bg-[#C58970]/10 cursor-pointer' 
                                : ''
                            }`}
                          />
                        ))}

                        {/* Appointments overlay */}
                        {colAppointments.map((apt) => {
                          const style = getAppointmentStyle(apt);
                          const isHighlighted = highlightedClientId && apt.client_id === highlightedClientId;
                          return (
                            <div
                              key={apt.id}
                              data-testid={`planning-apt-${apt.id}`}
                              className={`absolute left-1 right-1 rounded-lg p-2 text-white text-xs overflow-hidden shadow-md cursor-pointer hover:opacity-90 transition-all ${
                                isHighlighted ? 'ring-4 ring-yellow-400 ring-offset-2 z-20' : ''
                              }`}
                              style={{
                                ...style,
                                backgroundColor: apt.operator_color || col.color,
                              }}
                              title={`${apt.client_name} - ${apt.services.map(s => s.name).join(', ')}`}
                            >
                              <div className="flex justify-between items-start">
                                <div className="flex-1 min-w-0">
                                  <p className="font-semibold truncate">{apt.client_name}</p>
                                  <p className="text-white/80 truncate text-[10px]">
                                    {apt.time} - {apt.end_time}
                                  </p>
                                  <p className="text-white/70 truncate text-[10px]">
                                    {apt.services.map(s => s.name).join(', ')}
                                  </p>
                                </div>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    openRecurringDialog(apt);
                                  }}
                                  className="ml-1 p-1 rounded hover:bg-white/20 transition-colors flex-shrink-0"
                                  title="Ripeti appuntamento"
                                  data-testid={`repeat-btn-${apt.id}`}
                                >
                                  <Repeat className="w-3 h-3" />
                                </button>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    );
                  })}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* New Appointment Dialog */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle className="font-playfair text-2xl text-[#44403C]">
                Nuovo Appuntamento
              </DialogTitle>
              <DialogDescription>
                {format(selectedDate, "EEEE d MMMM yyyy", { locale: it })} alle {formData.time}
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label>Cliente</Label>
                <Select
                  value={formData.client_id}
                  onValueChange={(val) => setFormData({ ...formData, client_id: val })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleziona cliente" />
                  </SelectTrigger>
                  <SelectContent className="max-h-[200px]">
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
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="max-h-[200px]">
                      {TIME_SLOTS.map((time) => (
                        <SelectItem key={time} value={time}>
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
                    <SelectTrigger>
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
                <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto">
                  {services.map((service) => (
                    <Button
                      key={service.id}
                      type="button"
                      variant="outline"
                      className={`justify-start h-auto py-2 px-3 ${
                        formData.service_ids.includes(service.id)
                          ? 'bg-[#C58970]/10 border-[#C58970] text-[#C58970]'
                          : 'border-[#E6CCB2]'
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
                  className="bg-[#FAFAF9]"
                />
              </div>

              <DialogFooter>
                <Button
                  type="submit"
                  disabled={saving}
                  className="bg-[#C58970] hover:bg-[#B07860] text-white"
                >
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Salva Appuntamento'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
