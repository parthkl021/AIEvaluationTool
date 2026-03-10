import { Routes, Route, Navigate } from "react-router-dom";
import React, { useState, useEffect } from "react";

import "./App.css";
import LoginPage from "./components/Login/LoginPage";
import TestRunsPage from "./components/test-runs/TestRunsPage";
import TestRunDetails from "./components/test-run-details/TestRunDetailsPage";
import NewTestRunPage from "./components/new-test-run/NewTestRunPage";
import DevConfigPage from "./components/DevConfig/DevConfig";
import ContinueRunPage from "./components/continue-test-run/ContinueTestRunPage";
import Sidebar from "./components/common/sidebar/sidebar";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    setIsAuthenticated(!!token);
    setLoading(false);
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  const AuthenticatedApp = () => (
    <div className="app-container">
      <div className="sidebar">
        <Sidebar onLogout={() => setIsAuthenticated(false)} />
      </div>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<TestRunsPage />} />
          <Route path="/test-runs/:runName" element={<TestRunDetails />} />
          <Route path="/create-test-run" element={<NewTestRunPage />} />
          <Route path="/continue-run/:runName" element={<ContinueRunPage />} />
          <Route path="/__dev/config" element={<DevConfigPage />} />
        </Routes>
      </main>
    </div>
  );

  return (
    <Routes>
      <Route
        path="/login"
        element={<LoginPage onLoginSuccess={() => setIsAuthenticated(true)} />}
      />
      <Route
        path="/*"
        element={
          isAuthenticated ? <AuthenticatedApp /> : <Navigate to="/login" replace />
        }
      />
    </Routes>
  );
}

export default App;
