import { Alert, Box, Button, CircularProgress } from '@mui/material';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from './authContext';

function RequireAuth() {
  const { status, authError, refreshUser } = useAuth();
  const location = useLocation();

  if (status === 'loading') {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (status === 'error') {
    return (
      <Box sx={{ maxWidth: 480, mx: 'auto', p: 3 }}>
        <Alert severity="error">{authError || 'Could not verify your session.'}</Alert>
        <Button sx={{ mt: 2 }} onClick={() => void refreshUser()}>
          Try again
        </Button>
      </Box>
    );
  }

  if (status !== 'authenticated') {
    return <Navigate to="/student-login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}

export default RequireAuth;
