import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Clock, Scissors, CheckCircle, ArrowLeft, MapPin, Phone, Mail, Star, MessageSquare, ChevronDown, ChevronUp, ArrowRight } from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { toast, Toaster } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Artwork hero image uploaded by the user
const HERO_ARTWORK = "https://customer-assets.emergentagent.com/job_a05a9fc6-c017-4f4a-aee2-38e140acfa26/artifacts/u8hlm0ah_img0012.jpg";
// Real salon photo for background
const HERO_BG = "https://customer-assets.emergentagent.com/job_ac0aaacf-8266-485a-8bab-9e57ed904c7a/artifacts/0inxpacz_517029262_10231563813060391_9151321643853820111_n.jpg";
// Salon gallery photos (user approved)
const SALON_EXTERIOR = "https://customer-assets.emergentagent.com/job_a05a9fc6-c017-4f4a-aee2-38e140acfa26/artifacts/dadmar03_image.png";
const SALON_RECEPTION = "https://customer-assets.emergentagent.com/job_a05a9fc6-c017-4f4a-aee2-38e140acfa26/artifacts/snwuwd2g_image.png";
const SALON_INTERIOR = "https://customer-assets.emergentagent.com/job_a05a9fc6-c017-4f4a-aee2-38e140acfa26/artifacts/owkrsi8u_image.png";
const SALON_WORKSTATIONS = "https://customer-assets.emergentagent.com/job_a05a9fc6-c017-4f4a-aee2-38e140acfa26/artifacts/t15b4lty_image.png";

const GALLERY = [
  { img: "https://customer-assets.emergentagent.com/job_a05a9fc6-c017-4f4a-aee2-38e140acfa26/artifacts/7i4kwza6_image.png", label: "Balayage Dorato", tag: "Capelli Lunghi" },
  { img: "https://customer-assets.emergentagent.com/job_a05a9fc6-c017-4f4a-aee2-38e140acfa26/artifacts/zjh4hvlw_image.png", label: "Bob Mosso", tag: "Capelli Corti" },
  { img: "https://customer-assets.emergentagent.com/job_a05a9fc6-c017-4f4a-aee2-38e140acfa26/artifacts/krhax3qv_image.png", label: "Onde Ramate", tag: "Colorazione" },
  { img: "https://customer-assets.emergentagent.com/job_a05a9fc6-c017-4f4a-aee2-38e140acfa26/artifacts/0w1uwqaq_image.png", label: "Sfumature Calde", tag: "Balayage" },
  { img: "https://customer-assets.emergentagent.com/job_a05a9fc6-c017-4f4a-aee2-38e140acfa26/artifacts/r41kjm40_image.png", label: "Styling in Salone", tag: "Taglio" },
  { img: "https://customer-assets.emergentagent.com/job_ac0aaacf-8266-485a-8bab-9e57ed904c7a/artifacts/0inxpacz_517029262_10231563813060391_9151321643853820111_n.jpg", label: "Onde Naturali", tag: "Piega" },
];

const SERVICE_CATEGORIES = [
  {
    title: "Taglio & Piega",
    items: [
      { name: "Taglio", price: "€ 10" },
      { name: "Piega Corti", price: "€ 10" },
      { name: "Piega Lunghi", price: "€ 12" },
      { name: "Piega Fantasy", price: "€ 15" },
      { name: "Piastra/Ferro", price: "+ € 3" },
    ]
  },
  {
    title: "Colorazione",
    desc: "Tutte le colorazioni sono senza ammoniaca, con cheratina e olio di argan",
    items: [
      { name: "Colorazione Parziale / Completa / Cuffia / Cartine / Balayage / Giochi di Colore", price: "Da € 30" },
    ]
  },
  {
    title: "Modellanti",
    items: [
      { name: "Permanente / Ondulazione / Anticrespo / Stiratura Classica", price: "Da € 40" },
    ]
  },
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
  const [showServices, setShowServices] = useState(false);
  const [step, setStep] = useState(1);
  const [services, setServices] = useState([]);
  const [operators, setOperators] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const servicesRef = useRef(null);
  const contactRef = useRef(null);

  const [formData, setFormData] = useState({
    client_name: '', client_phone: '', service_ids: [], operator_id: '',
    date: format(new Date(), 'yyyy-MM-dd'), time: '09:00', notes: ''
  });

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [servicesRes, operatorsRes] = await Promise.all([
        axios.get(`${API}/public/services`), axios.get(`${API}/public/operators`)
      ]);
      setServices(servicesRes.data); setOperators(operatorsRes.data);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const toggleService = (id) => {
    setFormData(prev => ({
      ...prev, service_ids: prev.service_ids.includes(id) ? prev.service_ids.filter(s => s !== id) : [...prev.service_ids, id]
    }));
  };

  const selectedServices = services.filter(s => formData.service_ids.includes(s.id));
  const totalPrice = selectedServices.reduce((sum, s) => sum + (s.price || 0), 0);
  const totalDuration = selectedServices.reduce((sum, s) => sum + (s.duration || 0), 0);

  const handleSubmit = async () => {
    if (!formData.client_name || !formData.client_phone) { toast.error('Inserisci nome e telefono'); return; }
    setSubmitting(true);
    try { await axios.post(`${API}/public/book-appointment`, formData); setSuccess(true); }
    catch (err) { toast.error(err.response?.data?.detail || 'Errore nella prenotazione'); }
    finally { setSubmitting(false); }
  };

  const scrollTo = (ref) => { ref.current?.scrollIntoView({ behavior: 'smooth' }); };
  const openWhatsApp = () => { window.open('https://wa.me/393397833526?text=Ciao, vorrei prenotare un appuntamento!', '_blank'); };

  // SUCCESS PAGE
  if (success) {
    return (
      <div className="min-h-screen bg-[#1a1a2e] flex items-center justify-center p-4">
        <Toaster position="top-center" />
        <div className="max-w-md w-full text-center">
          <CheckCircle className="w-20 h-20 mx-auto text-emerald-400 mb-6" />
          <h1 className="text-3xl font-black text-white mb-3">Prenotazione Confermata!</h1>
          <p className="text-gray-300 mb-2">Ti aspettiamo il <span className="text-white font-bold">{format(new Date(formData.date), 'd MMMM yyyy', { locale: it })}</span> alle <span className="text-white font-bold">{formData.time}</span></p>
          <p className="text-sm text-gray-500 mb-8">Riceverai un promemoria prima dell'appuntamento.</p>
          <Button onClick={() => { setSuccess(false); setShowBooking(false); setStep(1); setFormData({ client_name: '', client_phone: '', service_ids: [], operator_id: '', date: format(new Date(), 'yyyy-MM-dd'), time: '09:00', notes: '' }); }}
            className="bg-white text-[#1a1a2e] hover:bg-gray-200 font-bold px-8" data-testid="booking-back-home-btn">Torna alla Home</Button>
        </div>
      </div>
    );
  }

  // BOOKING FORM
  if (showBooking) {
    return (
      <div className="min-h-screen bg-[#1a1a2e]">
        <Toaster position="top-center" />
        <div className="bg-[#242445] border-b border-gray-800 py-4 px-4 sticky top-0 z-50">
          <div className="max-w-lg mx-auto flex items-center gap-3">
            <Button variant="ghost" size="icon" onClick={() => setShowBooking(false)} className="text-gray-400 hover:text-white hover:bg-white/10 shrink-0" data-testid="booking-back-btn">
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
        <div className="max-w-lg mx-auto px-4 py-6">
          <div className="flex items-center justify-center gap-2 mb-6">
            {[1, 2, 3].map(s => (
              <div key={s} className="flex items-center gap-2">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${step >= s ? 'bg-white text-[#1a1a2e]' : 'bg-gray-800 text-gray-500'}`}>
                  {step > s ? <CheckCircle className="w-4 h-4" /> : s}
                </div>
                {s < 3 && <div className={`w-12 h-0.5 ${step > s ? 'bg-white' : 'bg-gray-800'}`} />}
              </div>
            ))}
          </div>
          {step === 1 && (
            <div className="space-y-4">
              <h2 className="text-xl font-black text-white">Scegli i Servizi</h2>
              {loading ? <div className="flex justify-center py-8"><Clock className="w-6 h-6 text-gray-500 animate-spin" /></div> : (
                <div className="space-y-2">
                  {services.map(service => (
                    <div key={service.id} onClick={() => toggleService(service.id)}
                      className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${formData.service_ids.includes(service.id) ? 'border-white bg-white/10' : 'border-gray-800 bg-[#242445] hover:border-gray-600'}`}
                      data-testid={`service-item-${service.id}`}>
                      <div className="flex justify-between items-center">
                        <div><p className="font-bold text-white">{service.name}</p><p className="text-sm text-gray-500">{service.duration} min</p></div>
                        <p className="font-black text-white">{'\u20AC'}{service.price}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {formData.service_ids.length > 0 && (
                <div className="bg-[#242445] p-4 rounded-xl border border-gray-800">
                  <p className="font-bold text-white">Riepilogo: {totalDuration} min - {'\u20AC'}{totalPrice}</p>
                </div>
              )}
              <Button onClick={() => setStep(2)} disabled={formData.service_ids.length === 0} className="w-full bg-white text-[#1a1a2e] hover:bg-gray-200 font-bold py-6" data-testid="booking-step1-next">Continua <ArrowRight className="w-4 h-4 ml-2" /></Button>
            </div>
          )}
          {step === 2 && (
            <div className="space-y-4">
              <h2 className="text-xl font-black text-white">Data e Ora</h2>
              <div className="space-y-3">
                <div><label className="text-sm text-gray-400 font-semibold mb-1 block">Data</label>
                  <Input type="date" value={formData.date} min={format(new Date(), 'yyyy-MM-dd')} onChange={(e) => setFormData({...formData, date: e.target.value})} className="bg-[#242445] border-gray-800 text-white" /></div>
                <div><label className="text-sm text-gray-400 font-semibold mb-1 block">Ora</label>
                  <select value={formData.time} onChange={(e) => setFormData({...formData, time: e.target.value})} className="w-full p-3 bg-[#242445] border border-gray-800 rounded-lg text-white">
                    {TIME_SLOTS.map(t => <option key={t} value={t}>{t}</option>)}
                  </select></div>
                {operators.length > 0 && (
                  <div><label className="text-sm text-gray-400 font-semibold mb-1 block">Operatore (opzionale)</label>
                    <select value={formData.operator_id} onChange={(e) => setFormData({...formData, operator_id: e.target.value})} className="w-full p-3 bg-[#242445] border border-gray-800 rounded-lg text-white">
                      <option value="">Nessuna preferenza</option>
                      {operators.map(op => <option key={op.id} value={op.id}>{op.name}</option>)}
                    </select></div>
                )}
              </div>
              <div className="flex gap-3">
                <Button onClick={() => setStep(1)} variant="outline" className="flex-1 border-gray-700 text-gray-300 hover:bg-white/10">Indietro</Button>
                <Button onClick={() => setStep(3)} className="flex-1 bg-white text-[#1a1a2e] hover:bg-gray-200 font-bold" data-testid="booking-step2-next">Continua <ArrowRight className="w-4 h-4 ml-2" /></Button>
              </div>
            </div>
          )}
          {step === 3 && (
            <div className="space-y-4">
              <h2 className="text-xl font-black text-white">I Tuoi Dati</h2>
              <div className="space-y-3">
                <div><label className="text-sm text-gray-400 font-semibold mb-1 block">Nome e Cognome *</label>
                  <Input value={formData.client_name} onChange={(e) => setFormData({...formData, client_name: e.target.value})} placeholder="Es. Maria Rossi" className="bg-[#242445] border-gray-800 text-white placeholder:text-gray-600" data-testid="booking-name-input" /></div>
                <div><label className="text-sm text-gray-400 font-semibold mb-1 block">Telefono *</label>
                  <Input value={formData.client_phone} onChange={(e) => setFormData({...formData, client_phone: e.target.value})} placeholder="Es. 339 123 4567" className="bg-[#242445] border-gray-800 text-white placeholder:text-gray-600" data-testid="booking-phone-input" /></div>
                <div><label className="text-sm text-gray-400 font-semibold mb-1 block">Note (opzionale)</label>
                  <Textarea value={formData.notes} onChange={(e) => setFormData({...formData, notes: e.target.value})} placeholder="Richieste particolari..." className="bg-[#242445] border-gray-800 text-white placeholder:text-gray-600" rows={3} /></div>
              </div>
              <div className="bg-[#242445] p-4 rounded-xl border border-gray-800 space-y-2">
                <p className="text-sm text-gray-400">Riepilogo:</p>
                {selectedServices.map(s => (<div key={s.id} className="flex justify-between text-sm"><span className="text-gray-300">{s.name}</span><span className="text-white font-bold">{'\u20AC'}{s.price}</span></div>))}
                <div className="border-t border-gray-800 pt-2 flex justify-between"><span className="text-white font-bold">Totale</span><span className="text-white font-black text-lg">{'\u20AC'}{totalPrice}</span></div>
                <p className="text-xs text-gray-500">{format(new Date(formData.date), 'd MMMM yyyy', { locale: it })} alle {formData.time}</p>
              </div>
              <div className="flex gap-3">
                <Button onClick={() => setStep(2)} variant="outline" className="flex-1 border-gray-700 text-gray-300 hover:bg-white/10">Indietro</Button>
                <Button onClick={handleSubmit} disabled={submitting} className="flex-1 bg-white text-[#1a1a2e] hover:bg-gray-200 font-bold" data-testid="booking-submit-btn">
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
    <div className="min-h-screen bg-[#1a1a2e] text-white" data-testid="booking-welcome">
      <Toaster position="top-center" />

      {/* NAVBAR */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#1a1a2e]/90 backdrop-blur-md border-b border-amber-400/10">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/logo.png?v=3" alt="MBHS Salon" className="w-10 h-10 rounded-lg" />
            <span className="font-black text-sm sm:text-base tracking-tight">BRUNO MELITO HAIR</span>
          </div>
          <div className="hidden sm:flex items-center gap-6 text-sm text-gray-400">
            <button onClick={() => { setShowServices(true); setTimeout(() => scrollTo(servicesRef), 100); }} className="hover:text-white transition-colors">Servizi</button>
            <button onClick={() => scrollTo(contactRef)} className="hover:text-white transition-colors">Contatti</button>
          </div>
          <Button onClick={() => setShowBooking(true)} className="bg-white text-[#1a1a2e] hover:bg-gray-200 font-bold text-sm px-4 sm:px-6" data-testid="booking-start-btn">
            PRENOTA ORA
          </Button>
        </div>
      </nav>

      {/* HERO SECTION */}
      <section className="relative min-h-screen flex items-center pt-16">
        <div className="absolute inset-0">
          <img src={HERO_BG} alt="Bruno Melito Hair" className="w-full h-full object-cover opacity-30" />
          <div className="absolute inset-0 bg-gradient-to-b from-[#1a1a2e]/60 via-[#1a1a2e]/40 to-[#1a1a2e]" />
        </div>
        <div className="relative max-w-6xl mx-auto px-4 py-20 sm:py-32 w-full">
          <div className="text-center max-w-3xl mx-auto">
            {/* Artwork centered */}
            <div className="flex justify-center mb-8">
              <img src={HERO_ARTWORK} alt="Metti la testa a posto!!" className="w-64 h-64 sm:w-80 sm:h-80 lg:w-96 lg:h-96 object-contain drop-shadow-2xl" />
            </div>
            <div className="inline-block bg-white/10 backdrop-blur-sm text-white text-xs font-bold px-4 py-2 rounded-full border border-white/10 mb-6">
              SOLO PER APPUNTAMENTO
            </div>
            <p className="text-base sm:text-lg text-gray-300 max-w-lg mx-auto mb-8 leading-relaxed">
              Scopri l'eccellenza dell'hair styling al Bruno Melito Hair. Dove ogni taglio è un'opera d'arte e ogni cliente è unica.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center mb-10">
              <Button onClick={() => setShowBooking(true)} className="bg-white text-[#1a1a2e] hover:bg-gray-200 font-black text-base px-8 py-6 rounded-xl">
                <Scissors className="w-5 h-5 mr-2" /> PRENOTA ORA
              </Button>
              <Button onClick={() => { setShowServices(true); setTimeout(() => scrollTo(servicesRef), 100); }} variant="outline" className="border-white/20 text-white hover:bg-white/10 font-bold text-base px-8 py-6 rounded-xl">
                Scopri i Servizi <ChevronDown className="w-4 h-4 ml-2" />
              </Button>
            </div>
            {/* Contact quick links */}
            <div className="flex flex-col sm:flex-row gap-4 text-sm justify-center">
              <a href="tel:08231878320" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors justify-center">
                <Phone className="w-4 h-4" /> 0823 18 78 320
              </a>
              <a href="tel:3397833526" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors justify-center">
                <Phone className="w-4 h-4" /> 339 78 33 526
              </a>
              <a href="https://maps.google.com/?q=Via+Vito+Nicola+Melorio+101+Santa+Maria+Capua+Vetere" target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors justify-center">
                <MapPin className="w-4 h-4" /> Via Vito Nicola Melorio 101, S.M.C.V.
              </a>
            </div>
          </div>
          {/* Experience badge */}
          <div className="absolute right-4 sm:right-8 bottom-20 sm:bottom-32 bg-white/5 backdrop-blur-md border border-rose-400/30 rounded-3xl p-5 text-center hidden md:block">
            <p className="text-4xl font-black text-rose-300">40+</p>
            <p className="text-xs text-gray-400 font-semibold">Anni di<br />Esperienza</p>
            <p className="text-[10px] text-gray-600 mt-1">Dal 1983</p>
          </div>
        </div>
      </section>

      {/* SERVICES SECTION - Collapsible */}
      <section ref={servicesRef} className="py-20 sm:py-28 relative">
        <div className="max-w-6xl mx-auto px-4">
          <button onClick={() => setShowServices(!showServices)} className="w-full text-center mb-4 group">
            <p className="text-amber-400 font-bold text-sm tracking-widest uppercase mb-3">I Nostri Servizi</p>
            <h2 className="text-3xl sm:text-4xl font-black">Servizi Professionali</h2>
            <p className="text-gray-500 mt-3 max-w-xl mx-auto">Dal taglio classico alle tecniche più innovative.</p>
            <div className="flex items-center justify-center gap-2 text-amber-400 font-bold mt-4">
              {showServices ? <><span>Nascondi listino</span><ChevronUp className="w-5 h-5" /></> : <><span>Mostra listino</span><ChevronDown className="w-5 h-5" /></>}
            </div>
          </button>

          {showServices && (
            <div className="space-y-6 mt-8 animate-in fade-in duration-300">
              {SERVICE_CATEGORIES.map((cat, idx) => {
                const borderColors = ['border-amber-400/30', 'border-rose-400/30', 'border-teal-400/30'];
                return (
                <div key={idx} className={`bg-[#242445]/80 border ${borderColors[idx % 3]} rounded-3xl p-6`}>
                  <h3 className="text-xl font-black text-white mb-1">{cat.title}</h3>
                  {cat.desc && <p className="text-sm text-gray-400 mb-4">{cat.desc}</p>}
                  <div className="space-y-3">
                    {cat.items.map((item, i) => (
                      <div key={i} className="flex justify-between items-center py-2 border-b border-white/5 last:border-0">
                        <span className="font-bold text-gray-300">{item.name}</span>
                        <span className="font-black text-amber-400 text-lg shrink-0 ml-4">{item.price}</span>
                      </div>
                    ))}
                  </div>
                </div>
                );
              })}
              <div className="text-center">
                <p className="text-gray-600 text-sm mb-6">Tutti i servizi includono consulenza personalizzata e prodotti professionali.</p>
                <Button onClick={() => setShowBooking(true)} className="bg-white text-[#1a1a2e] hover:bg-gray-200 font-bold px-8 py-6 rounded-xl">
                  <Scissors className="w-4 h-4 mr-2" /> PRENOTA ORA
                </Button>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* SALON GALLERY */}
      <section className="py-20 sm:py-28 bg-[#242445]">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-12">
            <p className="text-amber-400 font-bold text-sm tracking-widest uppercase mb-3">Il Nostro Salone</p>
            <h2 className="text-3xl sm:text-4xl font-black">Dove Nasce la Bellezza</h2>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { img: SALON_EXTERIOR, label: "Esterno", border: "border-amber-400/30" },
              { img: SALON_RECEPTION, label: "Reception", border: "border-rose-400/30" },
              { img: SALON_INTERIOR, label: "Area Colore", border: "border-teal-400/30" },
              { img: SALON_WORKSTATIONS, label: "Postazioni", border: "border-violet-400/30" },
            ].map((item, idx) => (
              <div key={idx} className={`relative rounded-3xl overflow-hidden aspect-square group border-2 ${item.border}`}>
                <img src={item.img} alt={item.label} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
                <p className="absolute bottom-3 left-3 text-white font-bold text-sm">{item.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ABOUT SECTION */}
      <section className="py-20 sm:py-28">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="rounded-2xl overflow-hidden h-80 lg:h-96">
              <img src={SALON_RECEPTION} alt="Il nostro salone" className="w-full h-full object-cover" />
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

      {/* REVIEWS */}
      <section className="py-20 sm:py-28">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-12">
            <p className="text-amber-400 font-bold text-sm tracking-widest uppercase mb-3">Recensioni</p>
            <h2 className="text-3xl sm:text-4xl font-black">Cosa Dicono di Noi</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {REVIEWS.map((review, idx) => (
              <div key={idx} className="bg-[#242445] border border-gray-800/50 rounded-3xl p-5">
                <div className="flex gap-0.5 mb-3">
                  {[...Array(review.rating)].map((_, i) => (<Star key={i} className="w-4 h-4 fill-amber-400 text-amber-400" />))}
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

      {/* HAIRSTYLE GALLERY */}
      <section className="py-20 sm:py-28 bg-[#242445]">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-12">
            <p className="text-amber-400 font-bold text-sm tracking-widest uppercase mb-3">Tendenze P/E 2026</p>
            <h2 className="text-3xl sm:text-4xl font-black">I Nostri Lavori</h2>
            <p className="text-gray-500 mt-3 max-w-xl mx-auto">Lasciati ispirare dalle ultime tendenze Primavera Estate 2026.</p>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
            {GALLERY.map((item, idx) => (
              <div key={idx} className="relative rounded-2xl overflow-hidden aspect-[3/4] group cursor-pointer">
                <img src={item.img} alt={item.label} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <div className="absolute top-3 right-3 bg-white/10 backdrop-blur-md text-white text-xs font-bold px-3 py-1 rounded-full border border-white/10">
                  {item.tag}
                </div>
                <div className="absolute bottom-0 left-0 right-0 p-4 translate-y-full group-hover:translate-y-0 transition-transform duration-300">
                  <p className="text-white font-bold">{item.label}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="text-center mt-8">
            <Button onClick={() => setShowBooking(true)} className="bg-white text-[#1a1a2e] hover:bg-gray-200 font-bold px-8 py-6 rounded-xl">
              <Scissors className="w-4 h-4 mr-2" /> PRENOTA ORA
            </Button>
          </div>
        </div>
      </section>

      {/* CONTACT SECTION */}
      <section ref={contactRef} className="py-20 sm:py-28">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-12">
            <p className="text-amber-400 font-bold text-sm tracking-widest uppercase mb-3">Contattaci</p>
            <h2 className="text-3xl sm:text-4xl font-black">Prenota il Tuo Appuntamento</h2>
            <p className="text-gray-500 mt-3">Siamo pronti ad accoglierti nel nostro salone.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
            <a href="https://maps.google.com/?q=Via+Vito+Nicola+Melorio+101+Santa+Maria+Capua+Vetere" target="_blank" rel="noopener noreferrer"
              className="bg-[#242445] border border-gray-800/50 rounded-3xl p-5 hover:border-gray-700 transition-colors text-center" data-testid="contact-address">
              <MapPin className="w-6 h-6 text-amber-400 mx-auto mb-3" />
              <h3 className="font-bold text-white text-sm mb-1">Indirizzo</h3>
              <p className="text-gray-500 text-xs leading-relaxed">Via Vito Nicola Melorio 101<br />Santa Maria Capua Vetere (CE)</p>
            </a>
            <div className="bg-[#242445] border border-gray-800/50 rounded-3xl p-5 text-center">
              <Phone className="w-6 h-6 text-amber-400 mx-auto mb-3" />
              <h3 className="font-bold text-white text-sm mb-1">Telefono</h3>
              <a href="tel:08231878320" className="text-gray-400 text-xs hover:text-white transition-colors block">0823 18 78 320</a>
              <a href="tel:3397833526" className="text-gray-400 text-xs hover:text-white transition-colors block mt-1">339 78 33 526</a>
            </div>
            <a href="mailto:melitobruno@gmail.com" className="bg-[#242445] border border-gray-800/50 rounded-3xl p-5 hover:border-gray-700 transition-colors text-center">
              <Mail className="w-6 h-6 text-amber-400 mx-auto mb-3" />
              <h3 className="font-bold text-white text-sm mb-1">Email</h3>
              <p className="text-gray-400 text-xs">melitobruno@gmail.com</p>
            </a>
            <div className="bg-[#242445] border border-gray-800/50 rounded-3xl p-5 text-center">
              <Clock className="w-6 h-6 text-amber-400 mx-auto mb-3" />
              <h3 className="font-bold text-white text-sm mb-1">Orari</h3>
              <p className="text-gray-400 text-xs">Mar - Sab: 08:00 - 19:00</p>
              <p className="text-gray-600 text-xs mt-1">Dom - Lun: Chiuso</p>
            </div>
          </div>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button onClick={() => setShowBooking(true)} className="bg-white text-[#1a1a2e] hover:bg-gray-200 font-black text-base px-10 py-6 rounded-xl w-full sm:w-auto" data-testid="contact-book-btn">
              <Scissors className="w-5 h-5 mr-2" /> PRENOTA ORA
            </Button>
            <Button onClick={openWhatsApp} className="bg-[#25D366] hover:bg-[#20bd5a] text-white font-bold text-base px-10 py-6 rounded-xl w-full sm:w-auto" data-testid="contact-whatsapp-btn">
              <MessageSquare className="w-5 h-5 mr-2" /> WHATSAPP
            </Button>
            <a href="tel:08231878320" className="w-full sm:w-auto">
              <Button variant="outline" className="border-gray-700 text-gray-300 hover:bg-white/10 font-bold text-base px-10 py-6 rounded-xl w-full" data-testid="contact-call-btn">
                <Phone className="w-5 h-5 mr-2" /> CHIAMA
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
          <p className="text-gray-800 text-xs mt-4">&copy; {new Date().getFullYear()} Bruno Melito Hair. Tutti i diritti riservati.</p>
        </div>
      </footer>

      {/* Fixed bottom CTA on mobile */}
      <div className="fixed bottom-0 left-0 right-0 p-3 bg-[#1a1a2e]/95 backdrop-blur-md border-t border-white/5 sm:hidden z-50">
        <Button onClick={() => setShowBooking(true)} className="w-full bg-white text-[#1a1a2e] hover:bg-gray-200 font-black py-5 rounded-xl" data-testid="mobile-book-btn">
          <Scissors className="w-5 h-5 mr-2" /> PRENOTA ORA
        </Button>
      </div>
    </div>
  );
}
