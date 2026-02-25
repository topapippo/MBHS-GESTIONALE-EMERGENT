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
import { ChevronLeft, ChevronRight, Plus, Clock, Loader2, Search, X, Repeat, Check, Trash2, Edit3, User, CreditCard, Banknote, Percent, Euro, CheckCircle, Star, MessageSquare, Bell } from 'lucide-react';
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

  // Client search in dialog
  const [clientSearch, setClientSearch] = useState('');
  const [showClientDropdown, setShowClientDropdown] = useState(false);

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

  // Edit/Delete appointment state
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingAppointment, setEditingAppointment] = useState(null);
  const [deleting, setDeleting] = useState(false);

  // Selected client info
  const [selectedClientInfo, setSelectedClientInfo] = useState(null);

  // Payment/Checkout state
  const [checkoutMode, setCheckoutMode] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [discountType, setDiscountType] = useState('none');
  const [discountValue, setDiscountValue] = useState('');
  const [processing, setProcessing] = useState(false);

  // Loyalty WhatsApp notification
  const [loyaltyAlertOpen, setLoyaltyAlertOpen] = useState(false);
  const [loyaltyAlertData, setLoyaltyAlertData] = useState(null);

  // Reminder notifications
  const [pendingRemindersCount, setPendingRemindersCount] = useState(0);
  const [inactiveClientsCount, setInactiveClientsCount] = useState(0);

  // Drag & Drop state
  const [draggedApt, setDraggedApt] = useState(null);
  const [dragOverSlot, setDragOverSlot] = useState(null);

  useEffect(() => {
    fetchData();
    fetchReminderCounts();
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

  const fetchReminderCounts = async () => {
    try {
      const [remRes, inactRes] = await Promise.all([
        axios.get(`${API}/reminders/tomorrow`),
        axios.get(`${API}/reminders/inactive-clients`)
      ]);
      setPendingRemindersCount(remRes.data.filter(r => !r.reminded).length);
      setInactiveClientsCount(inactRes.data.filter(c => !c.already_recalled).length);
    } catch (err) {
      // silent fail - not critical
    }
  };

  const handleSlotClick = (time, operatorId) => {
    setSelectedSlot(time);
    setSelectedOperator(operatorId);
    setClientSearch('');
    setShowClientDropdown(false);
    setFormData({
      ...formData,
      client_id: '',
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

  // Get client info when selected
  const handleClientSelect = (clientId, clientName) => {
    setFormData({ ...formData, client_id: clientId });
    setClientSearch(clientName);
    setShowClientDropdown(false);
    
    // Find client info
    const client = clients.find(c => c.id === clientId);
    setSelectedClientInfo(client);
  };

  // Open edit dialog for appointment
  const openEditDialog = (apt) => {
    setEditingAppointment(apt);
    setFormData({
      client_id: apt.client_id,
      service_ids: apt.services.map(s => s.id),
      operator_id: apt.operator_id || '',
      time: apt.time,
      notes: apt.notes || ''
    });
    setClientSearch(apt.client_name);
    const client = clients.find(c => c.id === apt.client_id);
    setSelectedClientInfo(client);
    setEditDialogOpen(true);
  };

  // Update appointment
  const handleUpdateAppointment = async (e) => {
    e.preventDefault();
    if (!editingAppointment) return;
    
    setSaving(true);
    try {
      await axios.put(`${API}/appointments/${editingAppointment.id}`, {
        ...formData,
        date: format(selectedDate, 'yyyy-MM-dd')
      });
      toast.success('Appuntamento aggiornato!');
      setEditDialogOpen(false);
      setEditingAppointment(null);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore nell\'aggiornamento');
    } finally {
      setSaving(false);
    }
  };

  // Delete appointment
  const handleDeleteAppointment = async () => {
    if (!editingAppointment) return;
    if (!window.confirm('Sei sicuro di voler eliminare questo appuntamento?')) return;
    
    setDeleting(true);
    try {
      await axios.delete(`${API}/appointments/${editingAppointment.id}`);
      toast.success('Appuntamento eliminato!');
      setEditDialogOpen(false);
      setEditingAppointment(null);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore nell\'eliminazione');
    } finally {
      setDeleting(false);
    }
  };

  // Calculate total for appointment
  const calculateTotal = () => {
    if (!editingAppointment) return 0;
    const servicesTotal = editingAppointment.services.reduce((sum, s) => sum + (s.price || 0), 0);
    return servicesTotal;
  };

  // Calculate discount
  const calculateDiscount = () => {
    const total = calculateTotal();
    if (discountType === 'none' || !discountValue) return 0;
    
    const value = parseFloat(discountValue) || 0;
    if (discountType === 'percent') {
      return (total * value) / 100;
    }
    return value; // fixed amount
  };

  // Calculate final amount
  const calculateFinalAmount = () => {
    return Math.max(0, calculateTotal() - calculateDiscount());
  };

  // Process payment
  const handleCheckout = async () => {
    if (!editingAppointment) return;
    
    setProcessing(true);
    try {
      const res = await axios.post(`${API}/appointments/${editingAppointment.id}/checkout`, {
        payment_method: paymentMethod,
        discount_type: discountType,
        discount_value: discountType !== 'none' ? parseFloat(discountValue) || 0 : 0,
        total_paid: calculateFinalAmount()
      });
      const pointsEarned = res.data.loyalty_points_earned || 0;
      const msg = pointsEarned > 0
        ? `Pagamento registrato! +${pointsEarned} punti fedeltà`
        : 'Pagamento registrato con successo!';
      toast.success(msg);
      setEditDialogOpen(false);
      setEditingAppointment(null);
      setCheckoutMode(false);
      resetCheckout();
      fetchData();

      // Check if loyalty threshold reached → show WhatsApp popup
      if (res.data.loyalty_threshold_reached) {
        setLoyaltyAlertData({
          clientName: res.data.client_name,
          clientPhone: res.data.client_phone,
          threshold: res.data.loyalty_threshold_reached,
          totalPoints: res.data.loyalty_total_points
        });
        setLoyaltyAlertOpen(true);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore nel pagamento');
    } finally {
      setProcessing(false);
    }
  };

  const openLoyaltyWhatsApp = () => {
    if (!loyaltyAlertData?.clientPhone) {
      toast.error('Numero di telefono non disponibile');
      return;
    }
    let phone = loyaltyAlertData.clientPhone.replace(/[\s\-\+]/g, '');
    if (!phone.startsWith('39')) phone = '39' + phone;
    const message = encodeURIComponent(
      `Ciao, hai raggiunto ${loyaltyAlertData.totalPoints} punti fedeltà presso MBHS SALON! Hai diritto ad un taglio gratis o uno sconto di 10,00 euro sui servizi di colpi di sole e schiariture. Prenota il tuo prossimo appuntamento!`
    );
    window.open(`https://wa.me/${phone}?text=${message}`, '_blank');
    setLoyaltyAlertOpen(false);
  };

  // Reset checkout state
  const resetCheckout = () => {
    setCheckoutMode(false);
    setPaymentMethod('cash');
    setDiscountType('none');
    setDiscountValue('');
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

  const getAppointmentStyle = (apt) => {
  };

  // Calculate appointment position and height
  // Drag & Drop handlers
  const handleDragStart = (e, apt) => {
    setDraggedApt(apt);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', apt.id);
    e.currentTarget.style.opacity = '0.5';
  };

  const handleDragEnd = (e) => {
    e.currentTarget.style.opacity = '1';
    setDraggedApt(null);
    setDragOverSlot(null);
  };

  const handleDragOver = (e, time, colId) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverSlot(`${time}-${colId}`);
  };

  const handleDragLeave = () => {
    setDragOverSlot(null);
  };

  const handleDrop = async (e, time, colId) => {
    e.preventDefault();
    setDragOverSlot(null);
    if (!draggedApt) return;
    if (draggedApt.time === time && draggedApt.operator_id === colId) return;
    
    try {
      const updateData = { time };
      if (colId !== draggedApt.operator_id) {
        updateData.operator_id = colId || '';
      }
      await axios.put(`${API}/appointments/${draggedApt.id}`, updateData);
      toast.success(`Spostato a ${time}`);
      fetchData();
    } catch (err) {
      toast.error('Errore nello spostamento');
    }
    setDraggedApt(null);
  };

  // Sort services by sort_order for consistent category ordering
  const CATEGORY_ORDER = ['taglio', 'piega', 'trattamento', 'colore', 'modellanti', 'abbonamenti', 'prodotti'];
  const sortedServices = [...services].sort((a, b) => {
    const catA = CATEGORY_ORDER.indexOf(a.category);
    const catB = CATEGORY_ORDER.indexOf(b.category);
    if (catA !== catB) return (catA === -1 ? 99 : catA) - (catB === -1 ? 99 : catB);
    return (a.sort_order || 999) - (b.sort_order || 999);
  });
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
    { id: null, name: 'Non assegnato', color: '#334155' },
    ...operators.map(op => ({ id: op.id, name: op.name, color: op.color }))
  ];

  return (
    <Layout>
      <div className="space-y-4" data-testid="planning-page">
        {/* Reminder Banner */}
        {(pendingRemindersCount > 0 || inactiveClientsCount > 0) && (
          <a
            href="/reminders"
            className="flex items-center gap-3 p-3 bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-xl hover:shadow-md transition-shadow"
            data-testid="reminder-banner"
          >
            <Bell className="w-5 h-5 text-amber-500 shrink-0" />
            <div className="flex-1 text-sm">
              {pendingRemindersCount > 0 && (
                <span className="font-bold text-[#0F172A]">{pendingRemindersCount} promemoria domani</span>
              )}
              {pendingRemindersCount > 0 && inactiveClientsCount > 0 && <span className="text-[#334155]"> · </span>}
              {inactiveClientsCount > 0 && (
                <span className="font-bold text-orange-600">{inactiveClientsCount} clienti inattivi</span>
              )}
            </div>
            <span className="text-xs text-[#0EA5E9] font-bold shrink-0">Gestisci →</span>
          </a>
        )}

        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-4xl font-black text-black">Planning</h1>
            <p className="text-[#0EA5E9] mt-1 font-bold text-lg">
              {format(selectedDate, "EEEE d MMMM yyyy", { locale: it })}
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {/* Search Bar */}
            <div className="relative">
              <div className="flex items-center">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[#0EA5E9]" />
                  <Input
                    placeholder="Cerca cliente..."
                    value={searchQuery}
                    onChange={(e) => handleSearch(e.target.value)}
                    onFocus={() => setSearchOpen(true)}
                    className="pl-9 w-48 md:w-56 bg-white border-2 border-[#0EA5E9]/50 focus:border-[#0EA5E9] font-medium"
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
                <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-[#E2E8F0] rounded-lg shadow-lg z-50 max-h-80 overflow-auto">
                  {searching ? (
                    <div className="p-4 text-center">
                      <Loader2 className="w-5 h-5 animate-spin mx-auto text-[#0EA5E9]" />
                    </div>
                  ) : searchResults.clients.length === 0 ? (
                    <div className="p-4 text-center text-[#334155] text-sm">
                      Nessun cliente trovato
                    </div>
                  ) : (
                    <div className="py-2">
                      {searchResults.clients.map((client) => {
                        const clientApts = searchResults.appointments.filter(a => a.client_id === client.id);
                        return (
                          <div key={client.id} className="border-b border-[#E2E8F0]/30 last:border-0">
                            <button
                              className="w-full px-4 py-2 text-left hover:bg-[#F8FAFC] flex items-center justify-between"
                              onClick={() => highlightClient(client.id)}
                              data-testid={`search-result-${client.id}`}
                            >
                              <div>
                                <p className="font-medium text-[#0F172A]">{client.name}</p>
                                <p className="text-xs text-[#334155]">{client.phone}</p>
                              </div>
                              <span className="text-xs bg-[#0EA5E9]/10 text-[#0EA5E9] px-2 py-1 rounded">
                                {clientApts.length} app.
                              </span>
                            </button>
                            {clientApts.slice(0, 3).map((apt) => (
                              <div
                                key={apt.id}
                                className="px-4 py-1 pl-8 text-xs text-[#334155] bg-[#F8FAFC]/50"
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
              <div className="flex items-center gap-2 bg-[#0EA5E9]/10 px-3 py-1.5 rounded-lg">
                <span className="text-sm text-[#0EA5E9] font-medium">
                  Filtro attivo
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-5 w-5"
                  onClick={clearHighlight}
                >
                  <X className="w-3 h-3 text-[#0EA5E9]" />
                </Button>
              </div>
            )}

            {/* Date Navigation */}
            <Button
              variant="outline"
              size="icon"
              onClick={() => setSelectedDate(subDays(selectedDate, 1))}
              className="border-[#E2E8F0]"
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              onClick={() => setSelectedDate(new Date())}
              className="border-[#E2E8F0] text-[#0F172A]"
            >
              Oggi
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={() => setSelectedDate(addDays(selectedDate, 1))}
              className="border-[#E2E8F0]"
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Planning Grid */}
        {loading ? (
          <Skeleton className="h-[600px] w-full" />
        ) : (
          <Card className="bg-white border-[#E2E8F0]/30 shadow-[0_2px_15px_-3px_rgba(0,0,0,0.07)] overflow-hidden">
            <CardContent className="p-0">
              {/* Header with operator names */}
              <div className="flex border-b-2 border-[#0EA5E9]/40 bg-gradient-to-r from-[#0EA5E9]/10 to-[#E2E8F0]/20 sticky top-0 z-10">
                <div className="w-16 flex-shrink-0 p-2 border-r-2 border-[#0EA5E9]/30">
                  <Clock className="w-5 h-5 text-[#0EA5E9] mx-auto" />
                </div>
                {columns.map((col) => (
                  <div
                    key={col.id || 'unassigned'}
                    className="flex-1 min-w-[150px] p-3 border-r-2 border-[#0EA5E9]/30 last:border-r-0"
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className="w-4 h-4 rounded-full flex-shrink-0 shadow-sm"
                        style={{ backgroundColor: col.color }}
                      />
                      <span className="font-bold text-[#0F172A] text-sm truncate">
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
                  <div className="w-16 flex-shrink-0 bg-gradient-to-b from-[#F8FAFC] to-white">
                    {TIME_SLOTS.map((time, idx) => (
                      <div
                        key={time}
                        className={`h-12 flex items-center justify-center border-b border-[#E2E8F0]/30 ${
                          time.endsWith(':00') ? 'font-bold text-sm text-[#0F172A] bg-[#E2E8F0]/20' : 'text-xs text-[#334155]'
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
                        className="flex-1 min-w-[150px] relative border-r border-[#E2E8F0]/20 last:border-r-0"
                      >
                        {/* Time slot backgrounds */}
                        {TIME_SLOTS.map((time) => (
                          <div
                            key={time}
                            onClick={() => !isSlotOccupied(time, col.id) && handleSlotClick(time, col.id)}
                            onDragOver={(e) => handleDragOver(e, time, col.id)}
                            onDragLeave={handleDragLeave}
                            onDrop={(e) => handleDrop(e, time, col.id)}
                            className={`h-12 border-b border-[#E2E8F0]/20 transition-colors ${
                              time.endsWith(':00') ? 'bg-white' : 'bg-[#F8FAFC]/50'
                            } ${
                              dragOverSlot === `${time}-${col.id}` ? 'bg-[#0EA5E9]/30 ring-2 ring-[#0EA5E9] ring-inset' : ''
                            } ${
                              !isSlotOccupied(time, col.id) 
                                ? 'hover:bg-[#0EA5E9]/20 cursor-pointer' 
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
                              draggable="true"
                              onDragStart={(e) => handleDragStart(e, apt)}
                              onDragEnd={handleDragEnd}
                              onClick={() => openEditDialog(apt)}
                              className={`absolute left-1 right-1 rounded-lg p-2 text-white overflow-hidden shadow-lg cursor-grab active:cursor-grabbing hover:scale-[1.02] hover:shadow-xl transition-all border-l-4 border-white/50 ${
                                isHighlighted ? 'ring-4 ring-yellow-400 ring-offset-2 z-20' : ''
                              }`}
                              style={{
                                ...style,
                                backgroundColor: apt.status === 'completed' ? '#10B981' : (apt.operator_color || col.color),
                              }}
                              title={`Clicca per modificare - ${apt.client_name}`}
                            >
                              <div className="flex justify-between items-start">
                                <div className="flex-1 min-w-0">
                                  <p className="font-bold truncate text-sm drop-shadow-sm">
                                    {apt.status === 'completed' && '\u2713 '}{apt.client_name}
                                  </p>
                                  <p className="text-white font-medium truncate text-[11px] drop-shadow-sm">
                                    {apt.time} - {apt.end_time}
                                  </p>
                                  <p className="text-white/90 truncate text-[10px]">
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

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs text-[#334155]">
          <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full bg-[#0EA5E9]" /> Da fare</div>
          <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full bg-emerald-500" /> Completato</div>
        </div>


        {/* New Appointment Dialog */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle className="font-playfair text-2xl text-[#0F172A]">
                Nuovo Appuntamento
              </DialogTitle>
              <DialogDescription>
                {format(selectedDate, "EEEE d MMMM yyyy", { locale: it })} alle {formData.time}
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label className="text-[#0F172A] font-semibold">Cliente</Label>
                <div className="relative">
                  <Input
                    type="text"
                    placeholder="Digita nome cliente..."
                    value={clientSearch}
                    onChange={(e) => {
                      setClientSearch(e.target.value);
                      setShowClientDropdown(true);
                      if (!e.target.value) {
                        setFormData({ ...formData, client_id: '' });
                        setSelectedClientInfo(null);
                      }
                    }}
                    onFocus={() => setShowClientDropdown(true)}
                    className="bg-white border-2 border-[#E2E8F0] text-[#0F172A] font-medium"
                    data-testid="search-client-dialog"
                  />
                  {showClientDropdown && clientSearch.length > 0 && (
                    <div className="absolute z-50 w-full mt-1 bg-white border-2 border-[#0EA5E9] rounded-lg shadow-xl max-h-48 overflow-auto">
                      {clients
                        .filter(c => c.name.toLowerCase().includes(clientSearch.toLowerCase()))
                        .slice(0, 20)
                        .map((client) => (
                          <button
                            key={client.id}
                            type="button"
                            className={`w-full px-3 py-2 text-left hover:bg-[#0EA5E9]/20 text-sm font-medium border-b border-[#E2E8F0]/30 last:border-0 ${
                              formData.client_id === client.id ? 'bg-[#0EA5E9]/20 text-[#0EA5E9]' : 'text-[#0F172A]'
                            }`}
                            onClick={() => handleClientSelect(client.id, client.name)}
                          >
                            {client.name}
                          </button>
                        ))}
                      {clients.filter(c => c.name.toLowerCase().includes(clientSearch.toLowerCase())).length === 0 && (
                        <div className="px-3 py-2 text-sm text-[#334155]">Nessun cliente trovato</div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Client Info Card */}
              {selectedClientInfo && (
                <div className="p-3 bg-[#FEF3C7] border-2 border-[#F59E0B] rounded-lg">
                  <div className="flex items-start gap-2">
                    <User className="w-5 h-5 text-[#F59E0B] flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p className="font-bold text-[#92400E]">{selectedClientInfo.name}</p>
                      {selectedClientInfo.phone && (
                        <p className="text-sm text-[#92400E]">Tel: {selectedClientInfo.phone}</p>
                      )}
                      {selectedClientInfo.notes && (
                        <p className="text-sm text-[#92400E] mt-1 whitespace-pre-wrap">{selectedClientInfo.notes}</p>
                      )}
                      {!selectedClientInfo.notes && (
                        <p className="text-sm text-[#92400E]/60 italic">Nessuna nota</p>
                      )}
                    </div>
                  </div>
                </div>
              )}

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
                  className="bg-[#0EA5E9] hover:bg-[#0284C7] text-white"
                  data-testid="save-appointment-btn"
                >
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Salva Appuntamento'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Recurring Appointment Dialog */}
        <Dialog open={recurringDialogOpen} onOpenChange={setRecurringDialogOpen}>
          <DialogContent className="sm:max-w-[400px]">
            <DialogHeader>
              <DialogTitle className="font-playfair text-2xl text-[#0F172A]">
                Ripeti Appuntamento
              </DialogTitle>
              <DialogDescription>
                {selectedAppointment && (
                  <span>
                    {selectedAppointment.client_name} - {selectedAppointment.date} alle {selectedAppointment.time}
                  </span>
                )}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              {selectedAppointment && (
                <div className="p-4 bg-[#F8FAFC] rounded-lg">
                  <p className="text-sm font-medium text-[#0F172A]">
                    Servizi: {selectedAppointment.services.map(s => s.name).join(', ')}
                  </p>
                  <p className="text-xs text-[#334155] mt-1">
                    {selectedAppointment.operator_name || 'Non assegnato'}
                  </p>
                </div>
              )}

              <div className="space-y-2">
                <Label>Ripeti ogni</Label>
                <Select
                  value={recurringData.repeat_weeks.toString()}
                  onValueChange={(val) => setRecurringData({ ...recurringData, repeat_weeks: parseInt(val) })}
                >
                  <SelectTrigger data-testid="select-repeat-weeks">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">1 settimana</SelectItem>
                    <SelectItem value="2">2 settimane</SelectItem>
                    <SelectItem value="3">3 settimane</SelectItem>
                    <SelectItem value="4">4 settimane</SelectItem>
                    <SelectItem value="6">6 settimane</SelectItem>
                    <SelectItem value="8">8 settimane</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Numero di ripetizioni</Label>
                <Select
                  value={recurringData.repeat_count.toString()}
                  onValueChange={(val) => setRecurringData({ ...recurringData, repeat_count: parseInt(val) })}
                >
                  <SelectTrigger data-testid="select-repeat-count">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {[2, 3, 4, 5, 6, 8, 10, 12].map((n) => (
                      <SelectItem key={n} value={n.toString()}>
                        {n} volte
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="p-3 bg-[#0EA5E9]/10 rounded-lg">
                <p className="text-sm text-[#0F172A]">
                  <Check className="w-4 h-4 inline mr-1 text-[#0EA5E9]" />
                  Verranno creati <strong>{recurringData.repeat_count}</strong> nuovi appuntamenti, 
                  uno ogni <strong>{recurringData.repeat_weeks}</strong> settimane
                </p>
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setRecurringDialogOpen(false)}
                  className="border-[#E2E8F0]"
                >
                  Annulla
                </Button>
                <Button
                  onClick={handleCreateRecurring}
                  disabled={creatingRecurring}
                  className="bg-[#0EA5E9] hover:bg-[#0284C7] text-white"
                  data-testid="create-recurring-btn"
                >
                  {creatingRecurring ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Crea Appuntamenti'}
                </Button>
              </DialogFooter>
            </div>
          </DialogContent>
        </Dialog>

        {/* Edit/Delete Appointment Dialog */}
        <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
          <DialogContent className="sm:max-w-[550px]">
            <DialogHeader>
              <DialogTitle className="font-playfair text-2xl text-[#0F172A]">
                Modifica Appuntamento
              </DialogTitle>
              <DialogDescription>
                {editingAppointment && `${editingAppointment.date} alle ${editingAppointment.time}`}
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleUpdateAppointment} className="space-y-4 mt-4">
              {/* Client Info */}
              {selectedClientInfo && (
                <div className="p-3 bg-[#FEF3C7] border-2 border-[#F59E0B] rounded-lg">
                  <div className="flex items-start gap-2">
                    <User className="w-5 h-5 text-[#F59E0B] flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p className="font-bold text-[#92400E]">{selectedClientInfo.name}</p>
                      {selectedClientInfo.phone && (
                        <p className="text-sm text-[#92400E]">Tel: {selectedClientInfo.phone}</p>
                      )}
                      {selectedClientInfo.notes && (
                        <p className="text-sm text-[#92400E] mt-1 whitespace-pre-wrap">{selectedClientInfo.notes}</p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-[#0F172A] font-semibold">Orario</Label>
                  <Select
                    value={formData.time}
                    onValueChange={(val) => setFormData({ ...formData, time: val })}
                  >
                    <SelectTrigger className="border-2 border-[#E2E8F0]">
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
                  <Label className="text-[#0F172A] font-semibold">Operatore</Label>
                  <Select
                    value={formData.operator_id || "none"}
                    onValueChange={(val) => setFormData({ ...formData, operator_id: val === "none" ? "" : val })}
                  >
                    <SelectTrigger className="border-2 border-[#E2E8F0]">
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
                <Label className="text-[#0F172A] font-semibold">Servizi</Label>
                <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto">
                  {services.map((service) => (
                    <Button
                      key={service.id}
                      type="button"
                      variant="outline"
                      className={`justify-start h-auto py-2 px-3 ${
                        formData.service_ids.includes(service.id)
                          ? 'bg-[#0EA5E9]/20 border-2 border-[#0EA5E9] text-[#0EA5E9] font-semibold'
                          : 'border-2 border-[#E2E8F0] text-[#0F172A]'
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
                <Label className="text-[#0F172A] font-semibold">Note appuntamento</Label>
                <Input
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Note aggiuntive..."
                  className="bg-white border-2 border-[#E2E8F0]"
                />
              </div>

              {/* Checkout Section */}
              {editingAppointment?.status === 'completed' ? (
                <div className="pt-4 border-t-2 border-emerald-300 bg-emerald-50 -mx-6 px-6 pb-4 rounded-b-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                      <CheckCircle className="w-6 h-6 text-emerald-600" />
                    </div>
                    <div>
                      <p className="font-bold text-emerald-800">Pagamento completato</p>
                      <p className="text-sm text-emerald-600">
                        {editingAppointment.payment_method === 'cash' ? 'Contanti' : editingAppointment.payment_method === 'card' ? 'Carta' : editingAppointment.payment_method || 'N/A'}
                        {editingAppointment.amount_paid ? ` - \u20AC${editingAppointment.amount_paid.toFixed(2)}` : ''}
                      </p>
                    </div>
                  </div>
                </div>
              ) : !checkoutMode ? (
                <div className="pt-4 border-t-2 border-[#E2E8F0]">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold text-[#0F172A]">Totale servizi</p>
                      <p className="text-2xl font-black text-[#0EA5E9]">€{calculateTotal().toFixed(2)}</p>
                    </div>
                    <Button
                      type="button"
                      onClick={() => setCheckoutMode(true)}
                      className="bg-green-600 hover:bg-green-700 text-white font-bold px-6"
                      data-testid="open-checkout-btn"
                    >
                      <Euro className="w-4 h-4 mr-2" />
                      INCASSA
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="pt-4 border-t-2 border-green-500 bg-green-50 -mx-6 px-6 pb-4 rounded-b-lg">
                  <h3 className="text-lg font-black text-green-800 mb-4 flex items-center gap-2">
                    <Euro className="w-5 h-5" />
                    INCASSO
                  </h3>
                  
                  {/* Payment Method */}
                  <div className="space-y-2 mb-4">
                    <Label className="text-[#0F172A] font-bold">Metodo di pagamento</Label>
                    <div className="grid grid-cols-2 gap-2">
                      <Button
                        type="button"
                        variant={paymentMethod === 'cash' ? 'default' : 'outline'}
                        className={paymentMethod === 'cash' ? 'bg-green-600 text-white' : 'border-2'}
                        onClick={() => setPaymentMethod('cash')}
                      >
                        <Banknote className="w-4 h-4 mr-2" />
                        Contanti
                      </Button>
                      <Button
                        type="button"
                        variant={paymentMethod === 'card' ? 'default' : 'outline'}
                        className={paymentMethod === 'card' ? 'bg-green-600 text-white' : 'border-2'}
                        onClick={() => setPaymentMethod('card')}
                      >
                        <CreditCard className="w-4 h-4 mr-2" />
                        Carta
                      </Button>
                      <Button
                        type="button"
                        variant={paymentMethod === 'transfer' ? 'default' : 'outline'}
                        className={paymentMethod === 'transfer' ? 'bg-green-600 text-white' : 'border-2'}
                        onClick={() => setPaymentMethod('transfer')}
                      >
                        <Euro className="w-4 h-4 mr-2" />
                        Bonifico
                      </Button>
                      <Button
                        type="button"
                        variant={paymentMethod === 'prepaid' ? 'default' : 'outline'}
                        className={paymentMethod === 'prepaid' ? 'bg-green-600 text-white' : 'border-2'}
                        onClick={() => setPaymentMethod('prepaid')}
                      >
                        <CreditCard className="w-4 h-4 mr-2" />
                        Prepagata
                      </Button>
                    </div>
                  </div>

                  {/* Discount */}
                  <div className="space-y-2 mb-4">
                    <Label className="text-[#0F172A] font-bold">Sconto</Label>
                    <div className="flex gap-2">
                      <Select value={discountType} onValueChange={setDiscountType}>
                        <SelectTrigger className="w-40 border-2">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">Nessuno</SelectItem>
                          <SelectItem value="percent">Percentuale %</SelectItem>
                          <SelectItem value="fixed">Importo fisso €</SelectItem>
                        </SelectContent>
                      </Select>
                      {discountType !== 'none' && (
                        <Input
                          type="number"
                          placeholder={discountType === 'percent' ? 'es. 10%' : 'es. 5€'}
                          value={discountValue}
                          onChange={(e) => setDiscountValue(e.target.value)}
                          className="flex-1 border-2"
                        />
                      )}
                    </div>
                  </div>

                  {/* Summary */}
                  <div className="bg-white rounded-lg p-4 border-2 border-green-200 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="font-semibold">Subtotale:</span>
                      <span>€{calculateTotal().toFixed(2)}</span>
                    </div>
                    {discountType !== 'none' && calculateDiscount() > 0 && (
                      <div className="flex justify-between text-sm text-red-600">
                        <span className="font-semibold">Sconto:</span>
                        <span>-€{calculateDiscount().toFixed(2)}</span>
                      </div>
                    )}
                    <div className="flex justify-between text-xl font-black pt-2 border-t border-green-200">
                      <span>TOTALE:</span>
                      <span className="text-green-600">€{calculateFinalAmount().toFixed(2)}</span>
                    </div>
                    {calculateFinalAmount() >= 10 && (
                      <div className="flex items-center gap-1.5 text-sm text-amber-600 pt-1" data-testid="loyalty-points-preview">
                        <Star className="w-4 h-4 text-amber-500" />
                        <span className="font-semibold">
                          +{Math.floor(calculateFinalAmount() / 10)} punti fedeltà
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Checkout Actions */}
                  <div className="flex gap-2 mt-4">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={resetCheckout}
                      className="flex-1 border-2"
                    >
                      Annulla
                    </Button>
                    <Button
                      type="button"
                      onClick={handleCheckout}
                      disabled={processing}
                      className="flex-1 bg-green-600 hover:bg-green-700 text-white font-bold"
                      data-testid="confirm-checkout-btn"
                    >
                      {processing ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <>
                          <CheckCircle className="w-4 h-4 mr-2" />
                          CONFERMA PAGAMENTO
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              )}

              {!checkoutMode && (
                <DialogFooter className="flex gap-2">
                  <Button
                    type="button"
                    variant="destructive"
                    onClick={handleDeleteAppointment}
                    disabled={deleting}
                    className="mr-auto"
                    data-testid="delete-appointment-btn"
                  >
                    {deleting ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Trash2 className="w-4 h-4 mr-1" /> Elimina</>}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setEditDialogOpen(false);
                      setEditingAppointment(null);
                      resetCheckout();
                    }}
                    className="border-[#E2E8F0]"
                  >
                    Annulla
                  </Button>
                  <Button
                    type="submit"
                    disabled={saving}
                    className="bg-[#0EA5E9] hover:bg-[#0284C7] text-white font-semibold"
                    data-testid="update-appointment-btn"
                  >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Edit3 className="w-4 h-4 mr-1" /> Salva</>}
                  </Button>
                </DialogFooter>
              )}
            </form>
          </DialogContent>
        </Dialog>

        {/* Loyalty WhatsApp Alert */}
        <Dialog open={loyaltyAlertOpen} onOpenChange={setLoyaltyAlertOpen}>
          <DialogContent className="sm:max-w-[420px]">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-xl font-black text-amber-600">
                <Star className="w-6 h-6 text-amber-500" />
                Traguardo Fedeltà Raggiunto!
              </DialogTitle>
              <DialogDescription>
                <span className="font-bold text-[#0F172A]">{loyaltyAlertData?.clientName}</span> ha raggiunto{' '}
                <span className="font-black text-amber-600">{loyaltyAlertData?.totalPoints} punti</span> fedeltà!
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div className="p-4 bg-amber-50 rounded-xl border border-amber-200 text-sm text-amber-800">
                {loyaltyAlertData?.totalPoints >= 10 ? (
                  <p>Ha diritto ad un <strong>taglio gratis</strong> o uno <strong>sconto di €10,00</strong> sui servizi di colpi di sole e schiariture.</p>
                ) : (
                  <p>Ha diritto ad uno <strong>sconto di €10,00</strong> sui servizi di colpi di sole e schiariture.</p>
                )}
              </div>
              <p className="text-sm text-[#334155]">Vuoi avvisare il cliente su WhatsApp?</p>
            </div>
            <DialogFooter className="flex gap-2 sm:gap-2">
              <Button
                variant="outline"
                onClick={() => setLoyaltyAlertOpen(false)}
                className="flex-1 border-[#E2E8F0]"
              >
                Chiudi
              </Button>
              <Button
                onClick={openLoyaltyWhatsApp}
                className="flex-1 bg-green-500 hover:bg-green-600 text-white font-bold"
                data-testid="loyalty-whatsapp-btn"
              >
                <MessageSquare className="w-4 h-4 mr-2" />
                Invia WhatsApp
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
