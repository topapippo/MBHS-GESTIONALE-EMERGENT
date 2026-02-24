import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Textarea } from '@/components/ui/textarea';
import { Users, Plus, Search, Phone, Mail, Edit2, Trash2, Loader2, History, MessageSquare } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function ClientsPage() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [clientToDelete, setClientToDelete] = useState(null);
  const [editingClient, setEditingClient] = useState(null);
  const [saving, setSaving] = useState(false);
  
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    email: '',
    notes: '',
    sms_reminder: true
  });

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      const res = await axios.get(`${API}/clients`);
      setClients(res.data);
    } catch (err) {
      console.error('Error fetching clients:', err);
      toast.error('Errore nel caricamento dei clienti');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error('Inserisci il nome del cliente');
      return;
    }
    
    setSaving(true);
    try {
      if (editingClient) {
        await axios.put(`${API}/clients/${editingClient.id}`, formData);
        toast.success('Cliente aggiornato!');
      } else {
        await axios.post(`${API}/clients`, formData);
        toast.success('Cliente aggiunto!');
      }
      setDialogOpen(false);
      setEditingClient(null);
      setFormData({ name: '', phone: '', email: '', notes: '', sms_reminder: true });
      fetchClients();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore nel salvataggio');
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (client) => {
    setEditingClient(client);
    setFormData({
      name: client.name,
      phone: client.phone,
      email: client.email,
      notes: client.notes,
      sms_reminder: client.sms_reminder !== false
    });
    setDialogOpen(true);
  };

  const handleDelete = async () => {
    if (!clientToDelete) return;
    try {
      await axios.delete(`${API}/clients/${clientToDelete}`);
      toast.success('Cliente eliminato');
      setDeleteDialogOpen(false);
      setClientToDelete(null);
      fetchClients();
    } catch (err) {
      toast.error('Errore nell\'eliminazione');
    }
  };

  const openNewDialog = () => {
    setEditingClient(null);
    setFormData({ name: '', phone: '', email: '', notes: '', sms_reminder: true });
    setDialogOpen(true);
  };

  const filteredClients = clients.filter(client =>
    client.name.toLowerCase().includes(search.toLowerCase()) ||
    client.phone.includes(search) ||
    client.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Layout>
      <div className="space-y-6" data-testid="clients-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="font-playfair text-3xl font-medium text-[#44403C]">Clienti</h1>
            <p className="text-[#78716C] mt-1 font-manrope">{clients.length} clienti totali</p>
          </div>
          <Button 
            onClick={openNewDialog}
            data-testid="new-client-btn"
            className="bg-[#C58970] hover:bg-[#B07860] text-white shadow-lg shadow-[#C58970]/20"
          >
            <Plus className="w-5 h-5 mr-2" />
            Nuovo Cliente
          </Button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#78716C]" />
          <Input
            type="search"
            placeholder="Cerca cliente per nome, telefono o email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            data-testid="search-clients-input"
            className="pl-10 bg-white border-[#E6CCB2]/50 focus:border-[#C58970] h-12"
          />
        </div>

        {/* Clients Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Skeleton key={i} className="h-48" />
            ))}
          </div>
        ) : filteredClients.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredClients.map((client) => (
              <Card
                key={client.id}
                data-testid={`client-card-${client.id}`}
                className="bg-white border-[#E6CCB2]/30 hover:border-[#C58970]/30 transition-all duration-300 hover:-translate-y-1 shadow-[0_2px_15px_-3px_rgba(0,0,0,0.07)]"
              >
                <CardContent className="p-5">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-full bg-[#C58970]/10 flex items-center justify-center">
                        <span className="text-lg font-playfair text-[#C58970]">
                          {client.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <h3 className="font-medium text-[#44403C]">{client.name}</h3>
                        <div className="flex items-center gap-1 text-xs text-[#78716C]">
                          <History className="w-3 h-3" />
                          {client.total_visits} visite
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <Button
                        size="icon"
                        variant="ghost"
                        onClick={() => handleEdit(client)}
                        className="text-[#78716C] hover:text-[#C58970]"
                      >
                        <Edit2 className="w-4 h-4" />
                      </Button>
                      <Button
                        size="icon"
                        variant="ghost"
                        onClick={() => {
                          setClientToDelete(client.id);
                          setDeleteDialogOpen(true);
                        }}
                        className="text-[#78716C] hover:text-[#E76F51]"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-2 text-sm">
                    {client.phone && (
                      <div className="flex items-center gap-2 text-[#78716C]">
                        <Phone className="w-4 h-4" />
                        <span>{client.phone}</span>
                        {client.sms_reminder && (
                          <MessageSquare className="w-3 h-3 text-[#789F8A]" title="SMS attivi" />
                        )}
                      </div>
                    )}
                    {client.email && (
                      <div className="flex items-center gap-2 text-[#78716C]">
                        <Mail className="w-4 h-4" />
                        <span className="truncate">{client.email}</span>
                      </div>
                    )}
                    {client.notes && (
                      <p className="text-[#78716C] text-xs mt-3 pt-3 border-t border-[#E6CCB2]/30 italic">
                        "{client.notes}"
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="bg-white border-[#E6CCB2]/30">
            <CardContent className="py-16 text-center">
              <Users className="w-16 h-16 mx-auto text-[#E6CCB2] mb-4" strokeWidth={1.5} />
              <h3 className="font-playfair text-xl text-[#44403C] mb-2">
                {search ? 'Nessun cliente trovato' : 'Nessun cliente'}
              </h3>
              <p className="text-[#78716C] mb-4">
                {search ? 'Prova con un termine diverso' : 'Aggiungi il tuo primo cliente'}
              </p>
              {!search && (
                <Button
                  onClick={openNewDialog}
                  className="bg-[#C58970] hover:bg-[#B07860] text-white"
                >
                  <Plus className="w-4 h-4 mr-2" /> Aggiungi Cliente
                </Button>
              )}
            </CardContent>
          </Card>
        )}

        {/* Add/Edit Dialog */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle className="font-playfair text-2xl text-[#44403C]">
                {editingClient ? 'Modifica Cliente' : 'Nuovo Cliente'}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label>Nome *</Label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Nome cliente"
                  data-testid="client-name-input"
                  className="bg-[#FAFAF9] border-transparent focus:border-[#C58970]"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Telefono</Label>
                <Input
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  placeholder="+39 ..."
                  data-testid="client-phone-input"
                  className="bg-[#FAFAF9] border-transparent focus:border-[#C58970]"
                />
              </div>
              <div className="space-y-2">
                <Label>Email</Label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="email@esempio.it"
                  data-testid="client-email-input"
                  className="bg-[#FAFAF9] border-transparent focus:border-[#C58970]"
                />
              </div>
              <div className="space-y-2">
                <Label>Note</Label>
                <Textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Note aggiuntive..."
                  data-testid="client-notes-input"
                  className="bg-[#FAFAF9] border-transparent focus:border-[#C58970] min-h-[80px]"
                />
              </div>
              <DialogFooter>
                <Button
                  type="submit"
                  disabled={saving}
                  data-testid="save-client-btn"
                  className="bg-[#C58970] hover:bg-[#B07860] text-white"
                >
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : editingClient ? 'Salva Modifiche' : 'Aggiungi Cliente'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation */}
        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Elimina Cliente</AlertDialogTitle>
              <AlertDialogDescription>
                Sei sicura di voler eliminare questo cliente? L'azione non può essere annullata.
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
