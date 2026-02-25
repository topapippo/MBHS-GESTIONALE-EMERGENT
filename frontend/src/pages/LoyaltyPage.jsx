import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
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
import { Star, Gift, Search, Trophy, TrendingUp, Award, ChevronRight, Clock, Minus, Plus } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function LoyaltyPage() {
  const [loyalties, setLoyalties] = useState([]);
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedClient, setSelectedClient] = useState(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [clientLoyalty, setClientLoyalty] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [redeemOpen, setRedeemOpen] = useState(false);
  const [redeemType, setRedeemType] = useState('');
  const [redeeming, setRedeeming] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [loyRes, configRes] = await Promise.all([
        axios.get(`${API}/loyalty`),
        axios.get(`${API}/loyalty/config`)
      ]);
      setLoyalties(loyRes.data);
      setConfig(configRes.data);
    } catch (err) {
      console.error(err);
      toast.error('Errore nel caricamento dei dati fedeltà');
    } finally {
      setLoading(false);
    }
  };

  const openClientDetail = async (loy) => {
    setSelectedClient(loy);
    setDetailOpen(true);
    setLoadingDetail(true);
    try {
      const res = await axios.get(`${API}/loyalty/${loy.client_id}`);
      setClientLoyalty(res.data);
    } catch (err) {
      toast.error('Errore nel caricamento dettagli');
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleRedeem = async () => {
    if (!selectedClient || !redeemType) return;
    setRedeeming(true);
    try {
      await axios.post(`${API}/loyalty/${selectedClient.client_id}/redeem`, {
        reward_type: redeemType
      });
      toast.success('Premio riscattato con successo!');
      setRedeemOpen(false);
      setRedeemType('');
      // Refresh data
      const res = await axios.get(`${API}/loyalty/${selectedClient.client_id}`);
      setClientLoyalty(res.data);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore nel riscatto');
    } finally {
      setRedeeming(false);
    }
  };

  const handleUseReward = async (rewardId) => {
    if (!selectedClient) return;
    try {
      await axios.post(`${API}/loyalty/${selectedClient.client_id}/use-reward/${rewardId}`);
      toast.success('Premio utilizzato!');
      const res = await axios.get(`${API}/loyalty/${selectedClient.client_id}`);
      setClientLoyalty(res.data);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore');
    }
  };

  const filtered = loyalties.filter(l =>
    l.client_name?.toLowerCase().includes(search.toLowerCase())
  );

  const totalPoints = loyalties.reduce((sum, l) => sum + l.points, 0);
  const clientsWithRewards = loyalties.filter(l => l.points >= 5).length;

  if (loading) {
    return (
      <Layout>
        <div className="space-y-4">
          <Skeleton className="h-12 w-64" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Skeleton className="h-28" />
            <Skeleton className="h-28" />
            <Skeleton className="h-28" />
          </div>
          <Skeleton className="h-64" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6" data-testid="loyalty-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-black text-[#0F172A] flex items-center gap-3">
              <Star className="w-7 h-7 text-amber-500" />
              Programma Fedeltà
            </h1>
            <p className="text-[#334155] mt-1">1 punto ogni €{config?.points_per_euro || 10} spesi</p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card className="bg-gradient-to-br from-amber-50 to-amber-100 border-amber-200">
            <CardContent className="p-5">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-amber-500 rounded-xl">
                  <Star className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-sm text-amber-700 font-semibold">Punti Totali in Circolo</p>
                  <p className="text-3xl font-black text-amber-600" data-testid="total-points">{totalPoints}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
            <CardContent className="p-5">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-[#0EA5E9] rounded-xl">
                  <Trophy className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-sm text-blue-700 font-semibold">Clienti Iscritti</p>
                  <p className="text-3xl font-black text-[#0EA5E9]" data-testid="total-enrolled">{loyalties.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
            <CardContent className="p-5">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-green-500 rounded-xl">
                  <Gift className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-sm text-green-700 font-semibold">Con Premi Disponibili</p>
                  <p className="text-3xl font-black text-green-600" data-testid="clients-with-rewards">{clientsWithRewards}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Rewards Info */}
        <Card className="border-[#E2E8F0]/30">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-bold text-[#0F172A] flex items-center gap-2">
              <Gift className="w-5 h-5 text-[#0EA5E9]" />
              Premi Disponibili
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 bg-purple-50 rounded-xl border border-purple-200">
                <div className="flex items-center gap-2 mb-2">
                  <Award className="w-5 h-5 text-purple-600" />
                  <h3 className="font-bold text-purple-800">Sconto 10% Colorazione</h3>
                </div>
                <p className="text-sm text-purple-600 mb-2">Sconto del 10% sul prossimo servizio di colorazione</p>
                <div className="flex items-center gap-1">
                  <Star className="w-4 h-4 text-amber-500" />
                  <span className="text-sm font-black text-purple-700">5 punti necessari</span>
                </div>
              </div>
              <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-200">
                <div className="flex items-center gap-2 mb-2">
                  <Trophy className="w-5 h-5 text-emerald-600" />
                  <h3 className="font-bold text-emerald-800">Taglio Gratuito</h3>
                </div>
                <p className="text-sm text-emerald-600 mb-2">Un taglio completamente gratuito</p>
                <div className="flex items-center gap-1">
                  <Star className="w-4 h-4 text-amber-500" />
                  <span className="text-sm font-black text-emerald-700">10 punti necessari</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#334155]" />
          <Input
            placeholder="Cerca cliente..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            data-testid="loyalty-search"
            className="pl-10 bg-white border-[#E2E8F0] focus:border-[#0EA5E9] h-11"
          />
        </div>

        {/* Client Loyalty List */}
        {filtered.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.sort((a, b) => b.points - a.points).map((loy) => (
              <Card
                key={loy.id}
                className="bg-white border-[#E2E8F0]/30 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => openClientDetail(loy)}
                data-testid={`loyalty-card-${loy.client_id}`}
              >
                <CardContent className="p-5">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-bold text-[#0F172A] truncate">{loy.client_name}</h3>
                      {loy.client_phone && (
                        <p className="text-sm text-[#334155] mt-0.5">{loy.client_phone}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-1 bg-amber-100 px-3 py-1.5 rounded-full ml-2 shrink-0">
                      <Star className="w-4 h-4 text-amber-500" />
                      <span className="text-lg font-black text-amber-600">{loy.points}</span>
                    </div>
                  </div>
                  
                  {/* Progress bars for rewards */}
                  <div className="mt-4 space-y-2">
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-purple-600 font-semibold">Sconto Colorazione</span>
                        <span className="font-bold text-purple-700">{Math.min(loy.points, 5)}/5</span>
                      </div>
                      <div className="h-2 bg-purple-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-purple-500 rounded-full transition-all"
                          style={{ width: `${Math.min(100, (loy.points / 5) * 100)}%` }}
                        />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-emerald-600 font-semibold">Taglio Gratuito</span>
                        <span className="font-bold text-emerald-700">{Math.min(loy.points, 10)}/10</span>
                      </div>
                      <div className="h-2 bg-emerald-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-emerald-500 rounded-full transition-all"
                          style={{ width: `${Math.min(100, (loy.points / 10) * 100)}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Active unredeemed rewards */}
                  {loy.active_rewards?.filter(r => !r.redeemed).length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {loy.active_rewards.filter(r => !r.redeemed).map((r) => (
                        <span key={r.id} className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-semibold">
                          {r.reward_name}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="mt-3 flex items-center text-xs text-[#334155]">
                    <TrendingUp className="w-3 h-3 mr-1" />
                    Totale guadagnati: {loy.total_points_earned}
                    <ChevronRight className="w-4 h-4 ml-auto text-[#CBD5E1]" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="bg-white border-[#E2E8F0]/30">
            <CardContent className="py-16 text-center">
              <Star className="w-16 h-16 mx-auto text-[#E2E8F0] mb-4" strokeWidth={1.5} />
              <h3 className="text-xl font-bold text-[#0F172A] mb-2">
                {search ? 'Nessun risultato' : 'Nessun cliente nel programma fedeltà'}
              </h3>
              <p className="text-[#334155]">
                {search ? 'Prova con un termine diverso' : 'I punti vengono assegnati automaticamente al checkout'}
              </p>
            </CardContent>
          </Card>
        )}

        {/* Client Detail Dialog */}
        <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
          <DialogContent className="sm:max-w-[550px] max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-2xl font-black text-[#0F172A] flex items-center gap-2">
                <Star className="w-6 h-6 text-amber-500" />
                {selectedClient?.client_name}
              </DialogTitle>
              <DialogDescription>Dettagli programma fedeltà</DialogDescription>
            </DialogHeader>

            {loadingDetail ? (
              <div className="space-y-3">
                <Skeleton className="h-20" />
                <Skeleton className="h-20" />
              </div>
            ) : clientLoyalty ? (
              <div className="space-y-5">
                {/* Points Summary */}
                <div className="flex items-center justify-center gap-2 bg-gradient-to-r from-amber-50 to-amber-100 p-6 rounded-xl border border-amber-200">
                  <Star className="w-8 h-8 text-amber-500" />
                  <span className="text-5xl font-black text-amber-600" data-testid="client-points">{clientLoyalty.points}</span>
                  <span className="text-lg font-semibold text-amber-700 ml-1">punti</span>
                </div>

                {/* Redeem Rewards */}
                <div className="space-y-3">
                  <h3 className="font-bold text-[#0F172A]">Riscatta Premi</h3>
                  {Object.entries(LOYALTY_REWARDS_UI).map(([key, reward]) => {
                    const reqPoints = config?.rewards?.[key]?.points_required || reward.pointsReq;
                    const canRedeem = clientLoyalty.points >= reqPoints;
                    return (
                      <div
                        key={key}
                        className={`p-4 rounded-xl border-2 flex items-center justify-between ${
                          canRedeem ? 'border-green-300 bg-green-50' : 'border-[#E2E8F0] bg-[#F8FAFC] opacity-60'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg ${reward.bgColor}`}>
                            {reward.icon}
                          </div>
                          <div>
                            <p className="font-bold text-[#0F172A]">{reward.name}</p>
                            <p className="text-xs text-[#334155]">{reqPoints} punti</p>
                          </div>
                        </div>
                        <Button
                          size="sm"
                          disabled={!canRedeem}
                          onClick={() => {
                            setRedeemType(key);
                            setRedeemOpen(true);
                          }}
                          className={canRedeem ? 'bg-amber-500 hover:bg-amber-600 text-white' : ''}
                          data-testid={`redeem-${key}-btn`}
                        >
                          <Gift className="w-4 h-4 mr-1" />
                          Riscatta
                        </Button>
                      </div>
                    );
                  })}
                </div>

                {/* Active Rewards */}
                {clientLoyalty.active_rewards?.filter(r => !r.redeemed).length > 0 && (
                  <div className="space-y-3">
                    <h3 className="font-bold text-[#0F172A]">Premi da Utilizzare</h3>
                    {clientLoyalty.active_rewards.filter(r => !r.redeemed).map((r) => (
                      <div key={r.id} className="p-4 bg-green-50 rounded-xl border border-green-200 flex items-center justify-between">
                        <div>
                          <p className="font-bold text-green-800">{r.reward_name}</p>
                          <p className="text-xs text-green-600">
                            <Clock className="w-3 h-3 inline mr-1" />
                            Riscattato il {new Date(r.created_at).toLocaleDateString('it-IT')}
                          </p>
                        </div>
                        <Button
                          size="sm"
                          onClick={() => handleUseReward(r.id)}
                          className="bg-green-600 hover:bg-green-700 text-white"
                          data-testid={`use-reward-${r.id}`}
                        >
                          Usa Ora
                        </Button>
                      </div>
                    ))}
                  </div>
                )}

                {/* History */}
                <div className="space-y-2">
                  <h3 className="font-bold text-[#0F172A]">Storico Punti</h3>
                  {clientLoyalty.history?.length > 0 ? (
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {[...clientLoyalty.history].reverse().slice(0, 20).map((h) => (
                        <div key={h.id} className="flex items-center justify-between p-3 bg-[#F8FAFC] rounded-lg border border-[#E2E8F0]">
                          <div className="flex items-center gap-2">
                            {h.type === 'earned' ? (
                              <Plus className="w-4 h-4 text-green-600" />
                            ) : h.type === 'redeemed' ? (
                              <Minus className="w-4 h-4 text-red-500" />
                            ) : (
                              <Star className="w-4 h-4 text-amber-500" />
                            )}
                            <div>
                              <p className="text-sm font-semibold text-[#0F172A]">{h.description}</p>
                              <p className="text-xs text-[#334155]">{new Date(h.date).toLocaleDateString('it-IT')}</p>
                            </div>
                          </div>
                          <span className={`font-black text-sm ${h.points > 0 ? 'text-green-600' : 'text-red-500'}`}>
                            {h.points > 0 ? `+${h.points}` : h.points}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-[#334155] text-center py-4">Nessuna attività</p>
                  )}
                </div>
              </div>
            ) : null}
          </DialogContent>
        </Dialog>

        {/* Redeem Confirmation */}
        <AlertDialog open={redeemOpen} onOpenChange={setRedeemOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Riscattare Premio?</AlertDialogTitle>
              <AlertDialogDescription>
                Vuoi riscattare "{LOYALTY_REWARDS_UI[redeemType]?.name}" per {selectedClient?.client_name}?
                Verranno scalati {config?.rewards?.[redeemType]?.points_required || LOYALTY_REWARDS_UI[redeemType]?.pointsReq} punti.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Annulla</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleRedeem}
                disabled={redeeming}
                className="bg-amber-500 hover:bg-amber-600"
              >
                {redeeming ? 'Riscatto...' : 'Conferma Riscatto'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </Layout>
  );
}

const LOYALTY_REWARDS_UI = {
  sconto_colorazione: {
    name: 'Sconto 10% Colorazione',
    pointsReq: 5,
    icon: <Award className="w-5 h-5 text-purple-600" />,
    bgColor: 'bg-purple-100',
  },
  taglio_gratuito: {
    name: 'Taglio Gratuito',
    pointsReq: 10,
    icon: <Trophy className="w-5 h-5 text-emerald-600" />,
    bgColor: 'bg-emerald-100',
  },
};
