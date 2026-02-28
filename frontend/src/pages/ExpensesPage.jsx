import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
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
  ArrowDownCircle, Plus, Trash2, Check, Pencil, Loader2,
  Calendar, AlertTriangle, RotateCcw, Receipt, Filter
} from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CATEGORIES = [
  { value: 'affitto', label: 'Affitto', color: 'bg-purple-100 text-purple-700' },
  { value: 'fornitori', label: 'Fornitori', color: 'bg-blue-100 text-blue-700' },
  { value: 'bollette', label: 'Bollette', color: 'bg-yellow-100 text-yellow-700' },
  { value: 'stipendi', label: 'Stipendi', color: 'bg-green-100 text-green-700' },
  { value: 'tasse', label: 'Tasse', color: 'bg-red-100 text-red-700' },
  { value: 'prodotti', label: 'Prodotti', color: 'bg-cyan-100 text-cyan-700' },
  { value: 'manutenzione', label: 'Manutenzione', color: 'bg-orange-100 text-orange-700' },
  { value: 'altro', label: 'Altro', color: 'bg-gray-100 text-gray-700' },
];

const RECURRENCES = [
  { value: 'monthly', label: 'Mensile' },
  { value: 'quarterly', label: 'Trimestrale' },
  { value: 'yearly', label: 'Annuale' },
];

export default function ExpensesPage() {
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingExpense, setEditingExpense] = useState(null);
  const [saving, setSaving] = useState(false);
  const [filter, setFilter] = useState('unpaid'); // 'all', 'unpaid', 'paid'
  const [categoryFilter, setCategoryFilter] = useState('all');

  const [formData, setFormData] = useState({
    description: '',
    amount: '',
    category: 'altro',
    due_date: new Date().toISOString().split('T')[0],
    is_recurring: false,
    recurrence: 'monthly',
    notes: ''
  });

  useEffect(() => {
    fetchExpenses();
  }, [filter]);

  const fetchExpenses = async () => {
    setLoading(true);
    try {
      let url = `${API}/expenses`;
      if (filter === 'unpaid') url += '?paid=false';
      else if (filter === 'paid') url += '?paid=true';
      const res = await axios.get(url);
      setExpenses(res.data);
    } catch (err) {
      console.error(err);
      toast.error('Errore nel caricamento');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.description || !formData.amount || !formData.due_date) {
      toast.error('Compila tutti i campi obbligatori');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        ...formData,
        amount: parseFloat(formData.amount),
        recurrence: formData.is_recurring ? formData.recurrence : null,
      };
      if (editingExpense) {
        await axios.put(`${API}/expenses/${editingExpense.id}`, payload);
        toast.success('Uscita aggiornata');
      } else {
        await axios.post(`${API}/expenses`, payload);
        toast.success('Uscita registrata');
      }
      setDialogOpen(false);
      resetForm();
      fetchExpenses();
    } catch (err) {
      toast.error('Errore nel salvataggio');
    }
    setSaving(false);
  };

  const markPaid = async (id) => {
    try {
      await axios.post(`${API}/expenses/${id}/pay`);
      toast.success('Segnata come pagata');
      fetchExpenses();
    } catch (err) {
      toast.error('Errore');
    }
  };

  const markUnpaid = async (id) => {
    try {
      await axios.post(`${API}/expenses/${id}/unpay`);
      toast.success('Riportata a da pagare');
      fetchExpenses();
    } catch (err) {
      toast.error('Errore');
    }
  };

  const deleteExpense = async (id) => {
    if (!window.confirm('Eliminare questa uscita?')) return;
    try {
      await axios.delete(`${API}/expenses/${id}`);
      toast.success('Uscita eliminata');
      fetchExpenses();
    } catch (err) {
      toast.error('Errore');
    }
  };

  const openEdit = (exp) => {
    setEditingExpense(exp);
    setFormData({
      description: exp.description,
      amount: String(exp.amount),
      category: exp.category,
      due_date: exp.due_date,
      is_recurring: exp.is_recurring || false,
      recurrence: exp.recurrence || 'monthly',
      notes: exp.notes || ''
    });
    setDialogOpen(true);
  };

  const resetForm = () => {
    setEditingExpense(null);
    setFormData({
      description: '',
      amount: '',
      category: 'altro',
      due_date: new Date().toISOString().split('T')[0],
      is_recurring: false,
      recurrence: 'monthly',
      notes: ''
    });
  };

  const getCategoryInfo = (cat) => CATEGORIES.find(c => c.value === cat) || CATEGORIES[CATEGORIES.length - 1];
  const today = new Date().toISOString().split('T')[0];

  const filteredExpenses = categoryFilter === 'all'
    ? expenses
    : expenses.filter(e => e.category === categoryFilter);

  const totalUnpaid = expenses.filter(e => !e.paid).reduce((sum, e) => sum + e.amount, 0);
  const overdueCount = expenses.filter(e => !e.paid && e.due_date < today).length;
  const totalPaid = expenses.filter(e => e.paid).reduce((sum, e) => sum + e.amount, 0);

  return (
    <Layout>
      <div className="space-y-6" data-testid="expenses-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl sm:text-3xl font-black text-[#0F172A] flex items-center gap-3">
              <ArrowDownCircle className="w-7 h-7 text-red-500" />
              Registro Uscite
            </h1>
            <p className="text-[#334155] mt-1">Gestisci spese e scadenze da pagare</p>
          </div>
          <Button
            onClick={() => { resetForm(); setDialogOpen(true); }}
            className="bg-red-500 hover:bg-red-600 text-white shrink-0"
            data-testid="new-expense-btn"
          >
            <Plus className="w-4 h-4 mr-2" /> Nuova Uscita
          </Button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200">
            <CardContent className="p-5">
              <p className="text-sm text-red-700 font-semibold">Da Pagare</p>
              <p className="text-3xl font-black text-red-600" data-testid="total-unpaid">&euro;{totalUnpaid.toFixed(2)}</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
            <CardContent className="p-5">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-orange-600" />
                <div>
                  <p className="text-sm text-orange-700 font-semibold">Scadute</p>
                  <p className="text-3xl font-black text-orange-600" data-testid="overdue-count">{overdueCount}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
            <CardContent className="p-5">
              <p className="text-sm text-green-700 font-semibold">Pagate</p>
              <p className="text-3xl font-black text-green-600">&euro;{totalPaid.toFixed(2)}</p>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <Card className="bg-white border-[#E2E8F0]/30">
          <CardContent className="p-4">
            <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
              <div className="flex gap-2">
                {[
                  { key: 'unpaid', label: 'Da Pagare', icon: AlertTriangle },
                  { key: 'paid', label: 'Pagate', icon: Check },
                  { key: 'all', label: 'Tutte', icon: Receipt },
                ].map(f => (
                  <Button
                    key={f.key}
                    variant={filter === f.key ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setFilter(f.key)}
                    className={filter === f.key ? 'bg-[#0EA5E9] text-white' : 'border-[#E2E8F0]'}
                    data-testid={`filter-${f.key}`}
                  >
                    <f.icon className="w-3.5 h-3.5 mr-1" /> {f.label}
                  </Button>
                ))}
              </div>
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="w-44" data-testid="category-filter">
                  <Filter className="w-3.5 h-3.5 mr-1" />
                  <SelectValue placeholder="Categoria" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutte le categorie</SelectItem>
                  {CATEGORIES.map(c => (
                    <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Expenses List */}
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => <Skeleton key={i} className="h-20" />)}
          </div>
        ) : filteredExpenses.length === 0 ? (
          <Card className="bg-white border-[#E2E8F0]/30">
            <CardContent className="py-12 text-center">
              <Receipt className="w-12 h-12 mx-auto text-[#E2E8F0] mb-3" />
              <p className="text-[#334155] font-semibold">Nessuna uscita registrata</p>
              <Button
                onClick={() => { resetForm(); setDialogOpen(true); }}
                className="mt-4 bg-red-500 hover:bg-red-600 text-white"
              >
                <Plus className="w-4 h-4 mr-2" /> Registra la prima uscita
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {filteredExpenses.map((exp) => {
              const catInfo = getCategoryInfo(exp.category);
              const isOverdue = !exp.paid && exp.due_date < today;
              const isDueSoon = !exp.paid && !isOverdue && exp.due_date <= new Date(Date.now() + 7 * 86400000).toISOString().split('T')[0];

              return (
                <Card
                  key={exp.id}
                  className={`bg-white border-2 transition-all ${
                    isOverdue ? 'border-red-300 bg-red-50/50' :
                    isDueSoon ? 'border-orange-200 bg-orange-50/30' :
                    exp.paid ? 'border-green-200 bg-green-50/30 opacity-70' :
                    'border-[#E2E8F0]'
                  }`}
                  data-testid={`expense-${exp.id}`}
                >
                  <CardContent className="p-4">
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className={`font-bold text-[#0F172A] ${exp.paid ? 'line-through' : ''}`}>{exp.description}</p>
                          <Badge className={catInfo.color}>{catInfo.label}</Badge>
                          {exp.is_recurring && (
                            <Badge variant="outline" className="text-xs border-[#0EA5E9] text-[#0EA5E9]">
                              <RotateCcw className="w-3 h-3 mr-1" />
                              {RECURRENCES.find(r => r.value === exp.recurrence)?.label || 'Ricorrente'}
                            </Badge>
                          )}
                          {isOverdue && (
                            <Badge className="bg-red-500 text-white">SCADUTA</Badge>
                          )}
                          {isDueSoon && !isOverdue && (
                            <Badge className="bg-orange-500 text-white">IN SCADENZA</Badge>
                          )}
                          {exp.paid && (
                            <Badge className="bg-green-500 text-white">PAGATA</Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-4 text-sm text-[#334155] mt-1">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3.5 h-3.5" />
                            Scadenza: {exp.due_date}
                          </span>
                          {exp.paid_date && (
                            <span className="text-green-600">Pagata il {exp.paid_date}</span>
                          )}
                        </div>
                        {exp.notes && <p className="text-xs text-[#64748B] mt-1">{exp.notes}</p>}
                      </div>
                      <div className="flex items-center gap-3 shrink-0">
                        <p className="text-2xl font-black text-red-600">&euro;{exp.amount.toFixed(2)}</p>
                        <div className="flex gap-1">
                          {!exp.paid ? (
                            <Button
                              size="sm"
                              onClick={() => markPaid(exp.id)}
                              className="bg-green-500 hover:bg-green-600 text-white"
                              data-testid={`pay-btn-${exp.id}`}
                            >
                              <Check className="w-4 h-4 mr-1" /> Paga
                            </Button>
                          ) : (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => markUnpaid(exp.id)}
                              className="border-orange-300 text-orange-600"
                              data-testid={`unpay-btn-${exp.id}`}
                            >
                              <RotateCcw className="w-3.5 h-3.5 mr-1" /> Annulla
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => openEdit(exp)}
                            className="text-[#334155] hover:text-[#0EA5E9]"
                            data-testid={`edit-expense-${exp.id}`}
                          >
                            <Pencil className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => deleteExpense(exp.id)}
                            className="text-[#334155] hover:text-red-500"
                            data-testid={`delete-expense-${exp.id}`}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        {/* Add/Edit Dialog */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="sm:max-w-[480px]">
            <DialogHeader>
              <DialogTitle className="text-xl font-bold text-[#0F172A]">
                {editingExpense ? 'Modifica Uscita' : 'Nuova Uscita'}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4 mt-2">
              <div className="space-y-2">
                <Label>Descrizione *</Label>
                <Input
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="es. Affitto locale, Fornitore colori..."
                  data-testid="expense-description-input"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Importo (&euro;) *</Label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.amount}
                    onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                    placeholder="500"
                    data-testid="expense-amount-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Categoria</Label>
                  <Select value={formData.category} onValueChange={(v) => setFormData({ ...formData, category: v })}>
                    <SelectTrigger data-testid="expense-category-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {CATEGORIES.map(c => (
                        <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Data Scadenza *</Label>
                <div className="flex gap-1 mb-2">
                  {[{label: '15gg', days: 15}, {label: '30gg', days: 30}, {label: '60gg', days: 60}, {label: 'Annuale', days: 365}].map(preset => (
                    <Button key={preset.days} type="button" variant="outline" size="sm"
                      className="text-xs flex-1"
                      onClick={() => {
                        const d = new Date();
                        d.setDate(d.getDate() + preset.days);
                        setFormData({ ...formData, due_date: d.toISOString().split('T')[0] });
                      }}
                      data-testid={`preset-${preset.days}`}>
                      {preset.label}
                    </Button>
                  ))}
                </div>
                <Input
                  type="date"
                  value={formData.due_date}
                  onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                  data-testid="expense-date-input"
                />
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-[#F8FAFC]">
                <div className="flex items-center gap-2">
                  <RotateCcw className="w-4 h-4 text-[#334155]" />
                  <Label className="font-normal">Pagamento ricorrente</Label>
                </div>
                <Switch
                  checked={formData.is_recurring}
                  onCheckedChange={(c) => setFormData({ ...formData, is_recurring: c })}
                />
              </div>
              {formData.is_recurring && (
                <div className="space-y-2">
                  <Label>Frequenza</Label>
                  <Select value={formData.recurrence} onValueChange={(v) => setFormData({ ...formData, recurrence: v })}>
                    <SelectTrigger data-testid="expense-recurrence-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {RECURRENCES.map(r => (
                        <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              <div className="space-y-2">
                <Label>Note</Label>
                <Input
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Note aggiuntive..."
                />
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }}>
                  Annulla
                </Button>
                <Button type="submit" disabled={saving} className="bg-red-500 hover:bg-red-600 text-white" data-testid="save-expense-btn">
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : editingExpense ? 'Salva' : 'Registra'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
