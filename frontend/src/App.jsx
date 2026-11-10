
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import StudentLogin from './pages/StudentLogin';
import StudentSignup from './pages/StudentSignup';
import GuestDashboard from './pages/GuestDashboard'
import StudentDashboard from './pages/StudentDashboard'
import StudentPreferences from './pages/StudentPreferences'
import StudentHistory from './pages/StudentHistory'
import StudentLogMeal from './pages/StudentLogMeal'
import { AuthProvider } from './auth/AuthProvider';
import RequireAuth from './auth/RequireAuth';


function App() {
    return (
    <BrowserRouter>
      <AuthProvider>
      <Routes>
        <Route path="/" element={<Navigate to="/student-login"/>} />
        
        <Route path="/student-login" element={<StudentLogin/>} />
        <Route path="/student-signup" element={<StudentSignup/>} />
       
        <Route path="/dashboard" element={<GuestDashboard/>} />
        <Route element={<RequireAuth />}>
          <Route path="/student-dashboard" element={<StudentDashboard/>} />
          <Route path="/preferences" element={<StudentPreferences/>} />
          <Route path="/student-history" element={<StudentHistory/>} />
          <Route path="/student-log" element={<StudentLogMeal/>} />
        </Route>
      </Routes>
      </AuthProvider>
    </BrowserRouter>
  );

}

export default App;
