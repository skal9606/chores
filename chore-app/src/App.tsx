import { useState, useMemo } from 'react';
import { Header } from './components/Header';
import { Calendar } from './components/Calendar';
import { ChoreModal } from './components/ChoreModal';
import { TeamMemberList } from './components/TeamMemberList';
import { useChores } from './hooks/useChores';
import type { Chore } from './types';

function App() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedChore, setSelectedChore] = useState<Chore | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);

  const {
    teamMembers,
    addChore,
    updateChore,
    deleteChore,
    toggleChoreComplete,
    addTeamMember,
    removeTeamMember,
    getChoresForDateRange,
  } = useChores();

  const displayedChores = useMemo(() => {
    const startDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    startDate.setDate(startDate.getDate() - 7); // Include previous month days
    const endDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 7); // Include next month days
    return getChoresForDateRange(startDate, endDate);
  }, [currentDate, getChoresForDateRange]);

  const handlePrevMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  const handleToday = () => {
    setCurrentDate(new Date());
  };

  const handleDateClick = (date: Date) => {
    setSelectedDate(date);
    setSelectedChore(null);
    setModalOpen(true);
  };

  const handleChoreClick = (chore: Chore) => {
    setSelectedChore(chore);
    setSelectedDate(null);
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setSelectedChore(null);
    setSelectedDate(null);
  };

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      <Header
        currentDate={currentDate}
        onPrevMonth={handlePrevMonth}
        onNextMonth={handleNextMonth}
        onToday={handleToday}
      />
      <div className="flex-1 flex overflow-hidden p-4 gap-4">
        <Calendar
          currentDate={currentDate}
          chores={displayedChores}
          teamMembers={teamMembers}
          onDateClick={handleDateClick}
          onChoreClick={handleChoreClick}
          onToggleComplete={toggleChoreComplete}
        />
        <TeamMemberList
          teamMembers={teamMembers}
          onAddMember={addTeamMember}
          onRemoveMember={removeTeamMember}
        />
      </div>
      <ChoreModal
        isOpen={modalOpen}
        chore={selectedChore}
        selectedDate={selectedDate}
        teamMembers={teamMembers}
        onClose={handleCloseModal}
        onSave={addChore}
        onUpdate={updateChore}
        onDelete={deleteChore}
      />
    </div>
  );
}

export default App;
