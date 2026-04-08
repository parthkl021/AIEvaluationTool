import { Routes, Route } from "react-router-dom";
import React, { useState, useEffect } from "react";

import "./App.css";
import LoginPage from "./components/Login/LoginPage";
import TestRunsPage from "./components/test-runs/TestRunsPage";
import TestRunDetails from "./components/test-run-details/TestRunDetailsPage";
import NewTestRunPage from "./components/new-test-run/NewTestRunPage";
import DevConfigPage from "./components/DevConfig/DevConfig";
import ContinueRunPage from "./components/continue-test-run/ContinueTestRunPage";
import Sidebar from "./components/common/sidebar/sidebar";
import Analysis from "./components/Analysis/Analysis";
import { redirectToLogin } from "./utils/auth";


function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const hash = window.location.hash.replace(/^#/, "");
    if (hash) {
      const values = Object.fromEntries(new URLSearchParams(hash));
      if (values.access_token && values.refresh_token) {
        localStorage.setItem("access_token", values.access_token);
        localStorage.setItem("refresh_token", values.refresh_token);
        if (values.user_name) localStorage.setItem("user_name", values.user_name);
        if (values.role) localStorage.setItem("role", values.role);
        window.history.replaceState({}, document.title, window.location.pathname + window.location.search);
      }
    }
    const token = localStorage.getItem("access_token");
    if (!token) {
      redirectToLogin();
      return;
    }
    setIsAuthenticated(true);
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
          <Route path="/analyse/:runName" element={<Analysis/>} />
        </Routes>
      </main>
    </div>
  );

  return (
    <Routes>
      <Route
        path="/login"
        element={<LoginPage />}
      />
      <Route
        path="/*"
        element={
          isAuthenticated ? <AuthenticatedApp /> : <LoginPage />
        }
      />
    </Routes>
  );
}

export default App;
