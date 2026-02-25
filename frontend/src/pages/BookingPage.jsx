import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Calendar, Clock, User, Scissors, CheckCircle, ArrowLeft, MapPin, Phone, Mail, Star, MessageSquare, ChevronDown, ArrowRight } from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { toast, Toaster } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const HERO_IMG = "https://customer-assets.emergentagent.com/job_ac0aaacf-8266-485a-8bab-9e57ed904c7a/artifacts/0inxpacz_517029262_10231563813060391_9151321643853820111_n.jpg";
const SALON_IMG = "https://images.unsplash.com/photo-1706629503603-e47c37722776?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2MzR8MHwxfHNlYXJjaHwyfHxsdXh1cnklMjBoYWlyJTIwc2Fsb24lMjBpbnRlcmlvciUyMGVsZWdhbnR8ZW58MHx8fHwxNzcyMDEwODc0fDA&ixlib=rb-4.1.0&q=85";

const SERVICES_DISPLAY = [
  { name: "Taglio", price: "€ 10", desc: "Taglio stilistico personalizzato" },
  { name: "Piega Corti", price: "€ 10", desc: "Piega professionale capelli corti" },
  { name: "Piega Lunghi", price: "€ 12", desc: "Piega professionale capelli lunghi" },
  { name: "Piega Fantasy", price: "€ 15", desc: "Piega creativa e personalizzata" },
  { name: "Piastra/Ferro", price: "+ € 3", desc: "Styling con piastra o ferro" },
  { name: "Colorazione Parziale", price: "€ 18", desc: "Colorazione su zone specifiche" },
  { name: "Colorazione Completa", price: "€ 30", desc: "Colorazione completa senza ammoniaca" },
  { name: "Cuffia - Cartine", price: "Da € 40", desc: "Schiariture con tecniche tradizionali" },
  { name: "Balayage", price: "Da € 40", desc: "Schiariture naturali e sfumate" },
  { name: "Giochi di Colore", price: "Da € 40", desc: "Effetti unici e personalizzati" },
];

const REVIEWS = [
  { name: "Maria R.", text: "Bruno è un vero professionista! Sono anni che vengo da lui e sono sempre soddisfatta. Consiglio vivamente!", rating: 5 },
  { name: "Laura B.", text: "Ambiente elegante e accogliente, personale gentilissimo. Il taglio è perfetto, proprio come lo volevo!", rating: 5 },
  { name: "Anna V.", text: "Finalmente ho trovato un parrucchiere che capisce cosa voglio! Colore stupendo e piega perfetta.", rating: 5 },
  { name: "Francesca N.", text: "Professionalità e cortesia. I miei capelli non sono mai stati così belli. Grazie Bruno!", rating: 5 },
];

const TIME_SLOTS = [];
for (let h = 8; h <= 20; h++) {
  for (let m = 0; m < 60; m += 15) {
    TIME_SLOTS.push(`${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`);
  }
}

export default function BookingPage() {
  const [showBooking, setShowBooking] = useState(false);
  const [step, setStep] = useState(1);
  const [services, setServices] = useState([]);
  const [operators, setOperators] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const servicesRef = useRef(null);
  const contactRef = useRef(null);

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

  const toggleService = (id) => {
    setFormData(prev => ({
      ...prev,
      service_ids: prev.service_ids.includes(id)
        ? prev.service_ids.filter(s => s !== id)
        : [...prev.service_ids, id]
    }));
  };

  const selectedServices = services.filter(s => formData.service_ids.includes(s.id));
  const totalPrice = selectedServices.reduce((sum, s) => sum + (s.price || 0), 0);
  const totalDuration = selectedServices.reduce((sum, s) => sum + (s.duration || 0), 0);

  const handleSubmit = async () => {
    if (!formData.client_name || !formData.client_phone) {
      toast.error('Inserisci nome e telefono');
      return;
    }
    setSubmitting(true);
    try {
      await axios.post(`${API}/public/book-appointment`, formData);
      setSuccess(true);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore nella prenotazione');
    } finally {
      setSubmitting(false);
    }
  };

  const scrollTo = (ref) => {
    ref.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const openWhatsApp = () => {
    window.open('https://wa.me/393397833526?text=Ciao, vorrei prenotare un appuntamento!', '_blank');
  };

  // SUCCESS PAGE
  if (success) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center p-4">
        <Toaster position="top-center" />
        <div className="max-w-md w-full text-center">
          <CheckCircle className="w-20 h-20 mx-auto text-emerald-400 mb-6" />
          <h1 className="text-3xl font-black text-white mb-3">Prenotazione Confermata!</h1>
          <p className="text-gray-300 mb-2">
            Ti aspettiamo il <span className="text-white font-bold">{format(new Date(formData.date), 'd MMMM yyyy', { locale: it })}</span> alle <span className="text-white font-bold">{formData.time}</span>
          </p>
          <p className="text-sm text-gray-500 mb-8">Riceverai un promemoria prima dell'appuntamento.</p>
          <Button
            onClick={() => { setSuccess(false); setShowBooking(false); setStep(1); setFormData({ client_name: '', client_phone: '', service_ids: [], operator_id: '', date: format(new Date(), 'yyyy-MM-dd'), time: '09:00', notes: '' }); }}
            className="bg-white text-[#0a0a0a] hover:bg-gray-200 font-bold px-8"
          >
            Torna alla Home
          </Button>
        </div>
      </div>
    );
  }

  // BOOKING FORM
  if (showBooking) {
    return (
      <div className="min-h-screen bg-[#0a0a0a]">
        <Toaster position="top-center" />
        {/* Header */}
        <div className="bg-[#111] border-b border-gray-800 py-4 px-4 sticky top-0 z-50">
          <div className="max-w-lg mx-auto flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setShowBooking(false)}
              className="text-gray-400 hover:text-white hover:bg-white/10 shrink-0"
              data-testid="booking-back-btn"
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div className="flex items-center gap-3">
              <img src="/logo.png?v=3" alt="MBHS Salon" className="w-9 h-9 rounded-lg" />
              <div>
                <h1 className="text-white text-sm font-black leading-tight">BRUNO MELITO HAIR</h1>
                <p className="text-gray-500 text-xs">Prenota il tuo appuntamento</p>
              </div>
            </div>
          </div>
        </div>

        {/* Steps */}
        <div className="max-w-lg mx-auto px-4 py-6">
          <div className="flex items-center justify-center gap-2 mb-6">
            {[1, 2, 3].map(s => (
              <div key={s} className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${step >= s ? 'bg-white text-[#0a0a0a]' : 'bg-gray-800 text-gray-500'}`}>
                  {step > s ? <CheckCircle className="w-4 h-4" /> : s}
                </div>
                {s < 3 && <div className={`w-12 h-0.5 ${step > s ? 'bg-white' : 'bg-gray-800'}`} />}
              </div>
            ))}
          </div>

          {/* Step 1: Services */}
          {step === 1 && (
            <div className="space-y-4">
              <h2 className="text-xl font-black text-white">Scegli i Servizi</h2>
              {loading ? (
                <div className="flex justify-center py-8"><Clock className="w-6 h-6 text-gray-500 animate-spin" /></div>
              ) : (
                <div className="space-y-2">
                  {services.map(service => (
                    <div
                      key={service.id}
                      onClick={() => toggleService(service.id)}
                      className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                        formData.service_ids.includes(service.id)
                          ? 'border-white bg-white/10'
                          : 'border-gray-800 bg-[#111] hover:border-gray-600'
                      }`}
                    >
                      <div className="flex justify-between items-center">
                        <div>
                          <p className="font-bold text-white">{service.name}</p>
                          <p className="text-sm text-gray-500">{service.duration} min</p>
                        </div>
                        <p className="font-black text-white">€{service.price}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {formData.service_ids.length > 0 && (
                <div className="bg-[#111] p-4 rounded-xl border border-gray-800">
                  <p className="font-bold text-white">Riepilogo: {totalDuration} min - €{totalPrice}</p>
                </div>
              )}
              <Button
                onClick={() => setStep(2)}
                disabled={formData.service_ids.length === 0}
                className="w-full bg-white text-[#0a0a0a] hover:bg-gray-200 font-bold py-6"
              >
                Continua <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          )}

          {/* Step 2: Date & Time */}
          {step === 2 && (
            <div className="space-y-4">
              <h2 className="text-xl font-black text-white">Data e Ora</h2>
              <div className="space-y-3">
                <div>
                  <label className="text-sm text-gray-400 font-semibold mb-1 block">Data</label>
                  <Input
                    type="date"
                    value={formData.date}
                    min={format(new Date(), 'yyyy-MM-dd')}
                    onChange={(e) => setFormData({...formData, date: e.target.value})}
                    className="bg-[#111] border-gray-800 text-white"
                  />
                </div>
                <div>
                  <label className="text-sm text-gray-400 font-semibold mb-1 block">Ora</label>
                  <select
                    value={formData.time}
                    onChange={(e) => setFormData({...formData, time: e.target.value})}
                    className="w-full p-3 bg-[#111] border border-gray-800 rounded-lg text-white"
                  >
                    {TIME_SLOTS.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                {operators.length > 0 && (
                  <div>
                    <label className="text-sm text-gray-400 font-semibold mb-1 block">Operatore (opzionale)</label>
                    <select
                      value={formData.operator_id}
                      onChange={(e) => setFormData({...formData, operator_id: e.target.value})}
                      className="w-full p-3 bg-[#111] border border-gray-800 rounded-lg text-white"
                    >
                      <option value="">Nessuna preferenza</option>
                      {operators.map(op => <option key={op.id} value={op.id}>{op.name}</option>)}
                    </select>
                  </div>
                )}
              </div>
              <div className="flex gap-3">
                <Button onClick={() => setStep(1)} variant="outline" className="flex-1 border-gray-700 text-gray-300 hover:bg-white/10">Indietro</Button>
                <Button onClick={() => setStep(3)} className="flex-1 bg-white text-[#0a0a0a] hover:bg-gray-200 font-bold">
                  Continua <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          )}

          {/* Step 3: Contact Info */}
          {step === 3 && (
            <div className="space-y-4">
              <h2 className="text-xl font-black text-white">I Tuoi Dati</h2>
              <div className="space-y-3">
                <div>
                  <label className="text-sm text-gray-400 font-semibold mb-1 block">Nome e Cognome *</label>
                  <Input
                    value={formData.client_name}
                    onChange={(e) => setFormData({...formData, client_name: e.target.value})}
                    placeholder="Es. Maria Rossi"
                    className="bg-[#111] border-gray-800 text-white placeholder:text-gray-600"
                  />
                </div>
                <div>
                  <label className="text-sm text-gray-400 font-semibold mb-1 block">Telefono *</label>
                  <Input
                    value={formData.client_phone}
                    onChange={(e) => setFormData({...formData, client_phone: e.target.value})}
                    placeholder="Es. 339 123 4567"
                    className="bg-[#111] border-gray-800 text-white placeholder:text-gray-600"
                  />
                </div>
                <div>
                  <label className="text-sm text-gray-400 font-semibold mb-1 block">Note (opzionale)</label>
                  <Textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({...formData, notes: e.target.value})}
                    placeholder="Richieste particolari..."
                    className="bg-[#111] border-gray-800 text-white placeholder:text-gray-600"
                    rows={3}
                  />
                </div>
              </div>
              {/* Summary */}
              <div className="bg-[#111] p-4 rounded-xl border border-gray-800 space-y-2">
                <p className="text-sm text-gray-400">Riepilogo:</p>
                {selectedServices.map(s => (
                  <div key={s.id} className="flex justify-between text-sm">
                    <span className="text-gray-300">{s.name}</span>
                    <span className="text-white font-bold">€{s.price}</span>
                  </div>
                ))}
                <div className="border-t border-gray-800 pt-2 flex justify-between">
                  <span className="text-white font-bold">Totale</span>
                  <span className="text-white font-black text-lg">€{totalPrice}</span>
                </div>
                <p className="text-xs text-gray-500">{format(new Date(formData.date), 'd MMMM yyyy', { locale: it })} alle {formData.time}</p>
              </div>
              <div className="flex gap-3">
                <Button onClick={() => setStep(2)} variant="outline" className="flex-1 border-gray-700 text-gray-300 hover:bg-white/10">Indietro</Button>
                <Button
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="flex-1 bg-white text-[#0a0a0a] hover:bg-gray-200 font-bold"
                >
                  {submitting ? <Clock className="w-4 h-4 animate-spin" /> : 'Conferma Prenotazione'}
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // ==================== LANDING PAGE ====================
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white" data-testid="booking-welcome">
      <Toaster position="top-center" />

      {/* NAVBAR */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0a]/90 backdrop-blur-md border-b border-white/5">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/logo.png?v=3" alt="MBHS Salon" className="w-10 h-10 rounded-lg" />
            <span className="font-black text-sm sm:text-base tracking-tight">BRUNO MELITO HAIR</span>
          </div>
          <div className="hidden sm:flex items-center gap-6 text-sm text-gray-400">
            <button onClick={() => scrollTo(servicesRef)} className="hover:text-white transition-colors">Servizi</button>
            <button onClick={() => scrollTo(contactRef)} className="hover:text-white transition-colors">Contatti</button>
          </div>
          <Button
            onClick={() => setShowBooking(true)}
            className="bg-white text-[#0a0a0a] hover:bg-gray-200 font-bold text-sm px-4 sm:px-6"
            data-testid="booking-start-btn"
          >
            PRENOTA ORA
          </Button>
        </div>
      </nav>

      {/* HERO SECTION */}
      <section className="relative min-h-screen flex items-center pt-16">
        <div className="absolute inset-0">
          <img src={HERO_IMG} alt="Bruno Melito Hair" className="w-full h-full object-cover opacity-30" />
          <div className="absolute inset-0 bg-gradient-to-b from-[#0a0a0a]/60 via-[#0a0a0a]/40 to-[#0a0a0a]" />
        </div>
        <div className="relative max-w-6xl mx-auto px-4 py-20 sm:py-32">
          <div className="max-w-2xl">
            <div className="inline-block bg-white/10 backdrop-blur-sm text-white text-xs font-bold px-4 py-2 rounded-full border border-white/10 mb-6">
              SOLO PER APPUNTAMENTO
            </div>
            <h1 className="text-4xl sm:text-6xl lg:text-7xl font-black leading-[0.9] tracking-tight mb-6">
              Metti la<br />testa a<br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-200 to-amber-400">posto!!</span>
            </h1>
            <p className="text-base sm:text-lg text-gray-300 max-w-lg mb-8 leading-relaxed">
              Scopri l'eccellenza dell'hair styling al Bruno Melito Hair. Dove ogni taglio è un'opera d'arte e ogni cliente è unica.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 mb-10">
              <Button
                onClick={() => setShowBooking(true)}
                className="bg-white text-[#0a0a0a] hover:bg-gray-200 font-black text-base px-8 py-6 rounded-xl"
              >
                <Scissors className="w-5 h-5 mr-2" />
                PRENOTA ORA
              </Button>
              <Button
                onClick={() => scrollTo(servicesRef)}
                variant="outline"
                className="border-white/20 text-white hover:bg-white/10 font-bold text-base px-8 py-6 rounded-xl"
              >
                Scopri i Servizi
                <ChevronDown className="w-4 h-4 ml-2" />
              </Button>
            </div>
            {/* Contact quick links */}
            <div className="flex flex-col sm:flex-row gap-4 text-sm">
              <a href="tel:08231878320" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
                <Phone className="w-4 h-4" /> 0823 18 78 320
              </a>
              <a href="tel:3397833526" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
                <Phone className="w-4 h-4" /> 339 78 33 526
              </a>
              <span className="flex items-center gap-2 text-gray-400">
                <MapPin className="w-4 h-4" /> Via Vito Nicola Melorio 101, S.M.C.V.
              </span>
            </div>
          </div>
          {/* Experience badge */}
          <div className="absolute right-4 sm:right-8 bottom-20 sm:bottom-32 bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-5 text-center hidden md:block">
            <p className="text-4xl font-black text-amber-300">40+</p>
            <p className="text-xs text-gray-400 font-semibold">Anni di<br />Esperienza</p>
            <p className="text-[10px] text-gray-600 mt-1">Dal 1983</p>
          </div>
        </div>
      </section>

      {/* SERVICES SECTION */}
      <section ref={servicesRef} className="py-20 sm:py-28 relative">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-12">
            <p className="text-amber-400 font-bold text-sm tracking-widest uppercase mb-3">I Nostri Servizi</p>
            <h2 className="text-3xl sm:text-4xl font-black">Servizi Professionali</h2>
            <p className="text-gray-500 mt-3 max-w-xl mx-auto">Dal taglio classico alle tecniche più innovative, offriamo una gamma completa di servizi per prenderci cura dei tuoi capelli.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {SERVICES_DISPLAY.map((service, idx) => (
              <div key={idx} className="bg-[#111] border border-gray-800/50 rounded-2xl p-5 hover:border-gray-700 transition-colors group">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-bold text-white group-hover:text-amber-300 transition-colors">{service.name}</h3>
                    <p className="text-sm text-gray-500 mt-1">{service.desc}</p>
                  </div>
                  <span className="text-amber-400 font-black text-lg shrink-0 ml-3">{service.price}</span>
                </div>
              </div>
            ))}
          </div>
          <div className="text-center mt-8">
            <p className="text-gray-600 text-sm mb-6">Tutti i nostri servizi includono consulenza personalizzata e prodotti professionali.</p>
            <Button
              onClick={() => setShowBooking(true)}
              className="bg-white text-[#0a0a0a] hover:bg-gray-200 font-bold px-8 py-6 rounded-xl"
            >
              <Scissors className="w-4 h-4 mr-2" />
              PRENOTA ORA
            </Button>
          </div>
        </div>
      </section>

      {/* ABOUT SECTION */}
      <section className="py-20 sm:py-28 bg-[#111]">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="rounded-2xl overflow-hidden h-80 lg:h-96">
              <img src={SALON_IMG} alt="Il nostro salone" className="w-full h-full object-cover" />
            </div>
            <div>
              <p className="text-amber-400 font-bold text-sm tracking-widest uppercase mb-3">Chi Siamo</p>
              <h2 className="text-3xl sm:text-4xl font-black mb-6">Dal 1983<br />con Passione</h2>
              <p className="text-gray-400 leading-relaxed mb-6">
                Dal 1983 con grande soddisfazione nostra e delle clienti che ci seguono, siamo un punto di riferimento per chi cerca qualità e professionalità nell'hair styling.
              </p>
              <p className="text-gray-400 leading-relaxed mb-8">
                Abbiamo introdotto una nuova linea di prodotti altamente curativi, di ultima generazione: shampoo, maschere e finishing, senza parabeni, solfati e sale. Le colorazioni e le schiariture sono senza ammoniaca, ma con cheratina, olio di semi di lino, proteine della seta e olio di argan.
              </p>
              <div className="grid grid-cols-2 gap-3">
                {["Dal 1983 nel settore", "Senza parabeni e solfati", "Colorazioni senza ammoniaca", "Cheratina e olio di argan"].map((item, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-amber-400 shrink-0" />
                    <span className="text-sm text-gray-300">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* REVIEWS SECTION */}
      <section className="py-20 sm:py-28">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-12">
            <p className="text-amber-400 font-bold text-sm tracking-widest uppercase mb-3">Recensioni</p>
            <h2 className="text-3xl sm:text-4xl font-black">Cosa Dicono di Noi</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {REVIEWS.map((review, idx) => (
              <div key={idx} className="bg-[#111] border border-gray-800/50 rounded-2xl p-5">
                <div className="flex gap-0.5 mb-3">
                  {[...Array(review.rating)].map((_, i) => (
                    <Star key={i} className="w-4 h-4 fill-amber-400 text-amber-400" />
                  ))}
                </div>
                <p className="text-gray-300 text-sm leading-relaxed mb-4">"{review.text}"</p>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-amber-400/10 rounded-full flex items-center justify-center">
                    <span className="text-amber-400 font-bold text-sm">{review.name[0]}</span>
                  </div>
                  <span className="text-sm text-gray-400 font-semibold">{review.name}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CONTACT SECTION */}
      <section ref={contactRef} className="py-20 sm:py-28 bg-[#111]">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-12">
            <p className="text-amber-400 font-bold text-sm tracking-widest uppercase mb-3">Contattaci</p>
            <h2 className="text-3xl sm:text-4xl font-black">Prenota il Tuo Appuntamento</h2>
            <p className="text-gray-500 mt-3">Siamo pronti ad accoglierti nel nostro salone.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
            {/* Address */}
            <a href="https://maps.google.com/?q=Via+Vito+Nicola+Melorio+101+Santa+Maria+Capua+Vetere" target="_blank" rel="noopener noreferrer"
              className="bg-[#0a0a0a] border border-gray-800/50 rounded-2xl p-5 hover:border-gray-700 transition-colors text-center">
              <MapPin className="w-6 h-6 text-amber-400 mx-auto mb-3" />
              <h3 className="font-bold text-white text-sm mb-1">Indirizzo</h3>
              <p className="text-gray-500 text-xs leading-relaxed">Via Vito Nicola Melorio 101<br />Santa Maria Capua Vetere (CE)</p>
            </a>
            {/* Phone */}
            <div className="bg-[#0a0a0a] border border-gray-800/50 rounded-2xl p-5 text-center">
              <Phone className="w-6 h-6 text-amber-400 mx-auto mb-3" />
              <h3 className="font-bold text-white text-sm mb-1">Telefono</h3>
              <a href="tel:08231878320" className="text-gray-400 text-xs hover:text-white transition-colors block">0823 18 78 320</a>
              <a href="tel:3397833526" className="text-gray-400 text-xs hover:text-white transition-colors block mt-1">339 78 33 526</a>
            </div>
            {/* Email */}
            <a href="mailto:info@brunomelitoair.it"
              className="bg-[#0a0a0a] border border-gray-800/50 rounded-2xl p-5 hover:border-gray-700 transition-colors text-center">
              <Mail className="w-6 h-6 text-amber-400 mx-auto mb-3" />
              <h3 className="font-bold text-white text-sm mb-1">Email</h3>
              <p className="text-gray-400 text-xs">info@brunomelitoair.it</p>
            </a>
            {/* Hours */}
            <div className="bg-[#0a0a0a] border border-gray-800/50 rounded-2xl p-5 text-center">
              <Clock className="w-6 h-6 text-amber-400 mx-auto mb-3" />
              <h3 className="font-bold text-white text-sm mb-1">Orari</h3>
              <p className="text-gray-400 text-xs">Mar - Sab: 9:00 - 19:00</p>
              <p className="text-gray-600 text-xs mt-1">Dom - Lun: Chiuso</p>
            </div>
          </div>
          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button
              onClick={() => setShowBooking(true)}
              className="bg-white text-[#0a0a0a] hover:bg-gray-200 font-black text-base px-10 py-6 rounded-xl w-full sm:w-auto"
            >
              <Scissors className="w-5 h-5 mr-2" />
              PRENOTA ORA
            </Button>
            <Button
              onClick={openWhatsApp}
              className="bg-[#25D366] hover:bg-[#20bd5a] text-white font-bold text-base px-10 py-6 rounded-xl w-full sm:w-auto"
            >
              <MessageSquare className="w-5 h-5 mr-2" />
              WHATSAPP
            </Button>
            <a href="tel:08231878320" className="w-full sm:w-auto">
              <Button variant="outline" className="border-gray-700 text-gray-300 hover:bg-white/10 font-bold text-base px-10 py-6 rounded-xl w-full">
                <Phone className="w-5 h-5 mr-2" />
                CHIAMA
              </Button>
            </a>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="py-8 border-t border-gray-800/50">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <img src="/logo.png?v=3" alt="MBHS Salon" className="w-12 h-12 rounded-lg mx-auto mb-3" />
          <p className="text-gray-500 text-sm font-semibold">BRUNO MELITO HAIR</p>
          <p className="text-gray-700 text-xs mt-2">Via Vito Nicola Melorio 101, Santa Maria Capua Vetere (CE)</p>
          <p className="text-gray-800 text-xs mt-4">© {new Date().getFullYear()} Bruno Melito Hair. Tutti i diritti riservati.</p>
        </div>
      </footer>

      {/* Fixed bottom CTA on mobile */}
      <div className="fixed bottom-0 left-0 right-0 p-3 bg-[#0a0a0a]/95 backdrop-blur-md border-t border-white/5 sm:hidden z-50">
        <Button
          onClick={() => setShowBooking(true)}
          className="w-full bg-white text-[#0a0a0a] hover:bg-gray-200 font-black py-5 rounded-xl"
        >
          <Scissors className="w-5 h-5 mr-2" />
          PRENOTA ORA
        </Button>
      </div>
    </div>
  );
}
