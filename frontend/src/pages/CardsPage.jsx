import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
  DialogDescription,
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
import { CreditCard, Plus, Euro, Calendar, Loader2, Trash2, RefreshCw, History } from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function CardsPage() {
  const [cards, setCards] = useState([]);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [rechargeDialogOpen, setRechargeDialogOpen] = useState(false);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedCard, setSelectedCard] = useState(null);
  const [saving, setSaving] = useState(false);
  const [showInactive, setShowInactive] = useState(false);
  
  const [formData, setFormData] = useState({
    client_id: '',
    card_type: 'prepaid',
    name: '',
    total_value: '',
    total_services: '',
    valid_until: '',
    notes: ''
  });
  
  const [rechargeAmount, setRechargeAmount] = useState('');

  useEffect(() => {
    fetchData();
  }, [showInactive]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [cardsRes, clientsRes] = await Promise.all([
        axios.get(`${API}/cards?active_only=${!showInactive}`),
        axios.get(`${API}/clients`)
      ]);
      setCards(cardsRes.data);
      setClients(clientsRes.data);
    } catch (err) {
      console.error('Error fetching data:', err);
      toast.error('Errore nel caricamento');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.client_id || !formData.name || !formData.total_value) {
      toast.error('Compila tutti i campi obbligatori');
      return;
    }

    setSaving(true);
    try {
      await axios.post(`${API}/cards`, {
        client_id: formData.client_id,
        card_type: formData.card_type,
        name: formData.name,
        total_value: parseFloat(formData.total_value),
        total_services: formData.total_services ? parseInt(formData.total_services) : null,
        valid_until: formData.valid_until || null,
        notes: formData.notes
      });
      toast.success('Card creata con successo!');
      setDialogOpen(false);
      setFormData({
        client_id: '',
        card_type: 'prepaid',
        name: '',
        total_value: '',
        total_services: '',
        valid_until: '',
        notes: ''
      });
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore nella creazione');
    } finally {
      setSaving(false);
    }
  };

  const handleRecharge = async () => {
    if (!selectedCard || !rechargeAmount) return;
    
    setSaving(true);
    try {
      await axios.post(`${API}/cards/${selectedCard.id}/recharge?amount=${parseFloat(rechargeAmount)}`);
      toast.success('Ricarica effettuata!');
      setRechargeDialogOpen(false);
      setRechargeAmount('');
      setSelectedCard(null);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore nella ricarica');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedCard) return;
    try {
      await axios.delete(`${API}/cards/${selectedCard.id}`);
      toast.success('Card eliminata');
      setDeleteDialogOpen(false);
      setSelectedCard(null);
      fetchData();
    } catch (err) {
      toast.error('Errore nell\'eliminazione');
    }
  };

  const getCardTypeLabel = (type) => {
    return type === 'prepaid' ? 'Prepagata' : 'Abbonamento';
  };

  const getCardProgress = (card) => {
    if (card.total_services) {
      return (card.used_services / card.total_services) * 100;
    }
    return ((card.total_value - card.remaining_value) / card.total_value) * 100;
  };

  // Preset card templates
  const presets = [
    { name: 'Card 10 Pieghe', value: 200, services: 10, type: 'prepaid' },
    { name: 'Card 5 Tagli', value: 150, services: 5, type: 'prepaid' },
    { name: 'Abbonamento Mensile', value: 100, services: null, type: 'subscription' },
    { name: 'Card Prepagata €50', value: 50, services: null, type: 'prepaid' },
    { name: 'Card Prepagata €100', value: 100, services: null, type: 'prepaid' },
  ];

  const applyPreset = (preset) => {
    setFormData({
      ...formData,
      name: preset.name,
      total_value: preset.value.toString(),
      total_services: preset.services?.toString() || '',
      card_type: preset.type
    });
  };

  return (
    <Layout>
      <div className="space-y-6" data-testid="cards-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="font-playfair text-3xl font-medium text-[#44403C]">Card & Abbonamenti</h1>
            <p className="text-[#78716C] mt-1 font-manrope">
              {cards.length} card {showInactive ? 'totali' : 'attive'}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => setShowInactive(!showInactive)}
              className={`border-[#E6CCB2] ${showInactive ? 'bg-[#FAF5F2]' : ''}`}
            >
              {showInactive ? 'Solo attive' : 'Mostra tutte'}
            </Button>
            <Button
              onClick={() => setDialogOpen(true)}
              data-testid="new-card-btn"
              className="bg-[#C58970] hover:bg-[#B07860] text-white shadow-lg shadow-[#C58970]/20"
            >
              <Plus className="w-5 h-5 mr-2" />
              Nuova Card
            </Button>
          </div>
        </div>

        {/* Cards Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-48" />
            ))}
          </div>
        ) : cards.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {cards.map((card) => (
              <Card
                key={card.id}
                data-testid={`card-${card.id}`}
                className={`bg-white border-[#E6CCB2]/30 hover:border-[#C58970]/30 transition-all duration-300 ${
                  !card.active ? 'opacity-60' : ''
                }`}
              >
                <CardContent className="p-5">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <Badge 
                          variant="outline"
                          className={card.card_type === 'prepaid' 
                            ? 'border-[#C58970] text-[#C58970]' 
                            : 'border-[#789F8A] text-[#789F8A]'
                          }
                        >
                          {getCardTypeLabel(card.card_type)}
                        </Badge>
                        {!card.active && (
                          <Badge variant="outline" className="border-[#78716C] text-[#78716C]">
                            Esaurita
                          </Badge>
                        )}
                      </div>
                      <h3 className="font-medium text-[#44403C]">{card.name}</h3>
                      <p className="text-sm text-[#78716C]">{card.client_name}</p>
                    </div>
                    <CreditCard className="w-8 h-8 text-[#E6CCB2]" strokeWidth={1.5} />
                  </div>

                  {/* Progress bar */}
                  <div className="mb-3">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-[#78716C]">Credito residuo</span>
                      <span className="font-semibold text-[#44403C]">€{card.remaining_value.toFixed(2)}</span>
                    </div>
                    <div className="h-2 bg-[#E6CCB2]/30 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-[#C58970] rounded-full transition-all"
                        style={{ width: `${100 - getCardProgress(card)}%` }}
                      />
                    </div>
                    {card.total_services && (
                      <p className="text-xs text-[#78716C] mt-1">
                        {card.used_services}/{card.total_services} servizi utilizzati
                      </p>
                    )}
                  </div>

                  {/* Valid until */}
                  {card.valid_until && (
                    <p className="text-xs text-[#78716C] flex items-center gap-1 mb-3">
                      <Calendar className="w-3 h-3" />
                      Valida fino al {format(new Date(card.valid_until), 'd MMM yyyy', { locale: it })}
                    </p>
                  )}

                  {/* Actions */}
                  <div className="flex items-center gap-2 pt-3 border-t border-[#E6CCB2]/30">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setSelectedCard(card);
                        setRechargeDialogOpen(true);
                      }}
                      className="flex-1 border-[#E6CCB2] text-[#44403C] hover:bg-[#FAF5F2]"
                    >
                      <RefreshCw className="w-4 h-4 mr-1" />
                      Ricarica
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setSelectedCard(card);
                        setHistoryDialogOpen(true);
                      }}
                      className="text-[#78716C]"
                    >
                      <History className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setSelectedCard(card);
                        setDeleteDialogOpen(true);
                      }}
                      className="text-[#78716C] hover:text-[#E76F51]"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="bg-white border-[#E6CCB2]/30">
            <CardContent className="py-16 text-center">
              <CreditCard className="w-16 h-16 mx-auto text-[#E6CCB2] mb-4" strokeWidth={1.5} />
              <h3 className="font-playfair text-xl text-[#44403C] mb-2">Nessuna card</h3>
              <p className="text-[#78716C] mb-4">Crea la prima card prepagata o abbonamento</p>
              <Button
                onClick={() => setDialogOpen(true)}
                className="bg-[#C58970] hover:bg-[#B07860] text-white"
              >
                <Plus className="w-4 h-4 mr-2" /> Nuova Card
              </Button>
            </CardContent>
          </Card>
        )}

        {/* New Card Dialog */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle className="font-playfair text-2xl text-[#44403C]">
                Nuova Card
              </DialogTitle>
              <DialogDescription>
                Crea una card prepagata o un abbonamento per un cliente
              </DialogDescription>
            </DialogHeader>
            
            {/* Presets */}
            <div className="flex flex-wrap gap-2 mb-4">
              {presets.map((preset) => (
                <Button
                  key={preset.name}
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => applyPreset(preset)}
                  className="border-[#E6CCB2] text-xs"
                >
                  {preset.name}
                </Button>
              ))}
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>Cliente *</Label>
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
                  <Label>Tipo *</Label>
                  <Select
                    value={formData.card_type}
                    onValueChange={(val) => setFormData({ ...formData, card_type: val })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="prepaid">Prepagata</SelectItem>
                      <SelectItem value="subscription">Abbonamento</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Nome Card *</Label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Es. Card 10 Pieghe"
                    className="bg-[#FAFAF9]"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Valore Totale (€) *</Label>
                  <Input
                    type="number"
                    min="0"
                    step="0.01"
                    value={formData.total_value}
                    onChange={(e) => setFormData({ ...formData, total_value: e.target.value })}
                    placeholder="100.00"
                    className="bg-[#FAFAF9]"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>N° Servizi (opzionale)</Label>
                  <Input
                    type="number"
                    min="1"
                    value={formData.total_services}
                    onChange={(e) => setFormData({ ...formData, total_services: e.target.value })}
                    placeholder="Es. 10"
                    className="bg-[#FAFAF9]"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Scadenza (opzionale)</Label>
                <Input
                  type="date"
                  value={formData.valid_until}
                  onChange={(e) => setFormData({ ...formData, valid_until: e.target.value })}
                  className="bg-[#FAFAF9]"
                />
              </div>

              <div className="space-y-2">
                <Label>Note</Label>
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
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Crea Card'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Recharge Dialog */}
        <Dialog open={rechargeDialogOpen} onOpenChange={setRechargeDialogOpen}>
          <DialogContent className="sm:max-w-[400px]">
            <DialogHeader>
              <DialogTitle className="font-playfair text-2xl text-[#44403C]">
                Ricarica Card
              </DialogTitle>
              <DialogDescription>
                {selectedCard?.name} - {selectedCard?.client_name}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div className="p-4 bg-[#FAFAF9] rounded-lg">
                <p className="text-sm text-[#78716C]">Credito attuale</p>
                <p className="text-2xl font-playfair text-[#44403C]">
                  €{selectedCard?.remaining_value.toFixed(2)}
                </p>
              </div>
              <div className="space-y-2">
                <Label>Importo Ricarica (€)</Label>
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={rechargeAmount}
                  onChange={(e) => setRechargeAmount(e.target.value)}
                  placeholder="50.00"
                  className="bg-[#FAFAF9]"
                />
              </div>
              <DialogFooter>
                <Button
                  onClick={handleRecharge}
                  disabled={saving || !rechargeAmount}
                  className="bg-[#C58970] hover:bg-[#B07860] text-white"
                >
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Ricarica'}
                </Button>
              </DialogFooter>
            </div>
          </DialogContent>
        </Dialog>

        {/* History Dialog */}
        <Dialog open={historyDialogOpen} onOpenChange={setHistoryDialogOpen}>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle className="font-playfair text-2xl text-[#44403C]">
                Storico Transazioni
              </DialogTitle>
              <DialogDescription>
                {selectedCard?.name} - {selectedCard?.client_name}
              </DialogDescription>
            </DialogHeader>
            <div className="mt-4 max-h-[300px] overflow-y-auto">
              {selectedCard?.transactions?.length > 0 ? (
                <div className="space-y-2">
                  {selectedCard.transactions.slice().reverse().map((tx) => (
                    <div
                      key={tx.id}
                      className="flex items-center justify-between p-3 bg-[#FAFAF9] rounded-lg"
                    >
                      <div>
                        <p className="text-sm text-[#44403C]">{tx.description}</p>
                        <p className="text-xs text-[#78716C]">
                          {format(new Date(tx.date), 'd MMM yyyy HH:mm', { locale: it })}
                        </p>
                      </div>
                      <span className={`font-semibold ${tx.amount < 0 ? 'text-[#789F8A]' : 'text-[#E76F51]'}`}>
                        {tx.amount < 0 ? '+' : '-'}€{Math.abs(tx.amount).toFixed(2)}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-[#78716C] py-8">Nessuna transazione</p>
              )}
            </div>
          </DialogContent>
        </Dialog>

        {/* Delete Dialog */}
        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Elimina Card</AlertDialogTitle>
              <AlertDialogDescription>
                Sei sicura di voler eliminare questa card? L'azione non può essere annullata.
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
