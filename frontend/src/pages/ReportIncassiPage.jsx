import { useState, useEffect } from 'react';
import axios from 'axios';
import * as XLSX from 'xlsx';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Euro, TrendingUp, Calendar, CreditCard, Banknote, Download, FileSpreadsheet } from 'lucide-react';
import { format, startOfDay, endOfDay, startOfWeek, endOfWeek, startOfMonth, endOfMonth, subDays } from 'date-fns';
import { it } from 'date-fns/locale';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function ReportIncassiPage() {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('today');
  const [stats, setStats] = useState({ total: 0, count: 0, cash: 0, prepaid: 0 });

  useEffect(() => {
    fetchPayments();
  }, [period]);

  const getDateRange = () => {
    const now = new Date();
    switch (period) {
      case 'today':
        return { start: startOfDay(now), end: endOfDay(now) };
      case 'yesterday':
        const yesterday = subDays(now, 1);
        return { start: startOfDay(yesterday), end: endOfDay(yesterday) };
      case 'week':
        return { start: startOfWeek(now, { weekStartsOn: 1 }), end: endOfWeek(now, { weekStartsOn: 1 }) };
      case 'month':
        return { start: startOfMonth(now), end: endOfMonth(now) };
      case 'last30':
        return { start: subDays(now, 30), end: now };
      default:
        return { start: startOfDay(now), end: endOfDay(now) };
    }
  };

  const fetchPayments = async () => {
    setLoading(true);
    try {
      const { start, end } = getDateRange();
      const res = await axios.get(`${API}/payments?start=${start.toISOString()}&end=${end.toISOString()}`);
      const data = res.data;
      setPayments(data);
      
      // Calculate stats
      const total = data.reduce((sum, p) => sum + p.total_paid, 0);
      const cash = data.filter(p => p.payment_method === 'cash').reduce((sum, p) => sum + p.total_paid, 0);
      const prepaid = data.filter(p => p.payment_method !== 'cash').reduce((sum, p) => sum + p.total_paid, 0);
      
      setStats({ total, count: data.length, cash, prepaid });
    } catch (err) {
      console.error('Error fetching payments:', err);
    } finally {
      setLoading(false);
    }
  };

  const exportToExcel = () => {
    const data = payments.map(p => ({
      'Data': p.date,
      'Cliente': p.client_name,
      'Servizi': p.services?.map(s => s.name).join(', ') || '',
      'Importo Originale': p.original_amount,
      'Sconto': p.discount_value || 0,
      'Totale Pagato': p.total_paid,
      'Metodo': p.payment_method === 'cash' ? 'Contanti' : 'Abbonamento/Prepagata'
    }));
    
    const ws = XLSX.utils.json_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Incassi');
    XLSX.writeFile(wb, `incassi_${period}_${format(new Date(), 'yyyy-MM-dd')}.xlsx`);
    toast.success('Report esportato!');
  };

  const getPeriodLabel = () => {
    switch (period) {
      case 'today': return 'Oggi';
      case 'yesterday': return 'Ieri';
      case 'week': return 'Questa settimana';
      case 'month': return 'Questo mese';
      case 'last30': return 'Ultimi 30 giorni';
      default: return '';
    }
  };

  return (
    <Layout>
      <div className="space-y-6" data-testid="report-incassi-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-4xl font-black text-black">Report Incassi</h1>
            <p className="text-[#0EA5E9] mt-1 font-bold text-lg">{getPeriodLabel()}</p>
          </div>
          <div className="flex items-center gap-3">
            <Select value={period} onValueChange={setPeriod}>
              <SelectTrigger className="w-48 border-2 border-[#0EA5E9] font-semibold">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="today">Oggi</SelectItem>
                <SelectItem value="yesterday">Ieri</SelectItem>
                <SelectItem value="week">Questa settimana</SelectItem>
                <SelectItem value="month">Questo mese</SelectItem>
                <SelectItem value="last30">Ultimi 30 giorni</SelectItem>
              </SelectContent>
            </Select>
            <Button onClick={exportToExcel} className="bg-green-600 hover:bg-green-700 text-white font-bold">
              <FileSpreadsheet className="w-4 h-4 mr-2" />
              Esporta Excel
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[1,2,3,4].map(i => <Skeleton key={i} className="h-32" />)}
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-green-100 font-semibold">Totale Incassato</p>
                      <p className="text-4xl font-black mt-2">€{stats.total.toFixed(2)}</p>
                    </div>
                    <Euro className="w-12 h-12 text-green-200" />
                  </div>
                  <p className="text-green-100 mt-2 font-medium">{stats.count} pagamenti</p>
                </CardContent>
              </Card>

              <Card className="bg-white border-2 border-[#E2E8F0]">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-[#334155] font-semibold">Contanti</p>
                      <p className="text-3xl font-black text-[#0F172A] mt-2">{'\u20AC'}{stats.cash.toFixed(2)}</p>
                    </div>
                    <Banknote className="w-10 h-10 text-green-500" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white border-2 border-[#E2E8F0]">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-[#334155] font-semibold">Abbonamento / Prepagata</p>
                      <p className="text-3xl font-black text-[#0F172A] mt-2">{'\u20AC'}{stats.prepaid.toFixed(2)}</p>
                    </div>
                    <CreditCard className="w-10 h-10 text-purple-500" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Payments List */}
            <Card className="bg-white border-2 border-[#E2E8F0]">
              <CardHeader>
                <CardTitle className="text-xl font-black text-[#0F172A]">Dettaglio Pagamenti</CardTitle>
              </CardHeader>
              <CardContent>
                {payments.length === 0 ? (
                  <div className="text-center py-12 text-[#334155]">
                    <Euro className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p className="font-semibold">Nessun pagamento in questo periodo</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {payments.map((payment) => (
                      <div key={payment.id} className="flex items-center justify-between p-4 bg-[#F8FAFC] rounded-lg border border-[#E2E8F0]">
                        <div className="flex-1">
                          <p className="font-bold text-[#0F172A]">{payment.client_name}</p>
                          <p className="text-sm text-[#334155]">{payment.services?.map(s => s.name).join(', ')}</p>
                          <p className="text-xs text-[#334155] mt-1">{payment.date}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-xl font-black text-green-600">€{payment.total_paid.toFixed(2)}</p>
                          <p className="text-xs text-[#334155] capitalize">
                            {payment.payment_method === 'cash' ? 'Contanti' : 'Abbonamento/Prepagata'}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </Layout>
  );
}
