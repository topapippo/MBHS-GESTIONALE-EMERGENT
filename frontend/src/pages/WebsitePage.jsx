import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Clock, Scissors, CheckCircle, ArrowLeft, MapPin, Phone, Mail, Star, MessageSquare, ChevronDown, ChevronUp, ArrowRight, Instagram, Facebook, Globe, Youtube } from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { toast, Toaster } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SOCIAL_LINKS = [
  { url: 'https://www.instagram.com/brunomelitohair', icon: Instagram, label: 'Instagram', color: 'hover:text-pink-400' },
  { url: 'https://www.facebook.com/brunomelitohair', icon: Facebook, label: 'Facebook', color: 'hover:text-blue-400' },
  { url: 'https://www.youtube.com/@brunomelit', icon: Youtube, label: 'YouTube', color: 'hover:text-red-400' },
  { url: 'https://www.facebook.com/brunomelitoparrucchierimettilatestaaposto1983', icon: Facebook, label: 'Facebook Page', color: 'hover:text-blue-400' },
  { url: 'https://style-maestro-5.preview.emergentagent.com', icon: Globe, label: 'Sito Web', color: 'hover:text-teal-400' },
];

const TIME_SLOTS = [];
for (let h = 8; h <= 20; h++) {
  for (let m = 0; m < 60; m += 15) {
    TIME_SLOTS.push(`${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`);
  }
}

const BORDER_COLORS = ['border-amber-400/30', 'border-rose-400/30', 'border-teal-400/30', 'border-violet-400/30', 'border-sky-400/30', 'border-orange-400/30'];
const GLOW_COLORS = ['hover:shadow-amber-400/20', 'hover:shadow-rose-400/20', 'hover:shadow-teal-400/20', 'hover:shadow-violet-400/20', 'hover:shadow-sky-400/20', 'hover:shadow-orange-400/20'];
const AVATAR_BGS = ['bg-amber-400/15', 'bg-rose-400/15', 'bg-teal-400/15', 'bg-violet-400/15'];
const AVATAR_TEXTS = ['text-amber-400', 'text-rose-400', 'text-teal-400', 'text-violet-400'];

export default function WebsitePage() {
  const [siteData, setSiteData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showBooking, setShowBooking] = useState(false);
  const [showServices, setShowServices] = useState(false);
  const [step, setStep] = useState(1);
  const [bookingServices, setBookingServices] = useState([]);
  const [operators, setOperators] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const servicesRef = useRef(null);
  const contactRef = useRef(null);

  const [formData, setFormData] = useState({
    client_name: '', client_phone: '', service_ids: [], operator_id: '',
    date: format(new Date(), 'yyyy-MM-dd'), time: '09:00', notes: ''
  });

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [siteRes, opsRes, svcRes] = await Promise.all([
          axios.get(`${API}/public/website`),
          axios.get(`${API}/public/operators`).catch(() => ({ data: [] })),
          axios.get(`${API}/public/services`).catch(() => ({ data: [] }))
        ]);
        setSiteData(siteRes.data);
        setOperators(opsRes.data);
        setBookingServices(svcRes.data);
      } catch (err) { console.error(err); }
      finally { setLoading(false); }
    };
    fetchAll();
  }, []);

  const config = siteData?.config || {};
  const reviews = siteData?.reviews || [];
  const gallery = siteData?.gallery || [];
  const salonPhotos = gallery.filter(g => g.section === 'salon');
  const hairstylePhotos = gallery.filter(g => g.section === 'gallery');

  const toggleService = (id) => {
    setFormData(prev => ({
      ...prev, service_ids: prev.service_ids.includes(id) ? prev.service_ids.filter(s => s !== id) : [...prev.service_ids, id]
    }));
  };
  const selectedServices = bookingServices.filter(s => formData.service_ids.includes(s.id));
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
  const openWhatsApp = () => {
    const num = config.whatsapp || '393397833526';
    window.open(`https://wa.me/${num}?text=Ciao, vorrei prenotare un appuntamento!`, '_blank');
  };

  const getImageUrl = (item) => {
    if (!item?.image_url) return '';
    if (item.image_url.startsWith('http')) return item.image_url;
    return `${process.env.REACT_APP_BACKEND_URL}${item.image_url}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#1a1a2e] flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-amber-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

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
            className="bg-white text-[#1a1a2e] hover:bg-gray-200 font-bold px-8" data-testid="website-back-home-btn">Torna alla Home</Button>
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
            <Button variant="ghost" size="icon" onClick={() => setShowBooking(false)} className="text-gray-400 hover:text-white hover:bg-white/10 shrink-0" data-testid="website-booking-back-btn">
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div className="flex items-center gap-3">
              <img src="/logo.png?v=3" alt={config.salon_name} className="w-9 h-9 rounded-lg" />
              <div>
                <h1 className="text-white text-sm font-black leading-tight">{config.salon_name || 'BRUNO MELITO HAIR'}</h1>
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
              <div className="space-y-2">
                {bookingServices.map(service => (
                  <div key={service.id} onClick={() => toggleService(service.id)}
                    className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${formData.service_ids.includes(service.id) ? 'border-white bg-white/10' : 'border-gray-800 bg-[#242445] hover:border-gray-600'}`}
                    data-testid={`website-service-${service.id}`}>
                    <div className="flex justify-between items-center">
                      <div><p className="font-bold text-white">{service.name}</p><p className="text-sm text-gray-500">{service.duration} min</p></div>
                      <p className="font-black text-white">{'\u20AC'}{service.price}</p>
                    </div>
                  </div>
                ))}
              </div>
              {formData.service_ids.length > 0 && (
                <div className="bg-[#242445] p-4 rounded-xl border border-gray-800">
                  <p className="font-bold text-white">Riepilogo: {totalDuration} min - {'\u20AC'}{totalPrice}</p>
                </div>
              )}
              <Button onClick={() => setStep(2)} disabled={formData.service_ids.length === 0} className="w-full bg-white text-[#1a1a2e] hover:bg-gray-200 font-bold py-6" data-testid="website-step1-next">Continua <ArrowRight className="w-4 h-4 ml-2" /></Button>
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
                <Button onClick={() => setStep(3)} className="flex-1 bg-white text-[#1a1a2e] hover:bg-gray-200 font-bold" data-testid="website-step2-next">Continua <ArrowRight className="w-4 h-4 ml-2" /></Button>
              </div>
            </div>
          )}
          {step === 3 && (
            <div className="space-y-4">
              <h2 className="text-xl font-black text-white">I Tuoi Dati</h2>
              <div className="space-y-3">
                <div><label className="text-sm text-gray-400 font-semibold mb-1 block">Nome e Cognome *</label>
                  <Input value={formData.client_name} onChange={(e) => setFormData({...formData, client_name: e.target.value})} placeholder="Es. Maria Rossi" className="bg-[#242445] border-gray-800 text-white placeholder:text-gray-600" data-testid="website-booking-name" /></div>
                <div><label className="text-sm text-gray-400 font-semibold mb-1 block">Telefono *</label>
                  <Input value={formData.client_phone} onChange={(e) => setFormData({...formData, client_phone: e.target.value})} placeholder="Es. 339 123 4567" className="bg-[#242445] border-gray-800 text-white placeholder:text-gray-600" data-testid="website-booking-phone" /></div>
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
                <Button onClick={handleSubmit} disabled={submitting} className="flex-1 bg-white text-[#1a1a2e] hover:bg-gray-200 font-bold" data-testid="website-submit-btn">
                  {submitting ? <Clock className="w-4 h-4 animate-spin" /> : 'Conferma Prenotazione'}
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // ==================== WEBSITE LANDING PAGE ====================
  const serviceCategories = config.service_categories || [];
  const hours = config.hours || {};
  const phones = config.phones || [];

  return (
    <div className="min-h-screen bg-[#1a1a2e] text-white" data-testid="website-landing">
      <Toaster position="top-center" />

      {/* NAVBAR */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#1a1a2e]/90 backdrop-blur-md border-b border-amber-400/10">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/logo.png?v=3" alt={config.salon_name} className="w-10 h-10 rounded-lg" />
            <span className="font-black text-sm sm:text-base tracking-tight">{config.salon_name || 'BRUNO MELITO HAIR'}</span>
          </div>
          <div className="hidden sm:flex items-center gap-6 text-sm text-gray-400">
            <button onClick={() => { setShowServices(true); setTimeout(() => scrollTo(servicesRef), 100); }} className="hover:text-white transition-colors">Servizi</button>
            <button onClick={() => scrollTo(contactRef)} className="hover:text-white transition-colors">Contatti</button>
            <div className="flex items-center gap-3 border-l border-gray-700 pl-4">
              {SOCIAL_LINKS.map((link, i) => (
                <a key={i} href={link.url} target="_blank" rel="noopener noreferrer" className={`text-gray-500 ${link.color} transition-colors`} title={link.label}>
                  <link.icon className="w-4 h-4" />
                </a>
              ))}
            </div>
            <a href="/login" className="hover:text-white transition-colors">Area Riservata</a>
          </div>
          <Button onClick={() => setShowBooking(true)} className="bg-white text-[#1a1a2e] hover:bg-gray-200 font-bold text-sm px-4 sm:px-6" data-testid="website-book-btn">
            PRENOTA ORA
          </Button>
        </div>
      </nav>

      {/* HERO */}
      <section className="relative min-h-screen flex items-center pt-16">
        <div className="absolute inset-0">
          {salonPhotos.length > 0 ? (
            <img src={getImageUrl(salonPhotos[0])} alt={config.salon_name} className="w-full h-full object-cover opacity-30" />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-[#1a1a2e] to-[#242445]" />
          )}
          <div className="absolute inset-0 bg-gradient-to-b from-[#1a1a2e]/60 via-[#1a1a2e]/40 to-[#1a1a2e]" />
        </div>
        <div className="relative max-w-6xl mx-auto px-4 py-20 sm:py-32 w-full">
          <div className="text-center max-w-3xl mx-auto">
            <div className="flex justify-center mb-8">
              <img src="/logo.png?v=3" alt={config.salon_name} className="w-48 h-48 sm:w-64 sm:h-64 object-contain drop-shadow-2xl rounded-2xl" />
            </div>
            <div className="inline-block bg-white/10 backdrop-blur-sm text-white text-xs font-bold px-4 py-2 rounded-full border border-amber-400/20 mb-6">
              {config.subtitle || 'SOLO PER APPUNTAMENTO'}
            </div>
            <p className="text-base sm:text-lg text-gray-300 max-w-lg mx-auto mb-8 leading-relaxed">
              {config.hero_description || ''}
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center mb-10">
              <Button onClick={() => setShowBooking(true)} className="bg-white text-[#1a1a2e] hover:bg-gray-200 font-black text-base px-8 py-6 rounded-xl" data-testid="website-hero-book-btn">
                <Scissors className="w-5 h-5 mr-2" /> PRENOTA ORA
              </Button>
              <Button onClick={() => { setShowServices(true); setTimeout(() => scrollTo(servicesRef), 100); }} variant="outline" className="border-white/20 text-white hover:bg-white/10 font-bold text-base px-8 py-6 rounded-xl">
                Scopri i Servizi <ChevronDown className="w-4 h-4 ml-2" />
              </Button>
            </div>
            <div className="flex flex-col sm:flex-row gap-4 text-sm justify-center">
              {phones.map((p, i) => (
                <a key={i} href={`tel:${p.replace(/\s/g, '')}`} className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors justify-center">
                  <Phone className="w-4 h-4" /> {p}
                </a>
              ))}
              {config.address && (
                <a href={config.maps_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors justify-center">
                  <MapPin className="w-4 h-4" /> {config.address}
                </a>
              )}
            </div>
          </div>
          {config.years_experience && (
            <div className="absolute right-4 sm:right-8 bottom-20 sm:bottom-32 bg-white/5 backdrop-blur-md border border-rose-400/30 rounded-3xl p-5 text-center hidden md:block hover:shadow-lg hover:shadow-rose-400/20 transition-all duration-300">
              <p className="text-4xl font-black text-rose-300">{config.years_experience}</p>
              <p className="text-xs text-gray-400 font-semibold">Anni di<br />Esperienza</p>
              {config.year_founded && <p className="text-[10px] text-gray-600 mt-1">Dal {config.year_founded}</p>}
            </div>
          )}
        </div>
      </section>

      {/* SERVICES */}
      {serviceCategories.length > 0 && (
        <section ref={servicesRef} className="py-20 sm:py-28 relative">
          <div className="max-w-6xl mx-auto px-4">
            <button onClick={() => setShowServices(!showServices)} className="w-full text-center mb-4 group">
              <p className="text-amber-400 font-bold text-sm tracking-widest uppercase mb-3">I Nostri Servizi</p>
              <h2 className="text-3xl sm:text-4xl font-black">Servizi Professionali</h2>
              <div className="flex items-center justify-center gap-2 text-amber-400 font-bold mt-4">
                {showServices ? <><span>Nascondi listino</span><ChevronUp className="w-5 h-5" /></> : <><span>Mostra listino</span><ChevronDown className="w-5 h-5" /></>}
              </div>
            </button>
            {showServices && (
              <div className="space-y-6 mt-8 animate-in fade-in duration-300">
                {serviceCategories.map((cat, idx) => (
                  <div key={idx} className={`bg-[#242445]/80 border ${BORDER_COLORS[idx % 3]} rounded-3xl p-6 transition-all duration-300 hover:shadow-lg ${GLOW_COLORS[idx % 3]} hover:border-opacity-60 hover:scale-[1.01]`}>
                    <h3 className="text-xl font-black text-white mb-1">{cat.title}</h3>
                    {cat.desc && <p className="text-sm text-gray-400 mb-4">{cat.desc}</p>}
                    <div className="space-y-3">
                      {(cat.items || []).map((item, i) => (
                        <div key={i} className="flex justify-between items-center py-2 border-b border-white/5 last:border-0">
                          <span className="font-bold text-gray-300">{item.name}</span>
                          <span className="font-black text-amber-400 text-lg shrink-0 ml-4">{'\u20AC'} {item.price}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
                <div className="text-center">
                  <Button onClick={() => setShowBooking(true)} className="bg-white text-[#1a1a2e] hover:bg-gray-200 font-bold px-8 py-6 rounded-xl">
                    <Scissors className="w-4 h-4 mr-2" /> PRENOTA ORA
                  </Button>
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* SALON GALLERY */}
      {salonPhotos.length > 0 && (
        <section className="py-20 sm:py-28 bg-[#242445]">
          <div className="max-w-6xl mx-auto px-4">
            <div className="text-center mb-12">
              <p className="text-amber-400 font-bold text-sm tracking-widest uppercase mb-3">Il Nostro Salone</p>
              <h2 className="text-3xl sm:text-4xl font-black">Dove Nasce la Bellezza</h2>
            </div>
            <div className={`grid gap-4 ${salonPhotos.length === 1 ? 'grid-cols-1 max-w-lg mx-auto' : salonPhotos.length === 2 ? 'grid-cols-2' : salonPhotos.length === 3 ? 'grid-cols-3' : 'grid-cols-2 lg:grid-cols-4'}`}>
              {salonPhotos.map((item, idx) => (
                <div key={item.id} className={`relative rounded-3xl overflow-hidden aspect-square group border-2 ${BORDER_COLORS[idx % 6]} transition-all duration-300 hover:shadow-xl ${GLOW_COLORS[idx % 6]} hover:border-opacity-60`}>
                  <img src={getImageUrl(item)} alt={item.label} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
                  {item.label && <p className="absolute bottom-3 left-3 text-white font-bold text-sm">{item.label}</p>}
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ABOUT */}
      {config.about_title && (
        <section className="py-20 sm:py-28">
          <div className="max-w-6xl mx-auto px-4">
            <div className={`grid grid-cols-1 ${salonPhotos.length > 1 ? 'lg:grid-cols-2' : ''} gap-12 items-center`}>
              {salonPhotos.length > 1 && (
                <div className="rounded-3xl overflow-hidden h-80 lg:h-96 border-2 border-rose-400/20 hover:shadow-xl hover:shadow-rose-400/20 transition-all duration-300">
                  <img src={getImageUrl(salonPhotos[1] || salonPhotos[0])} alt="Il nostro salone" className="w-full h-full object-cover" />
                </div>
              )}
              <div>
                <p className="text-rose-400 font-bold text-sm tracking-widest uppercase mb-3">Chi Siamo</p>
                <h2 className="text-3xl sm:text-4xl font-black mb-6">{config.about_title}</h2>
                {config.about_text && <p className="text-gray-400 leading-relaxed mb-6">{config.about_text}</p>}
                {config.about_text_2 && <p className="text-gray-400 leading-relaxed mb-8">{config.about_text_2}</p>}
                {config.about_features && config.about_features.length > 0 && (
                  <div className="grid grid-cols-2 gap-3">
                    {config.about_features.map((item, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-teal-400 shrink-0" />
                        <span className="text-sm text-gray-300">{item}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* REVIEWS */}
      {reviews.length > 0 && (
        <section className="py-20 sm:py-28">
          <div className="max-w-6xl mx-auto px-4">
            <div className="text-center mb-12">
              <p className="text-teal-400 font-bold text-sm tracking-widest uppercase mb-3">Recensioni</p>
              <h2 className="text-3xl sm:text-4xl font-black">Cosa Dicono di Noi</h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {reviews.map((review, idx) => (
                <div key={review.id || idx} className={`bg-[#242445]/80 border ${BORDER_COLORS[idx % 4]} rounded-3xl p-5 transition-all duration-300 hover:shadow-lg ${GLOW_COLORS[idx % 4]} hover:border-opacity-60 hover:scale-[1.02]`}>
                  <div className="flex gap-0.5 mb-3">
                    {[...Array(review.rating || 5)].map((_, i) => (<Star key={i} className="w-4 h-4 fill-amber-400 text-amber-400" />))}
                  </div>
                  <p className="text-gray-300 text-sm leading-relaxed mb-4">"{review.text}"</p>
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 ${AVATAR_BGS[idx % 4]} rounded-full flex items-center justify-center`}>
                      <span className={`${AVATAR_TEXTS[idx % 4]} font-bold text-sm`}>{(review.name || '?')[0]}</span>
                    </div>
                    <span className="text-sm text-gray-400 font-semibold">{review.name}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* HAIRSTYLE GALLERY */}
      {hairstylePhotos.length > 0 && (
        <section className="py-20 sm:py-28 bg-[#242445]">
          <div className="max-w-6xl mx-auto px-4">
            <div className="text-center mb-12">
              <p className="text-rose-400 font-bold text-sm tracking-widest uppercase mb-3">{config.gallery_title || 'I Nostri Lavori'}</p>
              <h2 className="text-3xl sm:text-4xl font-black">I Nostri Lavori</h2>
              {config.gallery_subtitle && <p className="text-gray-500 mt-3 max-w-xl mx-auto">{config.gallery_subtitle}</p>}
            </div>
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
              {hairstylePhotos.map((item, idx) => (
                <div key={item.id} className={`relative rounded-3xl overflow-hidden aspect-[3/4] group cursor-pointer border-2 ${BORDER_COLORS[idx % 6]} transition-all duration-300 hover:shadow-xl ${GLOW_COLORS[idx % 6]} hover:border-opacity-60`}>
                  <img src={getImageUrl(item)} alt={item.label} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  {item.tag && (
                    <div className="absolute top-3 right-3 bg-white/10 backdrop-blur-md text-white text-xs font-bold px-3 py-1 rounded-full border border-white/10">
                      {item.tag}
                    </div>
                  )}
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
      )}

      {/* CONTACT */}
      <section ref={contactRef} className="py-20 sm:py-28">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-12">
            <p className="text-violet-400 font-bold text-sm tracking-widest uppercase mb-3">Contattaci</p>
            <h2 className="text-3xl sm:text-4xl font-black">Prenota il Tuo Appuntamento</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
            {config.address && (
              <a href={config.maps_url} target="_blank" rel="noopener noreferrer" className="bg-[#242445]/80 border border-amber-400/25 rounded-3xl p-5 hover:border-amber-400/50 hover:shadow-lg hover:shadow-amber-400/20 transition-all duration-300 text-center" data-testid="website-contact-address">
                <MapPin className="w-6 h-6 text-amber-400 mx-auto mb-3" />
                <h3 className="font-bold text-white text-sm mb-1">Indirizzo</h3>
                <p className="text-gray-400 text-xs leading-relaxed">{config.address}</p>
              </a>
            )}
            {phones.length > 0 && (
              <div className="bg-[#242445]/80 border border-rose-400/25 rounded-3xl p-5 text-center hover:shadow-lg hover:shadow-rose-400/20 transition-all duration-300">
                <Phone className="w-6 h-6 text-rose-400 mx-auto mb-3" />
                <h3 className="font-bold text-white text-sm mb-1">Telefono</h3>
                {phones.map((p, i) => (
                  <a key={i} href={`tel:${p.replace(/\s/g, '')}`} className="text-gray-400 text-xs hover:text-white transition-colors block mt-1">{p}</a>
                ))}
              </div>
            )}
            {config.email && (
              <a href={`mailto:${config.email}`} className="bg-[#242445]/80 border border-teal-400/25 rounded-3xl p-5 hover:border-teal-400/50 hover:shadow-lg hover:shadow-teal-400/20 transition-all duration-300 text-center">
                <Mail className="w-6 h-6 text-teal-400 mx-auto mb-3" />
                <h3 className="font-bold text-white text-sm mb-1">Email</h3>
                <p className="text-gray-400 text-xs">{config.email}</p>
              </a>
            )}
            <div className="bg-[#242445]/80 border border-violet-400/25 rounded-3xl p-5 text-center hover:shadow-lg hover:shadow-violet-400/20 transition-all duration-300">
              <Clock className="w-6 h-6 text-violet-400 mx-auto mb-3" />
              <h3 className="font-bold text-white text-sm mb-1">Orari</h3>
              {Object.entries(hours).filter(([, v]) => v !== 'Chiuso').length > 0 ? (
                <>
                  <p className="text-gray-400 text-xs">
                    {Object.entries(hours).filter(([, v]) => v !== 'Chiuso').map(([d]) => d.charAt(0).toUpperCase() + d.slice(1)).join(' - ')}
                  </p>
                  <p className="text-gray-400 text-xs">{Object.values(hours).find(v => v !== 'Chiuso')}</p>
                  <p className="text-gray-600 text-xs mt-1">
                    {Object.entries(hours).filter(([, v]) => v === 'Chiuso').map(([d]) => d.charAt(0).toUpperCase() + d.slice(1)).join(', ')}: Chiuso
                  </p>
                </>
              ) : (
                <p className="text-gray-400 text-xs">Mar - Sab: 08:00 - 19:00</p>
              )}
            </div>
          </div>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button onClick={() => setShowBooking(true)} className="bg-gradient-to-r from-amber-400 to-rose-400 text-[#1a1a2e] hover:from-amber-300 hover:to-rose-300 font-black text-base px-10 py-6 rounded-2xl w-full sm:w-auto shadow-lg shadow-amber-400/20" data-testid="website-contact-book-btn">
              <Scissors className="w-5 h-5 mr-2" /> PRENOTA ORA
            </Button>
            <Button onClick={openWhatsApp} className="bg-[#25D366] hover:bg-[#20bd5a] text-white font-bold text-base px-10 py-6 rounded-2xl w-full sm:w-auto shadow-lg shadow-green-400/20" data-testid="website-whatsapp-btn">
              <MessageSquare className="w-5 h-5 mr-2" /> WHATSAPP
            </Button>
            {phones.length > 0 && (
              <a href={`tel:${phones[0].replace(/\s/g, '')}`} className="w-full sm:w-auto">
                <Button variant="outline" className="border-rose-400/30 text-rose-300 hover:bg-rose-400/10 font-bold text-base px-10 py-6 rounded-2xl w-full" data-testid="website-call-btn">
                  <Phone className="w-5 h-5 mr-2" /> CHIAMA
                </Button>
              </a>
            )}
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="py-12 border-t border-amber-400/10">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex flex-col items-center gap-6">
            <img src="/logo.png?v=3" alt={config.salon_name} className="w-14 h-14 rounded-2xl border border-amber-400/20" />
            <p className="text-gray-400 text-sm font-bold">{config.salon_name || 'BRUNO MELITO HAIR'}</p>
            
            {/* Social Links */}
            <div className="flex items-center gap-4">
              {SOCIAL_LINKS.map((link, i) => (
                <a key={i} href={link.url} target="_blank" rel="noopener noreferrer"
                  className={`w-10 h-10 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-gray-500 ${link.color} transition-all hover:bg-white/10 hover:scale-110`}
                  title={link.label}>
                  <link.icon className="w-5 h-5" />
                </a>
              ))}
            </div>

            {/* Links */}
            <div className="flex items-center gap-6 text-sm text-gray-500">
              <a href="/prenota" className="hover:text-white transition-colors">Prenota Online</a>
              <a href="/sito" className="hover:text-white transition-colors">Sito Web</a>
              <a href={config.maps_url} target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">Come Raggiungerci</a>
            </div>

            <p className="text-gray-700 text-xs">{config.address}</p>
            <p className="text-gray-800 text-xs">&copy; {new Date().getFullYear()} {config.salon_name || 'Bruno Melito Hair'}. Tutti i diritti riservati.</p>
          </div>
        </div>
      </footer>

      {/* Fixed bottom CTA on mobile */}
      <div className="fixed bottom-0 left-0 right-0 p-3 bg-[#1a1a2e]/95 backdrop-blur-md border-t border-amber-400/10 sm:hidden z-50">
        <Button onClick={() => setShowBooking(true)} className="w-full bg-gradient-to-r from-amber-400 to-rose-400 text-[#1a1a2e] hover:from-amber-300 hover:to-rose-300 font-black py-5 rounded-2xl shadow-lg" data-testid="website-mobile-book-btn">
          <Scissors className="w-5 h-5 mr-2" /> PRENOTA ORA
        </Button>
      </div>
    </div>
  );
}
