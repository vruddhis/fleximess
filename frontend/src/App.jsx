
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import StudentLogin from './pages/StudentLogin';
import StudentSignup from './pages/StudentSignup';


function App() {
    return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/student-login"/>} />
        
        <Route path="/student-login" element={<StudentLogin/>} />
        <Route path="/student-signup" element={<StudentSignup/>} />
       
      </Routes>
    </BrowserRouter>
  );

}

export default App;
