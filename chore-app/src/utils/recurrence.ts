import type { Chore, RecurrenceType } from '../types';
import { formatDate, parseDate } from './dateUtils';

export function generateRecurringChores(
  chore: Chore,
  startDate: Date,
  endDate: Date
): Chore[] {
  if (chore.recurrence === 'none') {
    return [];
  }

  const instances: Chore[] = [];
  const choreDate = parseDate(chore.date);
  let currentDate = new Date(choreDate);

  // Move to the first occurrence after or on startDate
  while (currentDate < startDate) {
    currentDate = getNextOccurrence(currentDate, chore.recurrence);
  }

  // Generate instances up to endDate
  while (currentDate <= endDate) {
    // Don't create duplicate for the original date
    if (formatDate(currentDate) !== chore.date) {
      instances.push({
        ...chore,
        id: `${chore.id}-${formatDate(currentDate)}`,
        date: formatDate(currentDate),
        parentId: chore.id,
        completed: false,
      });
    }
    currentDate = getNextOccurrence(currentDate, chore.recurrence);
  }

  return instances;
}

function getNextOccurrence(date: Date, recurrence: RecurrenceType): Date {
  const next = new Date(date);

  switch (recurrence) {
    case 'daily':
      next.setDate(next.getDate() + 1);
      break;
    case 'weekly':
      next.setDate(next.getDate() + 7);
      break;
    case 'monthly':
      next.setMonth(next.getMonth() + 1);
      break;
    default:
      break;
  }

  return next;
}

export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

export const MEMBER_COLORS = [
  '#3B82F6', // blue
  '#10B981', // emerald
  '#F59E0B', // amber
  '#EF4444', // red
  '#8B5CF6', // violet
  '#EC4899', // pink
  '#06B6D4', // cyan
  '#84CC16', // lime
];

export function getNextColor(existingColors: string[]): string {
  const availableColor = MEMBER_COLORS.find(
    (color) => !existingColors.includes(color)
  );
  return availableColor || MEMBER_COLORS[existingColors.length % MEMBER_COLORS.length];
}
