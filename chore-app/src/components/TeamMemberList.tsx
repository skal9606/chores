import { useState } from 'react';
import type { TeamMember } from '../types';

interface TeamMemberListProps {
  teamMembers: TeamMember[];
  onAddMember: (name: string) => void;
  onRemoveMember: (id: string) => void;
}

export function TeamMemberList({ teamMembers, onAddMember, onRemoveMember }: TeamMemberListProps) {
  const [newMemberName, setNewMemberName] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newMemberName.trim()) {
      onAddMember(newMemberName.trim());
      setNewMemberName('');
      setIsAdding(false);
    }
  };

  return (
    <div className="w-64 bg-white border-l border-gray-200 flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Team Members</h2>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {teamMembers.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-4">
            No team members yet. Add someone to get started!
          </p>
        ) : (
          <ul className="space-y-2">
            {teamMembers.map((member) => (
              <li
                key={member.id}
                className="flex items-center justify-between p-2 rounded-md hover:bg-gray-50 group"
              >
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: member.color }}
                  />
                  <span className="text-sm text-gray-700">{member.name}</span>
                </div>
                <button
                  onClick={() => onRemoveMember(member.id)}
                  className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-opacity"
                  aria-label={`Remove ${member.name}`}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="p-4 border-t border-gray-200">
        {isAdding ? (
          <form onSubmit={handleSubmit} className="space-y-2">
            <input
              type="text"
              value={newMemberName}
              onChange={(e) => setNewMemberName(e.target.value)}
              placeholder="Enter name"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              autoFocus
            />
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => {
                  setIsAdding(false);
                  setNewMemberName('');
                }}
                className="flex-1 px-3 py-1.5 text-sm text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!newMemberName.trim()}
                className="flex-1 px-3 py-1.5 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                Add
              </button>
            </div>
          </form>
        ) : (
          <button
            onClick={() => setIsAdding(true)}
            className="w-full px-3 py-2 text-sm text-blue-600 border border-blue-600 rounded-md hover:bg-blue-50 flex items-center justify-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Team Member
          </button>
        )}
      </div>
    </div>
  );
}
