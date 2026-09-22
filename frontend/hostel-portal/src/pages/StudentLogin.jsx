import { useState } from 'react'; //this is a hook
import './login.css';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import Stack from '@mui/material/Stack';
import Card from '@mui/material/Card';


import hostel from '../assets/hostel.jpeg';

function StudentLogin(){
    const [username, setUsername] = useState(''); //passing initial blank state
    const [password, setPassword] = useState('');

    const handleChange = (e) => {
    const { name, value } = e.target; //key value pair
        
        if (name === 'username') {
            setUsername(value); 
        } else if (name === 'password') {
            setPassword(value);
        }
  };

    const handleSubmit = (e) => { 
        e.preventDefault(); //by default if html form submitted it reloads entire page
//the username state variable in the html is the value
//onChange is everytime a character is typed, so we need to write that function also

        console.log("sending login data ", { username, password })
        //will do hashing later
        //REST API here

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


        <Typography variant="h5">Hostel Portal</Typography>
        <Typography variant="body2">Welcome back! Please login to your account.</Typography>
          <form onSubmit={handleSubmit}>

            <Stack spacing={2}>
                <Box>
                <Typography variant="body2" > LDAP ID
                                </Typography>
            <TextField name = "username" value={username} onChange={handleChange} fullWidth/> 
            </Box>
            <Box>
                <Typography variant="body2" > Password
                                </Typography>
            <TextField type="password" name="password" value={password} onChange={handleChange} fullWidth/> 
</Box>
            <Button type="submit" variant="contained">Login</Button>
            </Stack>
            </form> 
            <Divider sx={{ my: 3 }}>OR</Divider>
<Box style={{ textAlign: 'center' }}>
      <a href="/admin-login">Login as admin instead</a> </Box>
            </Box>

            
            
          
</Box>
</Box>
    )

}

export default StudentLogin;