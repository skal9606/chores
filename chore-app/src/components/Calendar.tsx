import { useMemo } from 'react';
import type { Chore, TeamMember } from '../types';
import { getMonthDays, formatDate, isSameMonth, isToday } from '../utils/dateUtils';
import { ChoreCard } from './ChoreCard';

interface CalendarProps {
  currentDate: Date;
  chores: Chore[];
  teamMembers: TeamMember[];
  onDateClick: (date: Date) => void;
  onChoreClick: (chore: Chore) => void;
  onToggleComplete: (id: string) => void;
}

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export function Calendar({
  currentDate,
  chores,
  teamMembers,
  onDateClick,
  onChoreClick,
  onToggleComplete,
}: CalendarProps) {
  const days = useMemo(
    () => getMonthDays(currentDate.getFullYear(), currentDate.getMonth()),
    [currentDate]
  );

  const choresByDate = useMemo(() => {
    const map: Record<string, Chore[]> = {};
    chores.forEach((chore) => {
      const date = chore.date;
      if (!map[date]) {
        map[date] = [];
      }
      map[date].push(chore);
    });
    return map;
  }, [chores]);

  const getMemberById = (id: string) => teamMembers.find((m) => m.id === id);

  return (
    <div className="flex-1 flex flex-col bg-white rounded-lg shadow overflow-hidden">
      {/* Weekday headers */}
      <div className="grid grid-cols-7 border-b border-gray-200">
        {WEEKDAYS.map((day) => (
          <div
            key={day}
            className="px-2 py-3 text-center text-sm font-semibold text-gray-700 bg-gray-50"
          >
            {day}
          </div>
        ))}
      </div>

      {/* Calendar grid */}
      <div className="flex-1 grid grid-cols-7 grid-rows-6">
        {days.map((day, index) => {
          const dateStr = formatDate(day);
          const dayChores = choresByDate[dateStr] || [];
          const isCurrentMonth = isSameMonth(day, currentDate);
          const isTodayDate = isToday(day);

          return (
            <div
              key={index}
              onClick={() => onDateClick(day)}
              className={`min-h-[100px] border-b border-r border-gray-200 p-1 cursor-pointer hover:bg-gray-50 transition-colors ${
                !isCurrentMonth ? 'bg-gray-50' : ''
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span
                  className={`text-sm font-medium w-7 h-7 flex items-center justify-center rounded-full ${
                    isTodayDate
                      ? 'bg-blue-600 text-white'
                      : isCurrentMonth
                      ? 'text-gray-900'
                      : 'text-gray-400'
                  }`}
                >
                  {day.getDate()}
                </span>
                {dayChores.length > 0 && (
                  <span className="text-xs text-gray-500">{dayChores.length}</span>
                )}
              </div>
              <div className="space-y-1 overflow-y-auto max-h-[80px]">
                {dayChores.slice(0, 3).map((chore) => (
                  <ChoreCard
                    key={chore.id}
                    chore={chore}
                    member={getMemberById(chore.assigneeId)}
                    onToggleComplete={onToggleComplete}
                    onClick={onChoreClick}
                  />
                ))}
                {dayChores.length > 3 && (
                  <div className="text-xs text-gray-500 px-2">
                    +{dayChores.length - 3} more
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
