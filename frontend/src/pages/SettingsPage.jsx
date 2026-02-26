import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Checkbox } from '@/components/ui/checkbox';
import { Settings, Save, Loader2, Clock, Building2, User, Lock } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const DAYS = [
  { value: 'lunedì', label: 'Lunedì' },
  { value: 'martedì', label: 'Martedì' },
  { value: 'mercoledì', label: 'Mercoledì' },
  { value: 'giovedì', label: 'Giovedì' },
  { value: 'venerdì', label: 'Venerdì' },
  { value: 'sabato', label: 'Sabato' },
  { value: 'domenica', label: 'Domenica' },
];

export default function SettingsPage() {
  const { updateUser } = useAuth();
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [changingPw, setChangingPw] = useState(false);
  const [pwForm, setPwForm] = useState({ current_password: '', new_password: '', confirm_password: '' });

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const res = await axios.get(`${API}/settings`);
      setSettings(res.data);
    } catch (err) {
      console.error('Error fetching settings:', err);
      toast.error('Errore nel caricamento delle impostazioni');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await axios.put(`${API}/settings`, {
        salon_name: settings.salon_name,
        name: settings.name,
        opening_time: settings.opening_time,
        closing_time: settings.closing_time,
        working_days: settings.working_days
      });
      updateUser({ name: settings.name, salon_name: settings.salon_name });
      toast.success('Impostazioni salvate!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore nel salvataggio');
    } finally {
      setSaving(false);
    }
  };

  const toggleDay = (day) => {
    setSettings(prev => ({
      ...prev,
      working_days: prev.working_days.includes(day)
        ? prev.working_days.filter(d => d !== day)
        : [...prev.working_days, day]
    }));
  };

  if (loading) {
    return (
      <Layout>
        <div className="space-y-6">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-64" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6" data-testid="settings-page">
        {/* Header */}
        <div>
          <h1 className="font-playfair text-3xl font-medium text-[#0F172A]">Impostazioni</h1>
          <p className="text-[#334155] mt-1 font-manrope">Gestisci le impostazioni del tuo salone</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Profile Settings */}
          <Card className="bg-white border-[#E2E8F0]/30 shadow-[0_2px_15px_-3px_rgba(0,0,0,0.07)]">
            <CardHeader>
              <CardTitle className="font-playfair text-xl text-[#0F172A] flex items-center gap-2">
                <User className="w-5 h-5 text-[#0EA5E9]" />
                Profilo
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Il tuo nome</Label>
                  <Input
                    value={settings.name || ''}
                    onChange={(e) => setSettings({ ...settings, name: e.target.value })}
                    data-testid="settings-name-input"
                    className="bg-[#F8FAFC] border-transparent focus:border-[#0EA5E9]"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input
                    value={settings.email || ''}
                    disabled
                    className="bg-[#F8FAFC] border-transparent opacity-60"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Salon Settings */}
          <Card className="bg-white border-[#E2E8F0]/30 shadow-[0_2px_15px_-3px_rgba(0,0,0,0.07)]">
            <CardHeader>
              <CardTitle className="font-playfair text-xl text-[#0F172A] flex items-center gap-2">
                <Building2 className="w-5 h-5 text-[#0EA5E9]" />
                Salone
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Nome del Salone</Label>
                <Input
                  value={settings.salon_name || ''}
                  onChange={(e) => setSettings({ ...settings, salon_name: e.target.value })}
                  data-testid="settings-salon-name-input"
                  className="bg-[#F8FAFC] border-transparent focus:border-[#0EA5E9]"
                />
              </div>
            </CardContent>
          </Card>

          {/* Working Hours */}
          <Card className="bg-white border-[#E2E8F0]/30 shadow-[0_2px_15px_-3px_rgba(0,0,0,0.07)]">
            <CardHeader>
              <CardTitle className="font-playfair text-xl text-[#0F172A] flex items-center gap-2">
                <Clock className="w-5 h-5 text-[#0EA5E9]" />
                Orari di Apertura
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Apertura</Label>
                  <Input
                    type="time"
                    value={settings.opening_time || '09:00'}
                    onChange={(e) => setSettings({ ...settings, opening_time: e.target.value })}
                    data-testid="settings-opening-time-input"
                    className="bg-[#F8FAFC] border-transparent focus:border-[#0EA5E9]"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Chiusura</Label>
                  <Input
                    type="time"
                    value={settings.closing_time || '19:00'}
                    onChange={(e) => setSettings({ ...settings, closing_time: e.target.value })}
                    data-testid="settings-closing-time-input"
                    className="bg-[#F8FAFC] border-transparent focus:border-[#0EA5E9]"
                  />
                </div>
              </div>

              <div className="space-y-3">
                <Label>Giorni Lavorativi</Label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {DAYS.map((day) => (
                    <div
                      key={day.value}
                      className={`flex items-center space-x-2 p-3 rounded-lg border cursor-pointer transition-colors ${
                        settings.working_days?.includes(day.value)
                          ? 'bg-[#0EA5E9]/10 border-[#0EA5E9]'
                          : 'bg-[#F8FAFC] border-transparent hover:border-[#E2E8F0]'
                      }`}
                      onClick={() => toggleDay(day.value)}
                    >
                      <Checkbox
                        checked={settings.working_days?.includes(day.value)}
                        className="data-[state=checked]:bg-[#0EA5E9] data-[state=checked]:border-[#0EA5E9]"
                      />
                      <span className={`text-sm ${
                        settings.working_days?.includes(day.value) ? 'text-[#0EA5E9] font-medium' : 'text-[#0F172A]'
                      }`}>
                        {day.label}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Save Button */}
          <div className="flex justify-end">
            <Button
              type="submit"
              disabled={saving}
              data-testid="save-settings-btn"
              className="bg-[#0EA5E9] hover:bg-[#0284C7] text-white shadow-lg shadow-[#0EA5E9]/20 px-8"
            >
              {saving ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <Save className="w-5 h-5 mr-2" />
                  Salva Impostazioni
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </Layout>
  );
}
