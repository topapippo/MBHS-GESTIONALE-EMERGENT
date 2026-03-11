import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Switch } from '@/components/ui/switch';
import { Save, Plus, Trash2, Upload, Image, Star, Eye, Loader2, X, GripVertical, Palette, Type, Phone, ChevronUp, ChevronDown, Brush } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const DEFAULT_SECTIONS_ORDER = ['hero','services','salon_gallery','about','promotions','reviews','hairstyle_gallery','loyalty','contact'];

const SECTION_LABELS = {
  hero: '🏠 Hero / Intestazione',
  services: '✂️ Servizi & Listino',
  salon_gallery: '📸 Foto Salone',
  about: 'ℹ️ Chi Siamo',
  promotions: '🎁 Promozioni',
  reviews: '⭐ Recensioni',
  hairstyle_gallery: '💇 Gallery Lavori',
  loyalty: '🎯 Programma Fedeltà',
  contact: '📞 Contatti',
};

const COLOR_PRESETS = [
  { name: 'Azzurro (default)', primary: '#0EA5E9', accent: '#0284C7', bg: '#FFF8F0', text: '#1e293b' },
  { name: 'Oro & Nero', primary: '#F59E0B', accent: '#D97706', bg: '#111111', text: '#ffffff' },
  { name: 'Rosa Elegante', primary: '#EC4899', accent: '#DB2777', bg: '#FFF0F6', text: '#1e293b' },
  { name: 'Verde Smeraldo', primary: '#10B981', accent: '#059669', bg: '#F0FDF4', text: '#1e293b' },
  { name: 'Viola Lusso', primary: '#8B5CF6', accent: '#7C3AED', bg: '#FAF5FF', text: '#1e293b' },
  { name: 'Rosso Passione', primary: '#EF4444', accent: '#DC2626', bg: '#FFF5F5', text: '#1e293b' },
  { name: 'Turchese Mare', primary: '#06B6D4', accent: '#0891B2', bg: '#F0FDFF', text: '#1e293b' },
  { name: 'Arancio Caldo', primary: '#F97316', accent: '#EA580C', bg: '#FFF7ED', text: '#1e293b' },
];

export default function WebsiteAdminPage() {
  const [config, setConfig] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [gallery, setGallery] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [reviewDialog, setReviewDialog] = useState(false);
  const [editReview, setEditReview] = useState(null);
  const [reviewForm, setReviewForm] = useState({ name: '', text: '', rating: 5 });
  const [sectionsOrder, setSectionsOrder] = useState(DEFAULT_SECTIONS_ORDER);
  const [sectionsVisible, setSectionsVisible] = useState({ hero:true,services:true,salon_gallery:true,about:true,promotions:true,reviews:true,hairstyle_gallery:true,loyalty:true,contact:true });
  const [colors, setColors] = useState({ primary:'#0EA5E9', accent:'#0284C7', bg:'#FFF8F0', text:'#1e293b' });

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [configRes, reviewsRes, galleryRes] = await Promise.all([
        axios.get(`${API}/website/config`),
        axios.get(`${API}/website/reviews`),
        axios.get(`${API}/website/gallery`)
      ]);
      const cfg = configRes.data;
      setConfig(cfg);
      setReviews(reviewsRes.data);
      setGallery(galleryRes.data);
      if (cfg.sections_order) setSectionsOrder(cfg.sections_order);
      if (cfg.sections_visible) setSectionsVisible(sv => ({ ...sv, ...cfg.sections_visible }));
      if (cfg.colors) setColors(c => ({ ...c, ...cfg.colors }));
    } catch { toast.error('Errore caricamento'); }
    finally { setLoading(false); }
  };

  const saveConfig = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/website/config`, { ...config, sections_order: sectionsOrder, sections_visible: sectionsVisible, colors });
      toast.success('✅ Sito aggiornato! Le modifiche sono live.');
    } catch { toast.error('Errore nel salvataggio'); }
    finally { setSaving(false); }
  };

  const updateField = (field, value) => setConfig(prev => ({ ...prev, [field]: value }));

  const moveSectionUp = (idx) => { if (idx===0) return; const o=[...sectionsOrder]; [o[idx-1],o[idx]]=[o[idx],o[idx-1]]; setSectionsOrder(o); };
  const moveSectionDown = (idx) => { if (idx===sectionsOrder.length-1) return; const o=[...sectionsOrder]; [o[idx],o[idx+1]]=[o[idx+1],o[idx]]; setSectionsOrder(o); };
  const toggleSection = (key) => setSectionsVisible(prev => ({ ...prev, [key]: !prev[key] }));

  const openReviewDialog = (review=null) => {
    if (review) { setEditReview(review); setReviewForm({ name:review.name, text:review.text, rating:review.rating }); }
    else { setEditReview(null); setReviewForm({ name:'', text:'', rating:5 }); }
    setReviewDialog(true);
  };
  const saveReview = async () => {
    try {
      if (editReview) await axios.put(`${API}/website/reviews/${editReview.id}`, reviewForm);
      else await axios.post(`${API}/website/reviews`, reviewForm);
      setReviewDialog(false);
      const res = await axios.get(`${API}/website/reviews`);
      setReviews(res.data);
      toast.success('Recensione salvata!');
    } catch { toast.error('Errore'); }
  };
  const deleteReview = async (id) => {
    if (!window.confirm('Eliminare?')) return;
    await axios.delete(`${API}/website/reviews/${id}`);
    setReviews(prev => prev.filter(r => r.id !== id));
    toast.success('Eliminata');
  };

  const handleMediaUpload = async (e, section) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;
    setUploading(true);
    try {
      for (const file of files) {
        const fd = new FormData(); fd.append('file', file);
        const up = await axios.post(`${API}/website/upload`, fd, { headers:{'Content-Type':'multipart/form-data'} });
        await axios.post(`${API}/website/gallery`, { image_url:up.data.url, label:file.name.split('.')[0], tag:'', section, file_type:up.data.file_type||'image' });
      }
      const res = await axios.get(`${API}/website/gallery`);
      setGallery(res.data);
      toast.success(`${files.length} file caricati!`);
    } catch (err) { toast.error('Errore upload'); }
    finally { setUploading(false); e.target.value=''; }
  };
  const updateGalleryItem = async (id, field, value) => {
    await axios.put(`${API}/website/gallery/${id}`, { [field]:value });
    setGallery(prev => prev.map(g => g.id===id ? {...g,[field]:value} : g));
  };
  const deleteGalleryItem = async (id) => {
    if (!window.confirm('Eliminare?')) return;
    await axios.delete(`${API}/website/gallery/${id}`);
    setGallery(prev => prev.filter(g => g.id!==id));
    toast.success('Eliminato');
  };
  const getImageUrl = (item) => {
    if (!item?.image_url) return '';
    if (item.image_url.startsWith('http')) return item.image_url;
    return `${process.env.REACT_APP_BACKEND_URL}${item.image_url}`;
  };

  const updateCategory = (i,f,v) => { const c=[...(config.service_categories||[])]; c[i]={...c[i],[f]:v}; updateField('service_categories',c); };
  const updateCategoryItem = (ci,ii,f,v) => { const c=[...(config.service_categories||[])]; const it=[...(c[ci].items||[])]; it[ii]={...it[ii],[f]:v}; c[ci]={...c[ci],items:it}; updateField('service_categories',c); };
  const addCategoryItem = (ci) => { const c=[...(config.service_categories||[])]; c[ci]={...c[ci],items:[...(c[ci].items||[]),{name:'',price:''}]}; updateField('service_categories',c); };
  const removeCategoryItem = (ci,ii) => { const c=[...(config.service_categories||[])]; c[ci]={...c[ci],items:c[ci].items.filter((_,i)=>i!==ii)}; updateField('service_categories',c); };
  const addCategory = () => updateField('service_categories',[...(config.service_categories||[]),{title:'Nuova Categoria',desc:'',items:[]}]);
  const removeCategory = (i) => updateField('service_categories',(config.service_categories||[]).filter((_,idx)=>idx!==i));
  const moveCategoryUp = (i) => { if(i===0)return; const c=[...(config.service_categories||[])]; [c[i-1],c[i]]=[c[i],c[i-1]]; updateField('service_categories',c); };
  const moveCategoryDown = (i) => { const c=[...(config.service_categories||[])]; if(i===c.length-1)return; [c[i],c[i+1]]=[c[i+1],c[i]]; updateField('service_categories',c); };

  const updateHour = (day,v) => updateField('hours',{...(config.hours||{}),[day]:v});
  const updatePhone = (i,v) => { const p=[...(config.phones||[])]; p[i]=v; updateField('phones',p); };
  const addPhone = () => updateField('phones',[...(config.phones||[]),'']);
  const removePhone = (i) => updateField('phones',(config.phones||[]).filter((_,idx)=>idx!==i));
  const updateFeature = (i,v) => { const f=[...(config.about_features||[])]; f[i]=v; updateField('about_features',f); };
  const addFeature = () => updateField('about_features',[...(config.about_features||[]),'']);
  const removeFeature = (i) => updateField('about_features',(config.about_features||[]).filter((_,idx)=>idx!==i));

  if (loading) return <Layout><div className="flex items-center justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-[#0EA5E9]" /></div></Layout>;

  const salonPhotos = gallery.filter(g => g.section==='salon');
  const galleryPhotos = gallery.filter(g => g.section==='gallery');

  return (
    <Layout>
      <div className="space-y-6" data-testid="website-admin-page">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-[#0F172A]">🎨 Gestione Sito Web</h1>
            <p className="text-sm text-[#334155]">Controlla tutto il sito senza toccare il codice</p>
          </div>
          <div className="flex gap-2">
            <a href="/sito" target="_blank" rel="noopener noreferrer">
              <Button variant="outline" className="border-[#0EA5E9] text-[#0EA5E9]"><Eye className="w-4 h-4 mr-2" />Anteprima</Button>
            </a>
            <Button onClick={saveConfig} disabled={saving} className="bg-[#0EA5E9] hover:bg-[#0284C7] text-white">
              {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
              Salva & Pubblica
            </Button>
          </div>
        </div>

        <Tabs defaultValue="sections" className="space-y-4">
          <TabsList className="bg-white border shadow-sm flex-wrap h-auto gap-1 p-1">
            <TabsTrigger value="sections" className="data-[state=active]:bg-[#0EA5E9] data-[state=active]:text-white">📐 Sezioni</TabsTrigger>
            <TabsTrigger value="style" className="data-[state=active]:bg-[#0EA5E9] data-[state=active]:text-white"><Palette className="w-3 h-3 mr-1" />Stile</TabsTrigger>
            <TabsTrigger value="texts" className="data-[state=active]:bg-[#0EA5E9] data-[state=active]:text-white"><Type className="w-3 h-3 mr-1" />Testi</TabsTrigger>
            <TabsTrigger value="services" className="data-[state=active]:bg-[#0EA5E9] data-[state=active]:text-white">✂️ Servizi</TabsTrigger>
            <TabsTrigger value="photos" className="data-[state=active]:bg-[#0EA5E9] data-[state=active]:text-white">📸 Foto</TabsTrigger>
            <TabsTrigger value="gallery" className="data-[state=active]:bg-[#0EA5E9] data-[state=active]:text-white">💇 Gallery</TabsTrigger>
            <TabsTrigger value="reviews" className="data-[state=active]:bg-[#0EA5E9] data-[state=active]:text-white">⭐ Recensioni</TabsTrigger>
            <TabsTrigger value="contacts" className="data-[state=active]:bg-[#0EA5E9] data-[state=active]:text-white"><Phone className="w-3 h-3 mr-1" />Contatti</TabsTrigger>
          </TabsList>

          {/* SEZIONI */}
          <TabsContent value="sections">
            <Card>
              <CardHeader>
                <CardTitle>📐 Ordine e Visibilità Sezioni</CardTitle>
                <p className="text-sm text-gray-500">Usa le frecce per riordinare. Attiva/disattiva per mostrare o nascondere ogni sezione.</p>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {sectionsOrder.map((key, idx) => (
                    <div key={key} className={`flex items-center gap-3 p-4 rounded-xl border-2 transition-all ${sectionsVisible[key] ? 'border-[#0EA5E9]/30 bg-blue-50/50' : 'border-gray-200 bg-gray-50 opacity-60'}`}>
                      <GripVertical className="w-5 h-5 text-gray-400 shrink-0" />
                      <div className="flex-1">
                        <p className="font-bold text-sm">{SECTION_LABELS[key] || key}</p>
                        <p className="text-xs text-gray-400">{sectionsVisible[key] ? '✅ Visibile' : '🚫 Nascosta'}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button onClick={() => moveSectionUp(idx)} disabled={idx===0} className="p-1 rounded hover:bg-gray-200 disabled:opacity-30"><ChevronUp className="w-4 h-4" /></button>
                        <button onClick={() => moveSectionDown(idx)} disabled={idx===sectionsOrder.length-1} className="p-1 rounded hover:bg-gray-200 disabled:opacity-30"><ChevronDown className="w-4 h-4" /></button>
                        <Switch checked={sectionsVisible[key]} onCheckedChange={() => toggleSection(key)} />
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-700">
                  💡 Dopo aver modificato, clicca <strong>"Salva & Pubblica"</strong> in alto per applicare le modifiche.
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* STILE */}
          <TabsContent value="style">
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><Brush className="w-5 h-5 text-[#0EA5E9]" />Tema Colori</CardTitle>
                  <p className="text-sm text-gray-500">Scegli un tema o personalizza i colori.</p>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <Label className="text-base font-bold mb-3 block">🎨 Temi Preimpostati</Label>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      {COLOR_PRESETS.map((preset) => (
                        <button key={preset.name} onClick={() => setColors({ primary:preset.primary, accent:preset.accent, bg:preset.bg, text:preset.text })}
                          className={`p-3 rounded-xl border-2 text-left transition-all hover:scale-105 ${colors.primary===preset.primary ? 'border-[#0EA5E9] shadow-md' : 'border-gray-200'}`}
                          style={{ background: preset.bg }}>
                          <div className="flex gap-1 mb-2">
                            <div className="w-5 h-5 rounded-full shadow" style={{ background: preset.primary }} />
                            <div className="w-5 h-5 rounded-full shadow" style={{ background: preset.accent }} />
                          </div>
                          <p className="text-xs font-bold" style={{ color: preset.text }}>{preset.name}</p>
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <Label className="text-base font-bold mb-3 block">🖌️ Colori Personalizzati</Label>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                      {[['primary','Colore Principale'],['accent','Colore Secondario'],['bg','Sfondo Pagina'],['text','Colore Testo']].map(([key, label]) => (
                        <div key={key}>
                          <Label className="text-xs text-gray-500 mb-1 block">{label}</Label>
                          <div className="flex items-center gap-2">
                            <input type="color" value={colors[key]} onChange={e => setColors(c=>({...c,[key]:e.target.value}))} className="w-10 h-10 rounded-lg border border-gray-200 cursor-pointer" />
                            <Input value={colors[key]} onChange={e => setColors(c=>({...c,[key]:e.target.value}))} className="font-mono text-sm" />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <Label className="text-base font-bold mb-3 block">👁️ Anteprima</Label>
                    <div className="rounded-2xl overflow-hidden border-2 border-gray-200 shadow-lg" style={{ background: colors.bg }}>
                      <div className="p-4" style={{ background: colors.primary }}>
                        <p className="text-white font-black text-lg">BRUNO MELITO HAIR</p>
                      </div>
                      <div className="p-6">
                        <p className="font-black text-2xl mb-2" style={{ color: colors.text }}>Titolo Sezione</p>
                        <p className="mb-4 text-sm" style={{ color: colors.text, opacity:0.6 }}>Testo di esempio del sito con questi colori.</p>
                        <button className="px-6 py-3 rounded-xl font-bold text-white" style={{ background: colors.primary }}>PRENOTA ORA</button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>🏷️ Badge & Slogan Hero</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <div><Label>Slogan principale</Label><Input value={config.slogan||''} onChange={e=>updateField('slogan',e.target.value)} placeholder="Es. Metti la testa a posto!!" className="mt-1" /></div>
                  <div><Label>Badge hero (piccola etichetta)</Label><Input value={config.subtitle||''} onChange={e=>updateField('subtitle',e.target.value)} placeholder="Es. SOLO PER APPUNTAMENTO" className="mt-1" /></div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* TESTI */}
          <TabsContent value="texts">
            <div className="space-y-6">
              <Card>
                <CardHeader><CardTitle>🏠 Sezione Hero</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div><Label>Nome Salone</Label><Input value={config.salon_name||''} onChange={e=>updateField('salon_name',e.target.value)} className="mt-1" /></div>
                    <div><Label>Badge Hero</Label><Input value={config.subtitle||''} onChange={e=>updateField('subtitle',e.target.value)} placeholder="SOLO PER APPUNTAMENTO" className="mt-1" /></div>
                  </div>
                  <div><Label>Descrizione (testo sotto il logo)</Label><Textarea value={config.hero_description||''} onChange={e=>updateField('hero_description',e.target.value)} rows={3} className="mt-1" /></div>
                  <div className="grid grid-cols-2 gap-4">
                    <div><Label>Anni Esperienza (es. 40+)</Label><Input value={config.years_experience||''} onChange={e=>updateField('years_experience',e.target.value)} className="mt-1" /></div>
                    <div><Label>Anno Fondazione</Label><Input value={config.year_founded||''} onChange={e=>updateField('year_founded',e.target.value)} className="mt-1" /></div>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>ℹ️ Chi Siamo</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <div><Label>Titolo</Label><Input value={config.about_title||''} onChange={e=>updateField('about_title',e.target.value)} className="mt-1" /></div>
                  <div><Label>Paragrafo 1</Label><Textarea value={config.about_text||''} onChange={e=>updateField('about_text',e.target.value)} rows={3} className="mt-1" /></div>
                  <div><Label>Paragrafo 2</Label><Textarea value={config.about_text_2||''} onChange={e=>updateField('about_text_2',e.target.value)} rows={3} className="mt-1" /></div>
                  <div>
                    <Label>Punti di Forza</Label>
                    <div className="space-y-2 mt-2">
                      {(config.about_features||[]).map((feat,idx) => (
                        <div key={idx} className="flex gap-2">
                          <Input value={feat} onChange={e=>updateFeature(idx,e.target.value)} placeholder="Es. Dal 1983 nel settore" />
                          <Button variant="ghost" size="icon" onClick={()=>removeFeature(idx)} className="text-red-500 shrink-0"><Trash2 className="w-4 h-4" /></Button>
                        </div>
                      ))}
                      <Button variant="outline" size="sm" onClick={addFeature}><Plus className="w-4 h-4 mr-1" />Aggiungi</Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>💇 Titoli Gallery</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <div><Label>Titolo sezione gallery</Label><Input value={config.gallery_title||''} onChange={e=>updateField('gallery_title',e.target.value)} className="mt-1" /></div>
                  <div><Label>Sottotitolo gallery</Label><Input value={config.gallery_subtitle||''} onChange={e=>updateField('gallery_subtitle',e.target.value)} className="mt-1" /></div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* SERVIZI */}
          <TabsContent value="services">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>✂️ Listino Prezzi & Servizi</CardTitle>
                    <p className="text-sm text-gray-500 mt-1">Servizi mostrati nel listino pubblico del sito.</p>
                  </div>
                  <Button variant="outline" size="sm" onClick={addCategory}><Plus className="w-4 h-4 mr-1" />Categoria</Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {(config.service_categories||[]).map((cat,catIdx) => (
                  <div key={catIdx} className="border-2 border-gray-200 rounded-2xl p-4 space-y-3 hover:border-[#0EA5E9]/30 transition-all">
                    <div className="flex items-center gap-2">
                      <div className="flex flex-col gap-0.5">
                        <button onClick={()=>moveCategoryUp(catIdx)} disabled={catIdx===0} className="p-0.5 rounded hover:bg-gray-100 disabled:opacity-30"><ChevronUp className="w-3 h-3" /></button>
                        <button onClick={()=>moveCategoryDown(catIdx)} disabled={catIdx===(config.service_categories||[]).length-1} className="p-0.5 rounded hover:bg-gray-100 disabled:opacity-30"><ChevronDown className="w-3 h-3" /></button>
                      </div>
                      <Input value={cat.title} onChange={e=>updateCategory(catIdx,'title',e.target.value)} placeholder="Nome Categoria" className="font-bold flex-1" />
                      <Button variant="ghost" size="icon" onClick={()=>removeCategory(catIdx)} className="text-red-500 shrink-0"><Trash2 className="w-4 h-4" /></Button>
                    </div>
                    <Input value={cat.desc||''} onChange={e=>updateCategory(catIdx,'desc',e.target.value)} placeholder="Descrizione (opzionale)" className="text-sm" />
                    <div className="space-y-2 pl-4 border-l-2 border-[#0EA5E9]/20">
                      {(cat.items||[]).map((item,itemIdx) => (
                        <div key={itemIdx} className="flex gap-2 items-center">
                          <Input value={item.name} onChange={e=>updateCategoryItem(catIdx,itemIdx,'name',e.target.value)} placeholder="Nome servizio" className="flex-1" />
                          <Input value={item.price} onChange={e=>updateCategoryItem(catIdx,itemIdx,'price',e.target.value)} placeholder="Prezzo" className="w-28" />
                          <Button variant="ghost" size="icon" onClick={()=>removeCategoryItem(catIdx,itemIdx)} className="text-red-400 shrink-0"><X className="w-4 h-4" /></Button>
                        </div>
                      ))}
                      <Button variant="outline" size="sm" onClick={()=>addCategoryItem(catIdx)}><Plus className="w-4 h-4 mr-1" />Servizio</Button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          {/* FOTO SALONE */}
          <TabsContent value="photos">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>📸 Foto del Salone</CardTitle>
                    <p className="text-sm text-gray-500 mt-1">La 1ª foto appare nell'hero. La 2ª nella sezione "Chi Siamo".</p>
                  </div>
                  <div className="relative">
                    <input type="file" accept="image/*,video/mp4,video/webm,video/quicktime" multiple onChange={e=>handleMediaUpload(e,'salon')} className="absolute inset-0 opacity-0 cursor-pointer z-10" disabled={uploading} />
                    <Button variant="outline" disabled={uploading}>{uploading?<Loader2 className="w-4 h-4 animate-spin mr-2"/>:<Upload className="w-4 h-4 mr-2"/>}Carica</Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {salonPhotos.length===0 ? (
                  <div className="text-center py-12 text-gray-400"><Image className="w-12 h-12 mx-auto mb-3 text-gray-300"/><p>Carica le prime foto del salone!</p></div>
                ) : (
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {salonPhotos.map((item,idx) => (
                      <div key={item.id} className="relative group rounded-2xl overflow-hidden border-2 border-gray-200">
                        {idx===0 && <div className="absolute top-2 left-2 z-10 bg-[#0EA5E9] text-white text-xs font-bold px-2 py-1 rounded-full">HERO</div>}
                        {idx===1 && <div className="absolute top-2 left-2 z-10 bg-rose-500 text-white text-xs font-bold px-2 py-1 rounded-full">CHI SIAMO</div>}
                        {item.file_type==='video' ? <video src={getImageUrl(item)} className="w-full aspect-square object-cover" muted playsInline/> : <img src={getImageUrl(item)} alt={item.label} className="w-full aspect-square object-cover"/>}
                        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                          <Button variant="ghost" size="icon" onClick={()=>deleteGalleryItem(item.id)} className="text-white hover:text-red-400"><Trash2 className="w-5 h-5"/></Button>
                        </div>
                        <div className="p-2"><Input value={item.label||''} onChange={e=>updateGalleryItem(item.id,'label',e.target.value)} placeholder="Etichetta" className="text-xs h-7"/></div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* GALLERY */}
          <TabsContent value="gallery">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>💇 Gallery Lavori</CardTitle>
                    <p className="text-sm text-gray-500 mt-1">Mostra i tuoi lavori migliori.</p>
                  </div>
                  <div className="relative">
                    <input type="file" accept="image/*,video/mp4,video/webm,video/quicktime" multiple onChange={e=>handleMediaUpload(e,'gallery')} className="absolute inset-0 opacity-0 cursor-pointer z-10" disabled={uploading} />
                    <Button variant="outline" disabled={uploading}>{uploading?<Loader2 className="w-4 h-4 animate-spin mr-2"/>:<Upload className="w-4 h-4 mr-2"/>}Carica</Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {galleryPhotos.length===0 ? (
                  <div className="text-center py-12 text-gray-400"><Image className="w-12 h-12 mx-auto mb-3 text-gray-300"/><p>Carica i tuoi lavori!</p></div>
                ) : (
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {galleryPhotos.map((item) => (
                      <div key={item.id} className="relative group rounded-2xl overflow-hidden border-2 border-gray-200">
                        {item.file_type==='video' ? <video src={getImageUrl(item)} className="w-full aspect-[3/4] object-cover" muted playsInline/> : <img src={getImageUrl(item)} alt={item.label} className="w-full aspect-[3/4] object-cover"/>}
                        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                          <Button variant="ghost" size="icon" onClick={()=>deleteGalleryItem(item.id)} className="text-white hover:text-red-400"><Trash2 className="w-5 h-5"/></Button>
                        </div>
                        <div className="p-2 space-y-1">
                          <Input value={item.label||''} onChange={e=>updateGalleryItem(item.id,'label',e.target.value)} placeholder="Nome" className="text-xs h-7"/>
                          <Input value={item.tag||''} onChange={e=>updateGalleryItem(item.id,'tag',e.target.value)} placeholder="Tag (es. Balayage)" className="text-xs h-7"/>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* RECENSIONI */}
          <TabsContent value="reviews">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>⭐ Recensioni Clienti</CardTitle>
                  <Button variant="outline" onClick={()=>openReviewDialog()}><Plus className="w-4 h-4 mr-1"/>Aggiungi</Button>
                </div>
              </CardHeader>
              <CardContent>
                {reviews.length===0 ? (
                  <div className="text-center py-12 text-gray-400"><Star className="w-12 h-12 mx-auto mb-3 text-gray-300"/><p>Aggiungi le recensioni dei tuoi clienti!</p></div>
                ) : (
                  <div className="space-y-3">
                    {reviews.map((review) => (
                      <div key={review.id} className="flex items-start gap-4 p-4 rounded-xl bg-gray-50 border border-gray-200">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-bold text-sm">{review.name}</span>
                            <div className="flex gap-0.5">{[...Array(review.rating||5)].map((_,i)=><Star key={i} className="w-3 h-3 fill-amber-400 text-amber-400"/>)}</div>
                          </div>
                          <p className="text-sm text-gray-600">"{review.text}"</p>
                        </div>
                        <div className="flex gap-1 shrink-0">
                          <Button variant="ghost" size="icon" onClick={()=>openReviewDialog(review)} className="h-8 w-8 text-blue-500"><Save className="w-3 h-3"/></Button>
                          <Button variant="ghost" size="icon" onClick={()=>deleteReview(review.id)} className="h-8 w-8 text-red-500"><Trash2 className="w-3 h-3"/></Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* CONTATTI */}
          <TabsContent value="contacts">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader><CardTitle>⏰ Orari di Apertura</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  {['lun','mar','mer','gio','ven','sab','dom'].map(day => (
                    <div key={day} className="flex items-center gap-3">
                      <span className="w-10 font-bold text-sm capitalize text-gray-600">{day}</span>
                      <Input value={(config.hours||{})[day]||''} onChange={e=>updateHour(day,e.target.value)} placeholder="08:00 - 19:00 oppure Chiuso"/>
                    </div>
                  ))}
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>📞 Contatti</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <div><Label>Email</Label><Input value={config.email||''} onChange={e=>updateField('email',e.target.value)} className="mt-1"/></div>
                  <div><Label>Indirizzo</Label><Input value={config.address||''} onChange={e=>updateField('address',e.target.value)} className="mt-1"/></div>
                  <div><Label>Link Google Maps</Label><Input value={config.maps_url||''} onChange={e=>updateField('maps_url',e.target.value)} className="mt-1"/></div>
                  <div><Label>WhatsApp (es. 393397833526)</Label><Input value={config.whatsapp||''} onChange={e=>updateField('whatsapp',e.target.value)} className="mt-1"/></div>
                  <div>
                    <Label>Telefoni</Label>
                    <div className="space-y-2 mt-2">
                      {(config.phones||[]).map((phone,idx) => (
                        <div key={idx} className="flex gap-2">
                          <Input value={phone} onChange={e=>updatePhone(idx,e.target.value)}/>
                          <Button variant="ghost" size="icon" onClick={()=>removePhone(idx)} className="text-red-500 shrink-0"><Trash2 className="w-4 h-4"/></Button>
                        </div>
                      ))}
                      <Button variant="outline" size="sm" onClick={addPhone}><Plus className="w-4 h-4 mr-1"/>Telefono</Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>

        <Dialog open={reviewDialog} onOpenChange={setReviewDialog}>
          <DialogContent>
            <DialogHeader><DialogTitle>{editReview?'Modifica Recensione':'Nuova Recensione'}</DialogTitle></DialogHeader>
            <div className="space-y-4">
              <div><Label>Nome Cliente</Label><Input value={reviewForm.name} onChange={e=>setReviewForm({...reviewForm,name:e.target.value})} placeholder="Es. Maria R." className="mt-1"/></div>
              <div><Label>Testo</Label><Textarea value={reviewForm.text} onChange={e=>setReviewForm({...reviewForm,text:e.target.value})} rows={3} className="mt-1"/></div>
              <div>
                <Label>Valutazione</Label>
                <div className="flex gap-1 mt-2">
                  {[1,2,3,4,5].map(n => (
                    <button key={n} onClick={()=>setReviewForm({...reviewForm,rating:n})}>
                      <Star className={`w-7 h-7 ${n<=reviewForm.rating?'fill-amber-400 text-amber-400':'text-gray-300'}`}/>
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={()=>setReviewDialog(false)}>Annulla</Button>
              <Button onClick={saveReview} className="bg-[#0EA5E9] text-white">Salva</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}


