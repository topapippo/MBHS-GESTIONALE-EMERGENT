import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import * as XLSX from 'xlsx';
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
  DialogDescription,
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
import { Users, Plus, Search, Phone, Mail, Edit2, Trash2, Loader2, History, MessageSquare, Upload, FileSpreadsheet, Euro } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function ClientsPage() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [clientHistory, setClientHistory] = useState(null);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [clientToDelete, setClientToDelete] = useState(null);
  const [editingClient, setEditingClient] = useState(null);
  const [saving, setSaving] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importPreview, setImportPreview] = useState([]);
  const fileInputRef = useRef(null);
  
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

  // Client History
  const openClientHistory = async (client) => {
    setHistoryDialogOpen(true);
    setLoadingHistory(true);
    try {
      const res = await axios.get(`${API}/clients/${client.id}/history`);
      setClientHistory(res.data);
    } catch (err) {
      toast.error('Errore nel caricamento storico');
    } finally {
      setLoadingHistory(false);
    }
  };

  // WhatsApp
  const openWhatsApp = async (client) => {
    try {
      const res = await axios.get(`${API}/clients/${client.id}/whatsapp`);
      window.open(res.data.url, '_blank');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore WhatsApp');
    }
  };

  // Excel Import Functions
  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const data = new Uint8Array(event.target.result);
        const workbook = XLSX.read(data, { type: 'array' });
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
        
        // Parse rows (skip header if present)
        const clients = [];
        for (let i = 0; i < jsonData.length; i++) {
          const row = jsonData[i];
          if (!row || row.length === 0) continue;
          
          // Try to find name in first non-empty column
          const name = String(row[0] || '').trim();
          if (!name || name.toLowerCase() === 'nome' || name.toLowerCase() === 'cliente') continue;
          
          // Look for phone, email, notes in other columns
          let phone = '';
          let email = '';
          let notes = '';
          
          for (let j = 1; j < row.length; j++) {
            const val = String(row[j] || '').trim();
            if (!val) continue;
            
            if (val.includes('@')) {
              email = val;
            } else if (/^[\d\s\+\-\.]+$/.test(val) && val.length >= 8) {
              phone = val;
            } else {
              notes = notes ? `${notes}, ${val}` : val;
            }
          }
          
          clients.push({ name, phone, email, notes });
        }
        
        setImportPreview(clients);
        setImportDialogOpen(true);
      } catch (err) {
        console.error('Error parsing Excel:', err);
        toast.error('Errore nella lettura del file Excel');
      }
    };
    reader.readAsArrayBuffer(file);
    
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleImport = async () => {
    if (importPreview.length === 0) return;
    
    setImporting(true);
    try {
      const res = await axios.post(`${API}/clients/import`, {
        clients: importPreview.map(c => ({
          name: c.name,
          phone: c.phone || '',
          email: c.email || '',
          notes: c.notes || '',
          sms_reminder: true
        }))
      });
      
      toast.success(`Importati ${res.data.imported} clienti! (${res.data.skipped} già esistenti)`);
      setImportDialogOpen(false);
      setImportPreview([]);
      fetchClients();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore nell\'importazione');
    } finally {
      setImporting(false);
    }
  };

  const filteredClients = clients.filter(client =>
    client.name.toLowerCase().includes(search.toLowerCase()) ||
    client.phone.includes(search) ||
    client.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Layout>
      <div className="space-y-6" data-testid="clients-page">
        {/* Hidden file input */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          accept=".xlsx,.xls,.csv"
          className="hidden"
        />

        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="font-playfair text-3xl font-medium text-[#0F172A]">Clienti</h1>
            <p className="text-[#334155] mt-1 font-manrope">{clients.length} clienti totali</p>
          </div>
          <div className="flex items-center gap-2">
            <Button 
              onClick={() => fileInputRef.current?.click()}
              variant="outline"
              data-testid="import-excel-btn"
              className="border-[#E2E8F0] text-[#0F172A] hover:bg-[#FAF5F2]"
            >
              <Upload className="w-5 h-5 mr-2" />
              Importa Excel
            </Button>
            <Button 
              onClick={openNewDialog}
              data-testid="new-client-btn"
              className="bg-[#0EA5E9] hover:bg-[#0284C7] text-white shadow-lg shadow-[#0EA5E9]/20"
            >
              <Plus className="w-5 h-5 mr-2" />
              Nuovo Cliente
            </Button>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#334155]" />
          <Input
            type="search"
            placeholder="Cerca cliente per nome, telefono o email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            data-testid="search-clients-input"
            className="pl-10 bg-white border-[#E2E8F0]/50 focus:border-[#0EA5E9] h-12"
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
                className="bg-white border-[#E2E8F0]/30 hover:border-[#0EA5E9]/30 transition-all duration-300 hover:-translate-y-1 shadow-[0_2px_15px_-3px_rgba(0,0,0,0.07)]"
              >
                <CardContent className="p-5">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-full bg-[#0EA5E9]/10 flex items-center justify-center">
                        <span className="text-lg font-playfair text-[#0EA5E9]">
                          {client.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <h3 className="font-medium text-[#0F172A]">{client.name}</h3>
                        <div className="flex items-center gap-1 text-xs text-[#334155]">
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
                        className="text-[#334155] hover:text-[#0EA5E9]"
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
                        className="text-[#334155] hover:text-[#E76F51]"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-2 text-sm">
                    {client.phone ? (
                      <div className="flex items-center gap-2 text-[#334155]">
                        <Phone className="w-4 h-4" />
                        <span>{client.phone}</span>
                        {client.sms_reminder && (
                          <MessageSquare className="w-3 h-3 text-[#789F8A]" title="SMS attivi" />
                        )}
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-red-500 bg-red-50 px-2 py-1.5 rounded-lg">
                        <Phone className="w-4 h-4" />
                        <span className="font-semibold text-xs">Telefono mancante!</span>
                      </div>
                    )}
                    {client.email && (
                      <div className="flex items-center gap-2 text-[#334155]">
                        <Mail className="w-4 h-4" />
                        <span className="truncate">{client.email}</span>
                      </div>
                    )}
                    {client.notes && (
                      <p className="text-[#334155] text-xs mt-3 pt-3 border-t border-[#E2E8F0]/30 italic">
                        "{client.notes.substring(0, 80)}{client.notes.length > 80 ? '...' : ''}"
                      </p>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2 mt-4 pt-3 border-t border-[#E2E8F0]/30">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => openClientHistory(client)}
                      className="flex-1 text-xs border-[#0EA5E9] text-[#0EA5E9] hover:bg-[#0EA5E9]/10"
                    >
                      <History className="w-3 h-3 mr-1" />
                      Storico
                    </Button>
                    {client.phone && (
                      <Button
                        size="sm"
                        onClick={() => openWhatsApp(client)}
                        className="flex-1 text-xs bg-green-500 hover:bg-green-600 text-white"
                      >
                        <MessageSquare className="w-3 h-3 mr-1" />
                        WhatsApp
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="bg-white border-[#E2E8F0]/30">
            <CardContent className="py-16 text-center">
              <Users className="w-16 h-16 mx-auto text-[#E2E8F0] mb-4" strokeWidth={1.5} />
              <h3 className="font-playfair text-xl text-[#0F172A] mb-2">
                {search ? 'Nessun cliente trovato' : 'Nessun cliente'}
              </h3>
              <p className="text-[#334155] mb-4">
                {search ? 'Prova con un termine diverso' : 'Aggiungi il tuo primo cliente'}
              </p>
              {!search && (
                <Button
                  onClick={openNewDialog}
                  className="bg-[#0EA5E9] hover:bg-[#0284C7] text-white"
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
              <DialogTitle className="font-playfair text-2xl text-[#0F172A]">
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
                  className="bg-[#F8FAFC] border-transparent focus:border-[#0EA5E9]"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  Telefono
                  <span className="text-xs text-orange-500 font-normal">(importante per promemoria)</span>
                </Label>
                <Input
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  placeholder="+39 ..."
                  data-testid="client-phone-input"
                  className={`border-2 ${
                    formData.phone
                      ? 'bg-[#F8FAFC] border-transparent focus:border-[#0EA5E9]'
                      : 'bg-orange-50 border-orange-300 focus:border-orange-400'
                  }`}
                />
                {!formData.phone && (
                  <p className="text-xs text-orange-500 font-medium">Senza telefono non potrai inviare promemoria WhatsApp</p>
                )}
              </div>
              <div className="space-y-2">
                <Label>Email</Label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="email@esempio.it"
                  data-testid="client-email-input"
                  className="bg-[#F8FAFC] border-transparent focus:border-[#0EA5E9]"
                />
              </div>
              <div className="space-y-2">
                <Label>Note</Label>
                <Textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Note aggiuntive..."
                  data-testid="client-notes-input"
                  className="bg-[#F8FAFC] border-transparent focus:border-[#0EA5E9] min-h-[80px]"
                />
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-[#F8FAFC]">
                <div className="flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-[#334155]" />
                  <Label className="font-normal">Promemoria SMS</Label>
                </div>
                <Switch
                  checked={formData.sms_reminder}
                  onCheckedChange={(checked) => setFormData({ ...formData, sms_reminder: checked })}
                  className="data-[state=checked]:bg-[#789F8A]"
                />
              </div>
              <DialogFooter>
                <Button
                  type="submit"
                  disabled={saving}
                  data-testid="save-client-btn"
                  className="bg-[#0EA5E9] hover:bg-[#0284C7] text-white"
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

        {/* Import Excel Dialog */}
        <Dialog open={importDialogOpen} onOpenChange={setImportDialogOpen}>
          <DialogContent className="sm:max-w-[600px]">
            <DialogHeader>
              <DialogTitle className="font-playfair text-2xl text-[#0F172A] flex items-center gap-2">
                <FileSpreadsheet className="w-6 h-6 text-[#0EA5E9]" />
                Importa Clienti da Excel
              </DialogTitle>
              <DialogDescription>
                Anteprima dei clienti da importare. Verifica i dati prima di confermare.
              </DialogDescription>
            </DialogHeader>
            <div className="mt-4">
              {importPreview.length > 0 ? (
                <>
                  <div className="max-h-[300px] overflow-y-auto border border-[#E2E8F0]/30 rounded-lg">
                    <table className="w-full text-sm">
                      <thead className="bg-[#F8FAFC] sticky top-0">
                        <tr>
                          <th className="text-left p-3 font-medium text-[#0F172A]">Nome</th>
                          <th className="text-left p-3 font-medium text-[#0F172A]">Telefono</th>
                          <th className="text-left p-3 font-medium text-[#0F172A]">Note</th>
                        </tr>
                      </thead>
                      <tbody>
                        {importPreview.map((client, idx) => (
                          <tr key={idx} className="border-t border-[#E2E8F0]/20 hover:bg-[#FAF5F2]">
                            <td className="p-3 text-[#0F172A]">{client.name}</td>
                            <td className="p-3 text-[#334155]">{client.phone || '-'}</td>
                            <td className="p-3 text-[#334155] text-xs max-w-[200px] truncate">{client.notes || '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="text-sm text-[#334155] mt-3">
                    Totale: <span className="font-medium text-[#0F172A]">{importPreview.length}</span> clienti da importare
                  </p>
                </>
              ) : (
                <p className="text-center text-[#334155] py-8">Nessun cliente trovato nel file</p>
              )}
            </div>
            <DialogFooter className="mt-4">
              <Button
                variant="outline"
                onClick={() => setImportDialogOpen(false)}
                className="border-[#E2E8F0]"
              >
                Annulla
              </Button>
              <Button
                onClick={handleImport}
                disabled={importing || importPreview.length === 0}
                className="bg-[#0EA5E9] hover:bg-[#0284C7] text-white"
              >
                {importing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    Importando...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    Importa {importPreview.length} Clienti
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Client History Dialog */}
        <Dialog open={historyDialogOpen} onOpenChange={setHistoryDialogOpen}>
          <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="font-playfair text-2xl text-[#0F172A] flex items-center gap-2">
                <History className="w-6 h-6 text-[#0EA5E9]" />
                Storico Cliente
              </DialogTitle>
              {clientHistory && (
                <DialogDescription>
                  {clientHistory.client.name}
                </DialogDescription>
              )}
            </DialogHeader>
            
            {loadingHistory ? (
              <div className="space-y-3">
                <Skeleton className="h-20" />
                <Skeleton className="h-20" />
              </div>
            ) : clientHistory ? (
              <div className="space-y-4">
                {/* Stats */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-4 bg-[#0EA5E9]/10 rounded-lg text-center">
                    <p className="text-2xl font-black text-[#0EA5E9]">{clientHistory.total_visits}</p>
                    <p className="text-xs text-[#334155] font-semibold">Visite</p>
                  </div>
                  <div className="p-4 bg-green-100 rounded-lg text-center">
                    <p className="text-2xl font-black text-green-600">€{clientHistory.total_spent.toFixed(0)}</p>
                    <p className="text-xs text-[#334155] font-semibold">Totale Speso</p>
                  </div>
                  <div className="p-4 bg-amber-100 rounded-lg text-center">
                    <p className="text-2xl font-black text-amber-600">{clientHistory.loyalty_points ?? 0}</p>
                    <p className="text-xs text-[#334155] font-semibold">Punti Fedeltà</p>
                  </div>
                  <div className="p-4 bg-purple-100 rounded-lg text-center">
                    <p className="text-sm font-black text-purple-600">{clientHistory.last_visit || '-'}</p>
                    <p className="text-xs text-[#334155] font-semibold">Ultima Visita</p>
                  </div>
                </div>

                {/* Active Rewards */}
                {clientHistory.active_rewards?.length > 0 && (
                  <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                    <p className="text-sm font-bold text-green-800 mb-1">Premi Disponibili</p>
                    <div className="flex flex-wrap gap-2">
                      {clientHistory.active_rewards.map((r, idx) => (
                        <span key={idx} className="text-xs bg-green-200 text-green-800 px-2 py-1 rounded-full font-semibold">
                          {r.reward_name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Appointments */}
                <div>
                  <h3 className="font-bold text-[#0F172A] mb-2">Appuntamenti</h3>
                  {clientHistory.appointments.length === 0 ? (
                    <p className="text-[#334155] text-sm">Nessun appuntamento</p>
                  ) : (
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {clientHistory.appointments.slice(0, 20).map((apt) => (
                        <div key={apt.id} className="p-3 bg-[#F8FAFC] rounded-lg border border-[#E2E8F0]">
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-semibold text-[#0F172A]">{apt.date} - {apt.time}</p>
                              <p className="text-sm text-[#334155]">{apt.services?.map(s => s.name).join(', ')}</p>
                            </div>
                            <span className={`text-xs px-2 py-1 rounded ${apt.paid ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                              {apt.paid ? 'Pagato' : 'Da pagare'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Payments */}
                {clientHistory.payments.length > 0 && (
                  <div>
                    <h3 className="font-bold text-[#0F172A] mb-2">Pagamenti</h3>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {clientHistory.payments.slice(0, 10).map((pay) => (
                        <div key={pay.id} className="p-3 bg-green-50 rounded-lg flex justify-between items-center">
                          <div>
                            <p className="font-semibold text-[#0F172A]">{pay.date}</p>
                            <p className="text-xs text-[#334155] capitalize">{pay.payment_method}</p>
                          </div>
                          <p className="font-black text-green-600">€{pay.total_paid.toFixed(2)}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : null}
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
