import { useState } from 'react';
import { Link } from 'react-router-dom';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import './login.css';

import hostel from '../assets/hostel.jpeg';

function StudentSignup() {
  const [form, setForm] = useState({ name: '', ldap: '', password: '' }); //setForm is a trigger function. we can't do form.name directly to change


function handleNameChange(event) {
  const value = event.target.value;
  setForm({ ...form, name: value }); //...form is the previous state snapshot. 
}

function handleLdapChange(event) {
  const value = event.target.value;
  setForm({ ...form, ldap: value });
}

function handlePasswordChange(event) {
  const value = event.target.value;
  setForm({ ...form, password: value });
}


  const handleSubmit = (event) => {
    event.preventDefault();
    console.log(form);
  };

  return (
    <Box className="login-container">
      <Box className="login-card">
        <Box className="image-box">
          <img
            src={hostel}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
        </Box>

        <Box className="form-box">
          <Typography variant="h5">Create your account</Typography>
          <Typography variant="body2">Sign up to access the FlexiMess Portal.</Typography>
          <form onSubmit={handleSubmit}>
            <Stack spacing={2}>
              <TextField
                label="Full name"
                name="name"
                value={form.name}
                onChange={handleNameChange}
                fullWidth
                required
              />
              <TextField
                label="LDAP ID"
                name="ldap"
                value={form.ldap}
                onChange={handleLdapChange} //so this is the event and the value here goes as name
                fullWidth
                required
              />
              <TextField
                label="Password"
                type="password"
                name="password"
                value={form.password}
                onChange={handlePasswordChange}
                fullWidth
                required
              />
              <Button type="submit" variant="contained">Sign up</Button>
            </Stack>
          </form>
          <Divider sx={{ my: 3 }}>OR</Divider>
          <Box style={{ textAlign: 'center' }}>
            <Link to="/student-login">Back to login</Link>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}

export default StudentSignup;
