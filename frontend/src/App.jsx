
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import StudentLogin from './pages/StudentLogin';
import StudentSignup from './pages/StudentSignup';
import GuestDashboard from './pages/GuestDashboard'
import StudentDashboard from './pages/StudentDashboard'


function App() {
    return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/student-login"/>} />
        
        <Route path="/student-login" element={<StudentLogin/>} />
        <Route path="/student-signup" element={<StudentSignup/>} />
       
        <Route path="/dashboard" element={<GuestDashboard/>} />
        <Route path="/student-dashboard" element={<StudentDashboard/>} />
      </Routes>
    </BrowserRouter>
  );

}

export default App;
