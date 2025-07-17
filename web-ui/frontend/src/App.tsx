import React, { useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Container, Box, Fab } from '@mui/material';
import { BugReport } from '@mui/icons-material';
import Dashboard from './components/Dashboard';
import SocketTest from './components/SocketTest';
import { socketService } from './services/socket';

// Create a theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  const [showSocketTest, setShowSocketTest] = React.useState(false);

  useEffect(() => {
    // Initialize WebSocket connection when app starts
    const initializeSocket = async () => {
      try {
        await socketService.connect();
        console.log('✅ WebSocket connected successfully');
      } catch (error) {
        console.error('❌ Failed to connect to WebSocket:', error);
        // App will still work with polling fallback
      }
    };

    initializeSocket();

    // Cleanup on unmount
    return () => {
      socketService.disconnect();
    };
  }, []);

  // Check URL for debug mode
  React.useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('debug') === 'socket') {
      setShowSocketTest(true);
    }
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="xl">
        <Box sx={{ py: 4 }}>
          {showSocketTest ? <SocketTest /> : <Dashboard />}
        </Box>
      </Container>
      
      {/* Debug FAB - only show in development */}
      {process.env.NODE_ENV === 'development' && (
        <Fab
          color="secondary"
          aria-label="debug"
          sx={{ position: 'fixed', bottom: 16, right: 16 }}
          onClick={() => setShowSocketTest(!showSocketTest)}
          title={showSocketTest ? 'Show Dashboard' : 'Show Socket Test'}
        >
          <BugReport />
        </Fab>
      )}
    </ThemeProvider>
  );
}

export default App;