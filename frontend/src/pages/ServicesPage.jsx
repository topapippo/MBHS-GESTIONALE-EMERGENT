import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
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
import { Scissors, Plus, Clock, Euro, Edit2, Trash2, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CATEGORIES = [
  { value: 'taglio', label: 'Taglio', color: '#0EA5E9' },
  { value: 'piega', label: 'Piega', color: '#E9C46A' },
  { value: 'trattamento', label: 'Trattamenti', color: '#334155' },
  { value: 'colore', label: 'Colore', color: '#789F8A' },
  { value: 'modellanti', label: 'Modellanti', color: '#C084FC' },
  { value: 'abbonamenti', label: 'Abbonamenti/Prepagate', color: '#6366F1' },
  { value: 'prodotti', label: 'Prodotti e Varie', color: '#F97316' },
];

const CATEGORY_ORDER = CATEGORIES.map(c => c.value);

const COLOR_PRESETS = [
  '#0EA5E9', '#0284C7', '#789F8A', '#10B981', '#E9C46A', '#F59E0B',
  '#F97316', '#EF4444', '#EC4899', '#C084FC', '#6366F1', '#334155',
  '#14B8A6', '#8B5CF6', '#D946EF', '#64748B',
];

export default function ServicesPage() {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [serviceToDelete, setServiceToDelete] = useState(null);
  const [editingService, setEditingService] = useState(null);
  const [saving, setSaving] = useState(false);
  
  const [formData, setFormData] = useState({
    name: '',
    category: 'taglio',
    duration: 30,
    price: 0,
    color: '#0EA5E9',
  });

  useEffect(() => {
    fetchServices();
  }, []);

  const fetchServices = async () => {
    try {
      const res = await axios.get(`${API}/services`);
      setServices(res.data);
    } catch (err) {
      console.error('Error fetching services:', err);
      toast.error('Errore nel caricamento dei servizi');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error('Inserisci il nome del servizio');
      return;
    }
    
    setSaving(true);
    try {
      if (editingService) {
        await axios.put(`${API}/services/${editingService.id}`, formData);
        toast.success('Servizio aggiornato!');
      } else {
        await axios.post(`${API}/services`, formData);
        toast.success('Servizio aggiunto!');
      }
      setDialogOpen(false);
      setEditingService(null);
      setFormData({ name: '', category: 'taglio', duration: 30, price: 0 });
      fetchServices();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore nel salvataggio');
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (service) => {
    setEditingService(service);
    setFormData({
      name: service.name,
      category: service.category,
      duration: service.duration,
      price: service.price,
      color: service.color || CATEGORIES.find(c => c.value === service.category)?.color || '#0EA5E9',
    });
    setDialogOpen(true);
  };

  const handleDelete = async () => {
    if (!serviceToDelete) return;
    try {
      await axios.delete(`${API}/services/${serviceToDelete}`);
      toast.success('Servizio eliminato');
      setDeleteDialogOpen(false);
      setServiceToDelete(null);
      fetchServices();
    } catch (err) {
      toast.error('Errore nell\'eliminazione');
    }
  };

  const openNewDialog = () => {
    setEditingService(null);
    setFormData({ name: '', category: 'taglio', duration: 30, price: 0 });
    setDialogOpen(true);
  };

  const getCategoryInfo = (category) => {
    return CATEGORIES.find(c => c.value === category) || CATEGORIES[4];
  };

  // Sort services by sort_order (or number prefix) and group by category
  const sortByOrder = (a, b) => {
    const orderA = a.sort_order || parseInt(a.name.match(/^\d+/)?.[0] || '999');
    const orderB = b.sort_order || parseInt(b.name.match(/^\d+/)?.[0] || '999');
    return orderA - orderB;
  };

  const groupedServices = services.sort(sortByOrder).reduce((acc, service) => {
    const cat = service.category;
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(service);
    return acc;
  }, {});

  // Sort categories in the defined order
  const sortedCategories = CATEGORY_ORDER.filter(cat => groupedServices[cat]);

  return (
    <Layout>
      <div className="space-y-6" data-testid="services-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="font-playfair text-3xl font-medium text-[#0F172A]">Servizi</h1>
            <p className="text-[#334155] mt-1 font-manrope">{services.length} servizi disponibili</p>
          </div>
          <Button 
            onClick={openNewDialog}
            data-testid="new-service-btn"
            className="bg-[#0EA5E9] hover:bg-[#0284C7] text-white shadow-lg shadow-[#0EA5E9]/20"
          >
            <Plus className="w-5 h-5 mr-2" />
            Nuovo Servizio
          </Button>
        </div>

        {/* Services by Category */}
        {loading ? (
          <div className="space-y-6">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-48" />
            ))}
          </div>
        ) : services.length > 0 ? (
          <div className="space-y-8">
            {CATEGORIES.map((category) => {
              const categoryServices = groupedServices[category.value];
              if (!categoryServices || categoryServices.length === 0) return null;
              
              return (
                <div key={category.value}>
                  <div className="flex items-center gap-2 mb-4">
                    <div 
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: category.color }}
                    />
                    <h2 className="font-playfair text-xl text-[#0F172A]">{category.label}</h2>
                    <Badge variant="outline" className="ml-2 border-[#E2E8F0] text-[#334155]">
                      {categoryServices.length}
                    </Badge>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {categoryServices.map((service) => (
                      <Card
                        key={service.id}
                        data-testid={`service-card-${service.id}`}
                        className="bg-white border-[#E2E8F0]/30 hover:border-[#0EA5E9]/30 transition-all duration-300 hover:-translate-y-1"
                      >
                        <CardContent className="p-5">
                          <div className="flex items-start justify-between">
                            <div>
                              <h3 className="font-medium text-[#0F172A] text-lg">{service.name}</h3>
                              <div className="flex items-center gap-4 mt-3 text-sm text-[#334155]">
                                <span className="flex items-center gap-1">
                                  <Clock className="w-4 h-4" /> {service.duration} min
                                </span>
                                <span className="flex items-center gap-1 font-semibold text-[#0F172A]">
                                  <Euro className="w-4 h-4" /> {service.price.toFixed(2)}
                                </span>
                              </div>
                            </div>
                            <div className="flex gap-1">
                              <Button
                                size="icon"
                                variant="ghost"
                                onClick={() => handleEdit(service)}
                                className="text-[#334155] hover:text-[#0EA5E9]"
                              >
                                <Edit2 className="w-4 h-4" />
                              </Button>
                              <Button
                                size="icon"
                                variant="ghost"
                                onClick={() => {
                                  setServiceToDelete(service.id);
                                  setDeleteDialogOpen(true);
                                }}
                                className="text-[#334155] hover:text-[#E76F51]"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <Card className="bg-white border-[#E2E8F0]/30">
            <CardContent className="py-16 text-center">
              <Scissors className="w-16 h-16 mx-auto text-[#E2E8F0] mb-4" strokeWidth={1.5} />
              <h3 className="font-playfair text-xl text-[#0F172A] mb-2">Nessun servizio</h3>
              <p className="text-[#334155] mb-4">Aggiungi i tuoi servizi per iniziare</p>
              <Button
                onClick={openNewDialog}
                className="bg-[#0EA5E9] hover:bg-[#0284C7] text-white"
              >
                <Plus className="w-4 h-4 mr-2" /> Aggiungi Servizio
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Add/Edit Dialog */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle className="font-playfair text-2xl text-[#0F172A]">
                {editingService ? 'Modifica Servizio' : 'Nuovo Servizio'}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label>Nome Servizio *</Label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Es. Taglio Donna"
                  data-testid="service-name-input"
                  className="bg-[#F8FAFC] border-transparent focus:border-[#0EA5E9]"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Categoria</Label>
                <Select
                  value={formData.category}
                  onValueChange={(val) => setFormData({ ...formData, category: val })}
                >
                  <SelectTrigger data-testid="service-category-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CATEGORIES.map((cat) => (
                      <SelectItem key={cat.value} value={cat.value}>
                        <div className="flex items-center gap-2">
                          <div 
                            className="w-2 h-2 rounded-full" 
                            style={{ backgroundColor: cat.color }}
                          />
                          {cat.label}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Durata (minuti)</Label>
                  <Input
                    type="number"
                    min="5"
                    step="5"
                    value={formData.duration}
                    onChange={(e) => setFormData({ ...formData, duration: parseInt(e.target.value) || 0 })}
                    data-testid="service-duration-input"
                    className="bg-[#F8FAFC] border-transparent focus:border-[#0EA5E9]"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Prezzo (€)</Label>
                  <Input
                    type="number"
                    min="0"
                    step="0.50"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: parseFloat(e.target.value) || 0 })}
                    data-testid="service-price-input"
                    className="bg-[#F8FAFC] border-transparent focus:border-[#0EA5E9]"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Colore</Label>
                <div className="flex flex-wrap gap-2">
                  {COLOR_PRESETS.map((c) => (
                    <button
                      key={c}
                      type="button"
                      onClick={() => setFormData({ ...formData, color: c })}
                      className={`w-7 h-7 rounded-full border-2 transition-all hover:scale-110 ${formData.color === c ? 'border-[#0F172A] scale-110 ring-2 ring-offset-1 ring-[#0F172A]/20' : 'border-transparent'}`}
                      style={{ backgroundColor: c }}
                      data-testid={`color-${c}`}
                    />
                  ))}
                </div>
              </div>
              <DialogFooter>
                <Button
                  type="submit"
                  disabled={saving}
                  data-testid="save-service-btn"
                  className="bg-[#0EA5E9] hover:bg-[#0284C7] text-white"
                >
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : editingService ? 'Salva Modifiche' : 'Aggiungi Servizio'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation */}
        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Elimina Servizio</AlertDialogTitle>
              <AlertDialogDescription>
                Sei sicura di voler eliminare questo servizio? L'azione non può essere annullata.
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
      </div>
    </Layout>
  );
}
