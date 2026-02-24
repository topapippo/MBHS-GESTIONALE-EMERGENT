import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { BarChart3, Euro, TrendingUp, Calendar as CalendarIcon, Users } from 'lucide-react';
import { format, subDays, startOfMonth, endOfMonth, subMonths } from 'date-fns';
import { it } from 'date-fns/locale';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const COLORS = ['#C58970', '#789F8A', '#E9C46A', '#78716C', '#E6CCB2'];

export default function StatsPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState({
    start: startOfMonth(new Date()),
    end: new Date()
  });

  useEffect(() => {
    fetchStats();
  }, [dateRange]);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/stats/revenue`, {
        params: {
          start_date: format(dateRange.start, 'yyyy-MM-dd'),
          end_date: format(dateRange.end, 'yyyy-MM-dd')
        }
      });
      setStats(res.data);
    } catch (err) {
      console.error('Error fetching stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const setPresetRange = (preset) => {
    const today = new Date();
    switch (preset) {
      case 'week':
        setDateRange({ start: subDays(today, 7), end: today });
        break;
      case 'month':
        setDateRange({ start: startOfMonth(today), end: today });
        break;
      case 'lastMonth':
        const lastMonth = subMonths(today, 1);
        setDateRange({ start: startOfMonth(lastMonth), end: endOfMonth(lastMonth) });
        break;
      case '3months':
        setDateRange({ start: subMonths(today, 3), end: today });
        break;
      default:
        break;
    }
  };

  const formatCurrency = (value) => `€${value.toFixed(0)}`;

  return (
    <Layout>
      <div className="space-y-6" data-testid="stats-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="font-playfair text-3xl font-medium text-[#44403C]">Statistiche</h1>
            <p className="text-[#78716C] mt-1 font-manrope">
              {format(dateRange.start, "d MMM", { locale: it })} - {format(dateRange.end, "d MMM yyyy", { locale: it })}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPresetRange('week')}
              className="border-[#E6CCB2] text-[#44403C]"
            >
              7 giorni
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPresetRange('month')}
              className="border-[#E6CCB2] text-[#44403C]"
            >
              Questo mese
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPresetRange('lastMonth')}
              className="border-[#E6CCB2] text-[#44403C]"
            >
              Mese scorso
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPresetRange('3months')}
              className="border-[#E6CCB2] text-[#44403C]"
            >
              3 mesi
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
        ) : (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className="bg-white border-[#E6CCB2]/30 shadow-[0_2px_15px_-3px_rgba(0,0,0,0.07)]">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm text-[#78716C] font-manrope">Incasso Totale</p>
                      <p className="text-3xl font-playfair font-medium text-[#44403C] mt-2">
                        €{(stats?.total_revenue || 0).toFixed(2)}
                      </p>
                    </div>
                    <div className="w-12 h-12 rounded-xl bg-[#C58970]/10 flex items-center justify-center">
                      <Euro className="w-6 h-6 text-[#C58970]" strokeWidth={1.5} />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white border-[#E6CCB2]/30 shadow-[0_2px_15px_-3px_rgba(0,0,0,0.07)]">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm text-[#78716C] font-manrope">Appuntamenti</p>
                      <p className="text-3xl font-playfair font-medium text-[#44403C] mt-2">
                        {stats?.total_appointments || 0}
                      </p>
                    </div>
                    <div className="w-12 h-12 rounded-xl bg-[#789F8A]/10 flex items-center justify-center">
                      <CalendarIcon className="w-6 h-6 text-[#789F8A]" strokeWidth={1.5} />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white border-[#E6CCB2]/30 shadow-[0_2px_15px_-3px_rgba(0,0,0,0.07)]">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm text-[#78716C] font-manrope">Media per Appuntamento</p>
                      <p className="text-3xl font-playfair font-medium text-[#44403C] mt-2">
                        €{stats?.total_appointments > 0 
                          ? (stats.total_revenue / stats.total_appointments).toFixed(2) 
                          : '0.00'}
                      </p>
                    </div>
                    <div className="w-12 h-12 rounded-xl bg-[#E9C46A]/10 flex items-center justify-center">
                      <TrendingUp className="w-6 h-6 text-[#E9C46A]" strokeWidth={1.5} />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Revenue Chart */}
              <Card className="bg-white border-[#E6CCB2]/30 shadow-[0_2px_15px_-3px_rgba(0,0,0,0.07)]">
                <CardHeader>
                  <CardTitle className="font-playfair text-xl text-[#44403C]">Incassi Giornalieri</CardTitle>
                </CardHeader>
                <CardContent>
                  {stats?.daily_revenue?.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={stats.daily_revenue}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E6CCB2" />
                        <XAxis 
                          dataKey="date" 
                          tick={{ fontSize: 12, fill: '#78716C' }}
                          tickFormatter={(val) => format(new Date(val), 'd/M')}
                        />
                        <YAxis 
                          tick={{ fontSize: 12, fill: '#78716C' }}
                          tickFormatter={formatCurrency}
                        />
                        <Tooltip 
                          formatter={(value) => [`€${value.toFixed(2)}`, 'Incasso']}
                          labelFormatter={(val) => format(new Date(val), 'EEEE d MMMM', { locale: it })}
                          contentStyle={{ 
                            backgroundColor: '#fff', 
                            border: '1px solid #E6CCB2',
                            borderRadius: '8px'
                          }}
                        />
                        <Bar dataKey="revenue" fill="#C58970" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[300px] flex items-center justify-center text-[#78716C]">
                      Nessun dato disponibile
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Services Breakdown */}
              <Card className="bg-white border-[#E6CCB2]/30 shadow-[0_2px_15px_-3px_rgba(0,0,0,0.07)]">
                <CardHeader>
                  <CardTitle className="font-playfair text-xl text-[#44403C]">Servizi Più Richiesti</CardTitle>
                </CardHeader>
                <CardContent>
                  {stats?.service_breakdown?.length > 0 ? (
                    <div className="flex flex-col lg:flex-row items-center gap-6">
                      <ResponsiveContainer width="100%" height={200}>
                        <PieChart>
                          <Pie
                            data={stats.service_breakdown.slice(0, 5)}
                            cx="50%"
                            cy="50%"
                            innerRadius={50}
                            outerRadius={80}
                            paddingAngle={2}
                            dataKey="count"
                          >
                            {stats.service_breakdown.slice(0, 5).map((entry, index) => (
                              <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip 
                            formatter={(value, name, props) => [`${value} volte`, props.payload.name]}
                            contentStyle={{ 
                              backgroundColor: '#fff', 
                              border: '1px solid #E6CCB2',
                              borderRadius: '8px'
                            }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                      <div className="space-y-2 w-full lg:w-auto">
                        {stats.service_breakdown.slice(0, 5).map((service, idx) => (
                          <div key={service.name} className="flex items-center justify-between gap-4">
                            <div className="flex items-center gap-2">
                              <div 
                                className="w-3 h-3 rounded-full"
                                style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                              />
                              <span className="text-sm text-[#44403C]">{service.name}</span>
                            </div>
                            <span className="text-sm font-medium text-[#78716C]">
                              {service.count}x - €{service.revenue.toFixed(0)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="h-[200px] flex items-center justify-center text-[#78716C]">
                      Nessun dato disponibile
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </div>
    </Layout>
  );
}
