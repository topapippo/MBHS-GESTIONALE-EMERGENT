import { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Calendar, Clock, User, Scissors, CheckCircle, ArrowLeft, MapPin, Phone } from 'lucide-react';
import { format, addDays } from 'date-fns';
import { it } from 'date-fns/locale';
import { toast, Toaster } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TIME_SLOTS = [];
for (let h = 8; h <= 20; h++) {
  for (let m = 0; m < 60; m += 15) {
    TIME_SLOTS.push(`${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`);
  }
}

export default function BookingPage() {
  const [showWelcome, setShowWelcome] = useState(true);
  const [step, setStep] = useState(1);
  const [services, setServices] = useState([]);
  const [operators, setOperators] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const [formData, setFormData] = useState({
    client_name: '',
    client_phone: '',
    service_ids: [],
    operator_id: '',
    date: format(new Date(), 'yyyy-MM-dd'),
    time: '09:00',
    notes: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [servicesRes, operatorsRes] = await Promise.all([
        axios.get(`${API}/public/services`),
        axios.get(`${API}/public/operators`)
      ]);
      setServices(servicesRes.data);
      setOperators(operatorsRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
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

  const handleSubmit = async () => {
    if (!formData.client_name || !formData.client_phone || formData.service_ids.length === 0) {
      toast.error('Compila tutti i campi obbligatori');
      return;
    }

    setSubmitting(true);
    try {
      await axios.post(`${API}/public/booking`, formData);
      setSuccess(true);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore nella prenotazione');
    } finally {
      setSubmitting(false);
    }
  };

  const selectedServices = services.filter(s => formData.service_ids.includes(s.id));
  const totalDuration = selectedServices.reduce((sum, s) => sum + s.duration, 0);
  const totalPrice = selectedServices.reduce((sum, s) => sum + s.price, 0);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8FAFC] p-4">
        <Skeleton className="h-96 max-w-lg mx-auto" />
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center p-4">
        <Card className="max-w-md w-full text-center">
          <CardContent className="p-8">
            <CheckCircle className="w-20 h-20 mx-auto text-green-500 mb-4" />
            <h1 className="text-2xl font-black text-[#0F172A] mb-2">Prenotazione Confermata!</h1>
            <p className="text-[#334155] mb-4">
              Ti aspettiamo il <strong>{format(new Date(formData.date), 'd MMMM yyyy', { locale: it })}</strong> alle <strong>{formData.time}</strong>
            </p>
            <p className="text-sm text-[#334155] mb-6">Riceverai un promemoria prima dell'appuntamento.</p>
            <Button
              onClick={() => { setSuccess(false); setShowWelcome(true); setStep(1); setFormData({ client_name: '', client_phone: '', service_ids: [], operator_id: '', date: format(addDays(new Date(), 1), 'yyyy-MM-dd'), time: '09:00', notes: '' }); }}
              variant="outline"
              className="border-[#0EA5E9] text-[#0EA5E9]"
            >
              Torna alla Home
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Welcome / Landing page
  if (showWelcome) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-[#0EA5E9] to-[#0369A1] flex flex-col items-center justify-center p-4" data-testid="booking-welcome">
        <Toaster position="top-center" />
        <div className="max-w-md w-full text-center space-y-6">
          {/* Logo */}
          <div className="flex justify-center">
            <img
              src="/logo.png?v=3"
              alt="MBHS Salon"
              className="w-40 h-40 rounded-2xl shadow-2xl border-4 border-white/20"
            />
          </div>

          {/* Salon Name */}
          <div>
            <h1 className="text-4xl font-black text-white tracking-tight">MBHS SALON</h1>
          </div>

          {/* Address */}
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-5 space-y-3 border border-white/20">
            <div className="flex items-start gap-3 text-white">
              <MapPin className="w-5 h-5 mt-0.5 shrink-0" />
              <p className="text-left text-sm leading-relaxed">
                Via Vito Nicola Melorio 101<br />
                Santa Maria Capua Vetere (CE)
              </p>
            </div>
            <div className="flex items-center gap-3 text-white">
              <Phone className="w-5 h-5 shrink-0" />
              <div className="text-left text-sm space-y-1">
                <a href="tel:08231878320" className="block hover:underline">0823 1878320</a>
                <a href="tel:3397833526" className="block hover:underline">339 783 3526</a>
              </div>
            </div>
          </div>

          {/* CTA Button */}
          <Button
            onClick={() => setShowWelcome(false)}
            className="w-full bg-white text-[#0EA5E9] hover:bg-blue-50 font-black text-lg py-7 rounded-xl shadow-xl transition-all active:scale-95"
            data-testid="booking-start-btn"
          >
            <Scissors className="w-5 h-5 mr-2" />
            PRENOTA APPUNTAMENTO
          </Button>

          <p className="text-blue-200 text-xs">Prenota online 24 ore su 24</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      <Toaster position="top-center" />
      
      {/* Header */}
      <div className="bg-[#0EA5E9] text-white py-4 px-4">
        <div className="max-w-lg mx-auto flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setShowWelcome(true)}
            className="text-white hover:bg-white/20 shrink-0"
            data-testid="booking-back-btn"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex items-center gap-3">
            <img src="/logo.png?v=3" alt="MBHS Salon" className="w-10 h-10 rounded-lg" />
            <div>
              <h1 className="text-lg font-black leading-tight">MBHS SALON</h1>
              <p className="text-blue-100 text-xs">Prenota il tuo appuntamento</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-lg mx-auto p-4">
        {/* Progress */}
        <div className="flex items-center justify-center gap-2 mb-6">
          {[1, 2, 3].map((s) => (
            <div
              key={s}
              className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                step >= s ? 'bg-[#0EA5E9] text-white' : 'bg-[#E2E8F0] text-[#334155]'
              }`}
            >
              {s}
            </div>
          ))}
        </div>

        {/* Step 1: Select Services */}
        {step === 1 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-xl font-black">
                <Scissors className="w-5 h-5 text-[#0EA5E9]" />
                Scegli i Servizi
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {services.map((service) => (
                <button
                  key={service.id}
                  onClick={() => toggleService(service.id)}
                  className={`w-full p-4 rounded-lg border-2 text-left transition-all ${
                    formData.service_ids.includes(service.id)
                      ? 'border-[#0EA5E9] bg-[#E0F2FE]'
                      : 'border-[#E2E8F0] hover:border-[#0EA5E9]/50'
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-bold text-[#0F172A]">{service.name}</p>
                      <p className="text-sm text-[#334155]">{service.duration} min</p>
                    </div>
                    <p className="text-lg font-black text-[#0EA5E9]">€{service.price}</p>
                  </div>
                </button>
              ))}

              {formData.service_ids.length > 0 && (
                <div className="mt-4 p-4 bg-[#0EA5E9]/10 rounded-lg">
                  <p className="font-semibold text-[#0F172A]">Riepilogo: {totalDuration} min - €{totalPrice}</p>
                </div>
              )}

              <Button
                onClick={() => setStep(2)}
                disabled={formData.service_ids.length === 0}
                className="w-full bg-[#0EA5E9] hover:bg-[#0284C7] text-white font-bold py-6"
              >
                Continua
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Step 2: Select Date/Time */}
        {step === 2 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-xl font-black">
                <Calendar className="w-5 h-5 text-[#0EA5E9]" />
                Scegli Data e Ora
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="font-bold">Data</Label>
                <Input
                  type="date"
                  value={formData.date}
                  min={format(addDays(new Date(), 1), 'yyyy-MM-dd')}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  className="mt-1 border-2"
                />
              </div>

              <div>
                <Label className="font-bold">Ora</Label>
                <Select value={formData.time} onValueChange={(val) => setFormData({ ...formData, time: val })}>
                  <SelectTrigger className="mt-1 border-2">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="max-h-48">
                    {TIME_SLOTS.map((time) => (
                      <SelectItem key={time} value={time}>{time}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {operators.length > 0 && (
                <div>
                  <Label className="font-bold">Operatore (opzionale)</Label>
                  <Select value={formData.operator_id || "any"} onValueChange={(val) => setFormData({ ...formData, operator_id: val === "any" ? "" : val })}>
                    <SelectTrigger className="mt-1 border-2">
                      <SelectValue placeholder="Qualsiasi" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="any">Qualsiasi</SelectItem>
                      {operators.map((op) => (
                        <SelectItem key={op.id} value={op.id}>{op.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setStep(1)} className="flex-1 border-2">
                  <ArrowLeft className="w-4 h-4 mr-1" /> Indietro
                </Button>
                <Button onClick={() => setStep(3)} className="flex-1 bg-[#0EA5E9] hover:bg-[#0284C7] text-white font-bold">
                  Continua
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 3: Your Info */}
        {step === 3 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-xl font-black">
                <User className="w-5 h-5 text-[#0EA5E9]" />
                I Tuoi Dati
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="font-bold">Nome e Cognome *</Label>
                <Input
                  value={formData.client_name}
                  onChange={(e) => setFormData({ ...formData, client_name: e.target.value })}
                  placeholder="Mario Rossi"
                  className="mt-1 border-2"
                />
              </div>

              <div>
                <Label className="font-bold">Telefono *</Label>
                <Input
                  type="tel"
                  value={formData.client_phone}
                  onChange={(e) => setFormData({ ...formData, client_phone: e.target.value })}
                  placeholder="+39 333 1234567"
                  className="mt-1 border-2"
                />
              </div>

              <div>
                <Label className="font-bold">Note (opzionale)</Label>
                <Input
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Richieste particolari..."
                  className="mt-1 border-2"
                />
              </div>

              {/* Summary */}
              <div className="p-4 bg-[#F8FAFC] rounded-lg border-2 border-[#E2E8F0]">
                <h3 className="font-bold text-[#0F172A] mb-2">Riepilogo Prenotazione</h3>
                <p className="text-sm"><strong>Data:</strong> {format(new Date(formData.date), 'd MMMM yyyy', { locale: it })}</p>
                <p className="text-sm"><strong>Ora:</strong> {formData.time}</p>
                <p className="text-sm"><strong>Servizi:</strong> {selectedServices.map(s => s.name).join(', ')}</p>
                <p className="text-lg font-black text-[#0EA5E9] mt-2">Totale: €{totalPrice}</p>
              </div>

              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setStep(2)} className="flex-1 border-2">
                  <ArrowLeft className="w-4 h-4 mr-1" /> Indietro
                </Button>
                <Button
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white font-bold"
                >
                  {submitting ? 'Invio...' : 'PRENOTA ORA'}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
