import type { Chore, TeamMember } from '../types';
import { useLocalStorage } from './useLocalStorage';
import { generateRecurringChores, generateId, getNextColor } from '../utils/recurrence';

export function useChores() {
  const [chores, setChores] = useLocalStorage<Chore[]>('chores', []);
  const [teamMembers, setTeamMembers] = useLocalStorage<TeamMember[]>('teamMembers', []);

  const addChore = (chore: Omit<Chore, 'id'>) => {
    const newChore: Chore = {
      ...chore,
      id: generateId(),
    };
    setChores((prev) => [...prev, newChore]);
  };

  const updateChore = (id: string, updates: Partial<Chore>) => {
    setChores((prev) =>
      prev.map((chore) =>
        chore.id === id ? { ...chore, ...updates } : chore
      )
    );
  };

  const deleteChore = (id: string) => {
    setChores((prev) => prev.filter((chore) => chore.id !== id && chore.parentId !== id));
  };

  const toggleChoreComplete = (id: string) => {
    setChores((prev) =>
      prev.map((chore) =>
        chore.id === id ? { ...chore, completed: !chore.completed } : chore
      )
    );
  };

  const addTeamMember = (name: string) => {
    const existingColors = teamMembers.map((m) => m.color);
    const newMember: TeamMember = {
      id: generateId(),
      name,
      color: getNextColor(existingColors),
    };
    setTeamMembers((prev) => [...prev, newMember]);
  };

  const removeTeamMember = (id: string) => {
    setTeamMembers((prev) => prev.filter((member) => member.id !== id));
    // Remove chores assigned to this member
    setChores((prev) => prev.filter((chore) => chore.assigneeId !== id));
  };

  const getChoresForDateRange = (startDate: Date, endDate: Date): Chore[] => {
    // Get base chores (non-recurring or first instance of recurring)
    const baseChores = chores.filter((chore) => !chore.parentId);

    // Generate recurring instances
    const recurringInstances = baseChores.flatMap((chore) =>
      generateRecurringChores(chore, startDate, endDate)
    );

    // Combine base chores and recurring instances
    const allChores = [...chores, ...recurringInstances];

    // Filter to date range
    return allChores.filter((chore) => {
      const choreDate = new Date(chore.date);
      return choreDate >= startDate && choreDate <= endDate;
    });
  };

  const getTeamMemberById = (id: string): TeamMember | undefined => {
    return teamMembers.find((member) => member.id === id);
  };

  return {
    chores,
    teamMembers,
    addChore,
    updateChore,
    deleteChore,
    toggleChoreComplete,
    addTeamMember,
    removeTeamMember,
    getChoresForDateRange,
    getTeamMemberById,
  };
}
