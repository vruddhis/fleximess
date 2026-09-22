
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import StudentLogin from './pages/StudentLogin';
import AdminLogin from './pages/AdminLogin';

function App() {
    return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/student-login"/>} />
        
        <Route path="/student-login" element={<StudentLogin/>} />
        <Route path="/admin-login" element={<AdminLogin />} />
      </Routes>
    </BrowserRouter>
  );

}

export default App;
