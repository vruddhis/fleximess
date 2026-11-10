import { useState } from 'react';

import { Link } from 'react-router-dom';
import { useLocation, useNavigate } from 'react-router-dom';

import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import Stack from '@mui/material/Stack';


import hostel from '../assets/hostel.jpeg';
import { useAuth } from '../auth/authContext';

function StudentLogin(){
    const navigate = useNavigate();
    const location = useLocation();
    const { login } = useAuth();
    const [username, setUsername] = useState(''); //passing initial blank state
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleChange = (e) => {
    const { name, value } = e.target; //key value pair
        
        if (name === 'username') {
            setUsername(value); 
        } else if (name === 'password') {
            setPassword(value);
        }
  };

    const handleSubmit = async (e) => {
        e.preventDefault(); //by default if html form submitted it reloads entire page
        setError('');
        setIsSubmitting(true);
        try {
            await login(username, password);
            navigate(location.state?.from?.pathname || '/student-dashboard', { replace: true });
        } catch (loginError) {
            setError(loginError.message);
        } finally {
            setIsSubmitting(false);
        }
    };
       

    return(
<Box className='login-container'>

    <Box className="login-card">
        <Box className="image-box">
          <img 
            src={hostel} 
            alt="Hostel picture" 
            style={{ width: '100%', height: '100%', objectFit: 'cover'}}
          />
        </Box>

        <Box className="form-box">


        <Typography variant="h5">FlexiMess Portal</Typography>
        <Typography variant="body2">Welcome back! Please login to your account.</Typography>
       
          <form onSubmit={handleSubmit}>

            <Stack spacing={2}>
                {error && <Alert severity="error">{error}</Alert>}
                <Box>
                <Typography variant="body2" > LDAP ID
                                </Typography>
            <TextField name="username" value={username} onChange={handleChange} fullWidth required autoComplete="username"/>
            </Box>
            <Box>
                <Typography variant="body2" > Password
                                </Typography>
            <TextField type="password" name="password" value={password} onChange={handleChange} fullWidth required autoComplete="current-password"/>
</Box>
            <Button type="submit" variant="contained" disabled={isSubmitting}>
                {isSubmitting ? 'Signing in…' : 'Login'}
            </Button>
            </Stack>
            </form> 
                        <Divider sx={{ my: 3 }}>OR</Divider>
                        <Stack direction="row" justifyContent="center" spacing={3}>
                            <Link to="/dashboard">View as guest</Link>
                            <Link to="/student-signup">Sign up</Link>
                        </Stack>
            </Box>

           
            
          
</Box>
</Box>
    )

}

export default StudentLogin;