
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import StudentLogin from './pages/StudentLogin';
import StudentSignup from './pages/StudentSignup';
import GuestDashboard from './pages/GuestDashboard'
import StudentDashboard from './pages/StudentDashboard'
import StudentPreferences from './pages/StudentPreferences'
import StudentHistory from './pages/StudentHistory'
import StudentLogMeal from './pages/StudentLogMeal'


function App() {
    return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/student-login"/>} />
        
        <Route path="/student-login" element={<StudentLogin/>} />
        <Route path="/student-signup" element={<StudentSignup/>} />
       
        <Route path="/dashboard" element={<GuestDashboard/>} />
        <Route path="/student-dashboard" element={<StudentDashboard/>} />

        <Route path="/preferences" element={<StudentPreferences/>} />

        <Route path="/student-history" element={<StudentHistory/>} />
        <Route path="/student-log" element={<StudentLogMeal/>} />
      </Routes>
    </BrowserRouter>
  );

}

export default App;
