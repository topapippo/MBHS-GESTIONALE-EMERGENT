import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isSameDay, addMonths, subMonths, startOfWeek, endOfWeek } from 'date-fns';
import { it } from 'date-fns/locale';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function MonthlyView() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentMonth, setCurrentMonth] = useState(new Date());

  useEffect(() => {
    fetchAppointments();
  }, [currentMonth]);

  const fetchAppointments = async () => {
    setLoading(true);
    try {
      const startDate = format(startOfMonth(currentMonth), 'yyyy-MM-dd');
      const endDate = format(endOfMonth(currentMonth), 'yyyy-MM-dd');
      const res = await axios.get(`${API}/appointments?start_date=${startDate}&end_date=${endDate}`);
      setAppointments(res.data);
    } catch (err) {
      console.error('Error fetching appointments:', err);
    } finally {
      setLoading(false);
    }
  };

  const monthStart = startOfMonth(currentMonth);
  const monthEnd = endOfMonth(currentMonth);
  const calendarStart = startOfWeek(monthStart, { weekStartsOn: 1 });
  const calendarEnd = endOfWeek(monthEnd, { weekStartsOn: 1 });
  const calendarDays = eachDayOfInterval({ start: calendarStart, end: calendarEnd });

  const getAppointmentsForDay = (date) => {
    const dateStr = format(date, 'yyyy-MM-dd');
    return appointments.filter(apt => apt.date === dateStr);
  };

  const weekDays = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom'];

  return (
    <Layout>
      <div className="space-y-6" data-testid="monthly-view-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="font-playfair text-3xl font-medium text-[#44403C]">Vista Mensile</h1>
            <p className="text-[#78716C] mt-1 font-manrope capitalize">
              {format(currentMonth, "MMMM yyyy", { locale: it })}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
              className="border-[#E6CCB2]"
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              onClick={() => setCurrentMonth(new Date())}
              className="border-[#E6CCB2] text-[#44403C]"
            >
              Oggi
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
              className="border-[#E6CCB2]"
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Calendar */}
        <Card className="bg-white border-[#E6CCB2]/30 shadow-[0_2px_15px_-3px_rgba(0,0,0,0.07)] overflow-hidden">
          <CardContent className="p-0">
            {/* Week Headers */}
            <div className="grid grid-cols-7 bg-[#FAFAF9] border-b border-[#E6CCB2]/30">
              {weekDays.map((day) => (
                <div key={day} className="p-3 text-center text-sm font-medium text-[#78716C]">
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar Grid */}
            {loading ? (
              <div className="p-4">
                <Skeleton className="h-96 w-full" />
              </div>
            ) : (
              <div className="grid grid-cols-7">
                {calendarDays.map((day, idx) => {
                  const dayAppointments = getAppointmentsForDay(day);
                  const isToday = isSameDay(day, new Date());
                  const isCurrentMonth = isSameMonth(day, currentMonth);
                  
                  return (
                    <div
                      key={idx}
                      data-testid={`calendar-day-${format(day, 'yyyy-MM-dd')}`}
                      className={`min-h-[100px] md:min-h-[120px] p-2 border-b border-r border-[#E6CCB2]/20 ${
                        !isCurrentMonth ? 'bg-[#FAFAF9]/50' : ''
                      }`}
                    >
                      <div className={`text-right mb-1 ${
                        isToday 
                          ? 'text-white' 
                          : isCurrentMonth 
                            ? 'text-[#44403C]' 
                            : 'text-[#78716C]/50'
                      }`}>
                        <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-sm font-medium ${
                          isToday ? 'bg-[#C58970]' : ''
                        }`}>
                          {format(day, 'd')}
                        </span>
                      </div>
                      
                      {/* Appointments */}
                      <div className="space-y-1">
                        {dayAppointments.slice(0, 2).map((apt) => (
                          <div
                            key={apt.id}
                            className={`text-[10px] md:text-xs px-1.5 py-0.5 rounded truncate ${
                              apt.status === 'completed'
                                ? 'bg-[#789F8A]/20 text-[#789F8A]'
                                : apt.status === 'cancelled'
                                  ? 'bg-[#E76F51]/20 text-[#E76F51]'
                                  : 'bg-[#C58970]/20 text-[#C58970]'
                            }`}
                          >
                            <span className="font-medium">{apt.time}</span> {apt.client_name}
                          </div>
                        ))}
                        {dayAppointments.length > 2 && (
                          <div className="text-[10px] text-[#78716C] px-1.5">
                            +{dayAppointments.length - 2} altri
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Summary */}
        <Card className="bg-white border-[#E6CCB2]/30">
          <CardContent className="p-4">
            <div className="flex flex-wrap items-center justify-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#C58970]" />
                <span className="text-[#78716C]">Programmati ({appointments.filter(a => a.status === 'scheduled').length})</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#789F8A]" />
                <span className="text-[#78716C]">Completati ({appointments.filter(a => a.status === 'completed').length})</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#E76F51]" />
                <span className="text-[#78716C]">Annullati ({appointments.filter(a => a.status === 'cancelled').length})</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
