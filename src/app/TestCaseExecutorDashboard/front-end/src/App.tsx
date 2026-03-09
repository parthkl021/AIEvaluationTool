import { Routes, Route } from "react-router-dom";
import React, { useState, useEffect } from 'react';

import "./App.css";
import TestRunsPage from "./components/test-runs/TestRunsPage";
import TestRunDetails from "./components/test-run-details/TestRunDetailsPage";
// import Login from './components/Login';

import NewTestRunPage from "./components/new-test-run/NewTestRunPage";
import DevConfigPage from "./components/DevConfig/DevConfig";
import ContinueRunPage from "./components/continue-test-run/ContinueTestRunPage";
import Sidebar from "./components/common/sidebar/sidebar";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const loginUrl = process.env.REACT_APP_LOGIN_URL || "http://localhost:8080/login";

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem('access_token');
    setIsAuthenticated(!!token);
    setLoading(false);
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  // if (!isAuthenticated) {

  // }

  return (
    <div className="app-container">
      <div className="sidebar">
        <Sidebar />
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
}

export default App;
