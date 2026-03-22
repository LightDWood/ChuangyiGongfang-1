import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores';
import LoginPage from './pages/LoginPage';
import ChatPage from './pages/ChatPage';

function App() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const checkAuth = useAuthStore((state) => state.checkAuth);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={isAuthenticated ? <Navigate to="/chat" /> : <LoginPage />}
        />
        <Route
          path="/chat"
          element={isAuthenticated ? <ChatPage /> : <Navigate to="/login" />}
        />
        <Route path="*" element={<Navigate to={isAuthenticated ? '/chat' : '/login'} />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
