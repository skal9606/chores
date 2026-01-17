export interface TeamMember {
  id: string;
  name: string;
  color: string;
}

export interface Chore {
  id: string;
  title: string;
  date: string; // ISO date string (YYYY-MM-DD)
  assigneeId: string;
  completed: boolean;
  recurrence: 'none' | 'daily' | 'weekly' | 'monthly';
  parentId?: string; // for recurring instances
}

export type RecurrenceType = Chore['recurrence'];
