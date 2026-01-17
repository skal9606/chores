import type { Chore, TeamMember } from '../types';

interface ChoreCardProps {
  chore: Chore;
  member: TeamMember | undefined;
  onToggleComplete: (id: string) => void;
  onClick: (chore: Chore) => void;
}

export function ChoreCard({ chore, member, onToggleComplete, onClick }: ChoreCardProps) {
  const handleCheckboxClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onToggleComplete(chore.id);
  };

  return (
    <div
      onClick={() => onClick(chore)}
      className="group flex items-center gap-1.5 px-2 py-1 rounded text-xs cursor-pointer hover:opacity-80 transition-opacity"
      style={{ backgroundColor: member?.color ? `${member.color}20` : '#e5e7eb' }}
    >
      <button
        onClick={handleCheckboxClick}
        className="flex-shrink-0 w-3.5 h-3.5 rounded border flex items-center justify-center"
        style={{
          borderColor: member?.color || '#9ca3af',
          backgroundColor: chore.completed ? (member?.color || '#9ca3af') : 'transparent',
        }}
      >
        {chore.completed && (
          <svg className="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        )}
      </button>
      <span
        className={`truncate ${chore.completed ? 'line-through opacity-60' : ''}`}
        style={{ color: member?.color || '#374151' }}
      >
        {chore.title}
      </span>
      {chore.recurrence !== 'none' && (
        <svg className="w-3 h-3 flex-shrink-0 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      )}
    </div>
  );
}
