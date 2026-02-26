import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '@/components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import {
  Gift, Plus, Trash2, Pencil, Loader2, Copy, Eye, EyeOff,
  Users, Star, Heart, UserPlus, Award, Cake, Hash, TrendingUp
} from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const RULE_TYPES = [
  { value: 'under_30', label: 'Under 30', icon: Users, color: 'bg-pink-100 text-pink-700' },
  { value: 'first_visit', label: 'Prima Visita', icon: UserPlus, color: 'bg-blue-100 text-blue-700' },
  { value: 'birthday', label: 'Compleanno', icon: Cake, color: 'bg-purple-100 text-purple-700' },
  { value: 'bring_friend', label: "Porta un'Amica", icon: Heart, color: 'bg-red-100 text-red-700' },
  { value: 'google_review', label: 'Recensione Google', icon: Star, color: 'bg-yellow-100 text-yellow-700' },
  { value: 'fidelity_vip', label: 'Fidelity VIP (10+ visite)', icon: Award, color: 'bg-emerald-100 text-emerald-700' },
  { value: 'promo_code', label: 'Codice Promo Generico', icon: Hash, color: 'bg-gray-100 text-gray-700' },
];

export default function PromotionsPage() {
  const [promotions, setPromotions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [saving, setSaving] = useState(false);

  const [formData, setFormData] = useState({
    name: '', description: '', rule_type: 'under_30',
    free_service_name: '', promo_code: '', active: true, show_on_booking: true
  });

  useEffect(() => { fetchPromos(); }, []);

  const fetchPromos = async () => {
    try {
      const res = await axios.get(`${API}/promotions`);
      setPromotions(res.data);
    } catch (err) {
      toast.error('Errore nel caricamento');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name || !formData.free_service_name) {
      toast.error('Compila nome e servizio omaggio');
      return;
    }
    setSaving(true);
    try {
      if (editing) {
        await axios.put(`${API}/promotions/${editing.id}`, formData);
        toast.success('Promozione aggiornata');
      } else {
        await axios.post(`${API}/promotions`, formData);
        toast.success('Promozione creata');
      }
      setDialogOpen(false);
      resetForm();
      fetchPromos();
    } catch (err) {
      toast.error('Errore nel salvataggio');
    }
    setSaving(false);
  };

  const deletePromo = async (id) => {
    if (!window.confirm('Eliminare questa promozione?')) return;
    try {
      await axios.delete(`${API}/promotions/${id}`);
      toast.success('Promozione eliminata');
      fetchPromos();
    } catch (err) {
      toast.error('Errore');
    }
  };

  const toggleActive = async (promo) => {
    try {
      await axios.put(`${API}/promotions/${promo.id}`, { active: !promo.active });
      fetchPromos();
      toast.success(promo.active ? 'Disattivata' : 'Attivata');
    } catch (err) {
      toast.error('Errore');
    }
  };

  const openEdit = (promo) => {
    setEditing(promo);
    setFormData({
      name: promo.name, description: promo.description, rule_type: promo.rule_type,
      free_service_name: promo.free_service_name, promo_code: promo.promo_code || '',
      active: promo.active, show_on_booking: promo.show_on_booking
    });
    setDialogOpen(true);
  };

  const resetForm = () => {
    setEditing(null);
    setFormData({
      name: '', description: '', rule_type: 'under_30',
      free_service_name: '', promo_code: '', active: true, show_on_booking: true
    });
  };

  const copyCode = (code) => {
    navigator.clipboard.writeText(code);
    toast.success(`Codice "${code}" copiato!`);
  };

  const getRuleInfo = (rt) => RULE_TYPES.find(r => r.value === rt) || RULE_TYPES[6];
  const totalUsage = promotions.reduce((s, p) => s + (p.usage_count || 0), 0);

  return (
    <Layout>
      <div className="space-y-6" data-testid="promotions-page">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl sm:text-3xl font-black text-[#0F172A] flex items-center gap-3">
              <Gift className="w-7 h-7 text-pink-500" />
              Promozioni
            </h1>
            <p className="text-[#334155] mt-1">Crea offerte con servizi extra in omaggio per far crescere il salone</p>
          </div>
          <Button onClick={() => { resetForm(); setDialogOpen(true); }}
            className="bg-pink-500 hover:bg-pink-600 text-white shrink-0"
            data-testid="new-promo-btn">
            <Plus className="w-4 h-4 mr-2" /> Nuova Promozione
          </Button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card className="bg-gradient-to-br from-pink-50 to-pink-100 border-pink-200">
            <CardContent className="p-5">
              <p className="text-sm text-pink-700 font-semibold">Promozioni Attive</p>
              <p className="text-3xl font-black text-pink-600" data-testid="active-promos-count">
                {promotions.filter(p => p.active).length}
              </p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
            <CardContent className="p-5">
              <p className="text-sm text-blue-700 font-semibold">Totale Promozioni</p>
              <p className="text-3xl font-black text-blue-600">{promotions.length}</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
            <CardContent className="p-5">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-green-600" />
                <div>
                  <p className="text-sm text-green-700 font-semibold">Utilizzi Totali</p>
                  <p className="text-3xl font-black text-green-600" data-testid="total-usage">{totalUsage}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Promo List */}
        {promotions.length === 0 && !loading ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Gift className="w-12 h-12 mx-auto text-[#E2E8F0] mb-3" />
              <p className="text-[#334155] font-semibold">Nessuna promozione creata</p>
              <p className="text-sm text-[#94A3B8] mt-1">Crea la tua prima promozione per attirare nuovi clienti!</p>
              <Button onClick={() => { resetForm(); setDialogOpen(true); }}
                className="mt-4 bg-pink-500 hover:bg-pink-600 text-white">
                <Plus className="w-4 h-4 mr-2" /> Crea Promozione
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {promotions.map((promo) => {
              const ruleInfo = getRuleInfo(promo.rule_type);
              const RuleIcon = ruleInfo.icon;
              return (
                <Card key={promo.id}
                  className={`border-2 transition-all ${promo.active ? 'border-[#E2E8F0] bg-white' : 'border-gray-200 bg-gray-50 opacity-60'}`}
                  data-testid={`promo-${promo.id}`}>
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap mb-2">
                          <Badge className={ruleInfo.color + ' font-semibold'}>
                            <RuleIcon className="w-3 h-3 mr-1" /> {ruleInfo.label}
                          </Badge>
                          {promo.active ? (
                            <Badge className="bg-green-100 text-green-700">Attiva</Badge>
                          ) : (
                            <Badge className="bg-gray-200 text-gray-500">Disattivata</Badge>
                          )}
                          {promo.show_on_booking && (
                            <Badge variant="outline" className="text-xs border-[#0EA5E9] text-[#0EA5E9]">
                              <Eye className="w-3 h-3 mr-1" /> Online
                            </Badge>
                          )}
                        </div>
                        <h3 className="font-bold text-lg text-[#0F172A]">{promo.name}</h3>
                        <p className="text-sm text-[#334155] mt-1">{promo.description}</p>
                        <div className="mt-3 p-2.5 bg-pink-50 border border-pink-200 rounded-lg">
                          <p className="text-sm font-bold text-pink-700 flex items-center gap-1.5">
                            <Gift className="w-4 h-4" /> OMAGGIO: {promo.free_service_name}
                          </p>
                        </div>
                        <div className="flex items-center gap-4 mt-3 text-sm">
                          <button onClick={() => copyCode(promo.promo_code)}
                            className="flex items-center gap-1.5 text-[#0EA5E9] hover:underline font-mono font-bold"
                            data-testid={`copy-code-${promo.id}`}>
                            <Copy className="w-3.5 h-3.5" /> {promo.promo_code}
                          </button>
                          <span className="text-[#64748B] flex items-center gap-1">
                            <TrendingUp className="w-3.5 h-3.5" /> {promo.usage_count || 0} utilizzi
                          </span>
                        </div>
                      </div>
                      <div className="flex flex-col gap-1 shrink-0">
                        <Switch checked={promo.active} onCheckedChange={() => toggleActive(promo)} />
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-[#334155] hover:text-[#0EA5E9]"
                          onClick={() => openEdit(promo)} data-testid={`edit-promo-${promo.id}`}>
                          <Pencil className="w-3.5 h-3.5" />
                        </Button>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-[#334155] hover:text-red-500"
                          onClick={() => deletePromo(promo.id)} data-testid={`delete-promo-${promo.id}`}>
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        {/* Create/Edit Dialog */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="sm:max-w-[520px]">
            <DialogHeader>
              <DialogTitle className="text-xl font-bold text-[#0F172A] flex items-center gap-2">
                <Gift className="w-5 h-5 text-pink-500" />
                {editing ? 'Modifica Promozione' : 'Nuova Promozione'}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4 mt-2">
              <div className="space-y-2">
                <Label>Nome Promozione *</Label>
                <Input value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="es. Speciale Under 30"
                  data-testid="promo-name-input" />
              </div>
              <div className="space-y-2">
                <Label>Descrizione</Label>
                <Input value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="es. Piega GRATIS con qualsiasi servizio colore per under 30" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Regola</Label>
                  <Select value={formData.rule_type}
                    onValueChange={(v) => setFormData({ ...formData, rule_type: v })}>
                    <SelectTrigger data-testid="promo-rule-select"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {RULE_TYPES.map(r => (
                        <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Servizio in Omaggio *</Label>
                  <Input value={formData.free_service_name}
                    onChange={(e) => setFormData({ ...formData, free_service_name: e.target.value })}
                    placeholder="es. Piega, Trattamento Olaplex"
                    data-testid="promo-service-input" />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Codice Promo (opzionale, generato automaticamente)</Label>
                <Input value={formData.promo_code}
                  onChange={(e) => setFormData({ ...formData, promo_code: e.target.value.toUpperCase() })}
                  placeholder="es. UNDER30" className="font-mono" />
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-[#F8FAFC]">
                <Label className="font-normal flex items-center gap-2">
                  <Eye className="w-4 h-4 text-[#334155]" /> Mostra sulla pagina prenotazione
                </Label>
                <Switch checked={formData.show_on_booking}
                  onCheckedChange={(c) => setFormData({ ...formData, show_on_booking: c })} />
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }}>Annulla</Button>
                <Button type="submit" disabled={saving} className="bg-pink-500 hover:bg-pink-600 text-white" data-testid="save-promo-btn">
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : editing ? 'Salva' : 'Crea'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
