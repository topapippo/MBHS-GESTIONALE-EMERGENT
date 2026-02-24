import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ChevronLeft, ChevronRight, Clock } from 'lucide-react';
import { format, startOfWeek, addDays, addWeeks, subWeeks, isSameDay } from 'date-fns';
import { it } from 'date-fns/locale';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function WeeklyView() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [weekStart, setWeekStart] = useState(startOfWeek(new Date(), { weekStartsOn: 1 }));

  useEffect(() => {
    fetchAppointments();
  }, [weekStart]);

  const fetchAppointments = async () => {
    setLoading(true);
    try {
      const startDate = format(weekStart, 'yyyy-MM-dd');
      const endDate = format(addDays(weekStart, 6), 'yyyy-MM-dd');
      const res = await axios.get(`${API}/appointments?start_date=${startDate}&end_date=${endDate}`);
      setAppointments(res.data);
    } catch (err) {
      console.error('Error fetching appointments:', err);
    } finally {
      setLoading(false);
    }
  };

  const weekDays = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));

  const getAppointmentsForDay = (date) => {
    const dateStr = format(date, 'yyyy-MM-dd');
    return appointments.filter(apt => apt.date === dateStr);
  };

  const getStatusBg = (status) => {
    switch (status) {
      case 'completed': return 'bg-[#789F8A]';
      case 'cancelled': return 'bg-[#E76F51]/50';
      default: return 'bg-[#C58970]';
    }
  };

  return (
    <Layout>
      <div className="space-y-6" data-testid="weekly-view-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="font-playfair text-3xl font-medium text-[#44403C]">Vista Settimanale</h1>
            <p className="text-[#78716C] mt-1 font-manrope">
              {format(weekStart, "d MMMM", { locale: it })} - {format(addDays(weekStart, 6), "d MMMM yyyy", { locale: it })}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              onClick={() => setWeekStart(subWeeks(weekStart, 1))}
              className="border-[#E6CCB2]"
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              onClick={() => setWeekStart(startOfWeek(new Date(), { weekStartsOn: 1 }))}
              className="border-[#E6CCB2] text-[#44403C]"
            >
              Oggi
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={() => setWeekStart(addWeeks(weekStart, 1))}
              className="border-[#E6CCB2]"
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Week Grid */}
        {loading ? (
          <div className="grid grid-cols-7 gap-4">
            {[1, 2, 3, 4, 5, 6, 7].map((i) => (
              <Skeleton key={i} className="h-64" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-7 gap-4">
            {weekDays.map((day) => {
              const dayAppointments = getAppointmentsForDay(day);
              const isToday = isSameDay(day, new Date());
              
              return (
                <Card
                  key={day.toString()}
                  data-testid={`day-${format(day, 'yyyy-MM-dd')}`}
                  className={`bg-white border-[#E6CCB2]/30 min-h-[300px] ${
                    isToday ? 'ring-2 ring-[#C58970] border-[#C58970]' : ''
                  }`}
                >
                  <CardContent className="p-3">
                    {/* Day Header */}
                    <div className={`text-center pb-3 mb-3 border-b border-[#E6CCB2]/30 ${
                      isToday ? 'text-[#C58970]' : 'text-[#44403C]'
                    }`}>
                      <p className="text-xs uppercase tracking-wide font-manrope">
                        {format(day, 'EEE', { locale: it })}
                      </p>
                      <p className={`text-2xl font-playfair font-medium ${
                        isToday ? 'bg-[#C58970] text-white w-10 h-10 rounded-full mx-auto flex items-center justify-center' : ''
                      }`}>
                        {format(day, 'd')}
                      </p>
                    </div>

                    {/* Appointments */}
                    <div className="space-y-2">
                      {dayAppointments.length > 0 ? (
                        dayAppointments.map((apt) => (
                          <div
                            key={apt.id}
                            className={`p-2 rounded-lg text-white text-xs ${getStatusBg(apt.status)}`}
                          >
                            <p className="font-semibold">{apt.time}</p>
                            <p className="truncate">{apt.client_name}</p>
                            <p className="text-white/80 truncate text-[10px]">
                              {apt.services.map(s => s.name).join(', ')}
                            </p>
                          </div>
                        ))
                      ) : (
                        <p className="text-xs text-[#78716C] text-center py-4">-</p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        {/* Summary */}
        <Card className="bg-white border-[#E6CCB2]/30">
          <CardContent className="p-4">
            <div className="flex flex-wrap items-center justify-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#C58970]" />
                <span className="text-[#78716C]">Programmati</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#789F8A]" />
                <span className="text-[#78716C]">Completati</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#E76F51]/50" />
                <span className="text-[#78716C]">Annullati</span>
              </div>
              <div className="text-[#44403C] font-medium">
                Totale: {appointments.length} appuntamenti
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
