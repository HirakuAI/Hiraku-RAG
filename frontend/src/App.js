import "./App.css";
import React, { useState, useEffect } from "react";
import ChatInterface from "./components/ChatInterface";
import { LoginForm, RegisterForm } from "./components/AuthComponents";

function App() {
  const [authToken, setAuthToken] = useState(localStorage.getItem("authToken"));
  const [isRegistering, setIsRegistering] = useState(false);

  const handleLogin = (token) => {
    localStorage.setItem("authToken", token);
    setAuthToken(token);
  };

  const handleLogout = () => {
    localStorage.removeItem("authToken");
    setAuthToken(null);
  };

  return (
    <div className="App">
      {!authToken ? (
        isRegistering ? (
          <RegisterForm onSwitchToLogin={() => setIsRegistering(false)} />
        ) : (
          <LoginForm
            onLogin={handleLogin}
            onSwitchToRegister={() => setIsRegistering(true)}
          />
        )
      ) : (
        <ChatInterface authToken={authToken} onLogout={handleLogout} />
      )}
    </div>
  );
}

export default App;
