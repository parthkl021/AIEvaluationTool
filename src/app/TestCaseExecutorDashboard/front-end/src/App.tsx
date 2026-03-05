import { Routes, Route } from "react-router-dom";
import React, { useState, useEffect } from 'react';
import logo from './logo.svg';
import './App.css';
import TestRunsPage from './components/test-runs/TestRunsPage';
import TestRunDetails from './components/test-run-details/TestRunDetailsPage';
import Login from './components/Login';

import Navbar from "./components/common/Navbar";
import NewTestRunPage from "./components/new-test-run/NewTestRunPage";
import DevConfigPage from "./components/DevConfig/DevConfig";
import ContinueRunPage from "./components/continue-test-run/ContinueTestRunPage";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem('access_token');
    setIsAuthenticated(!!token);
    setLoading(false);
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  return (
     <div className="app-container">
        <Navbar /> {/* Add the Navbar here */}
        <Routes>
          <Route path="/" element={<TestRunsPage />} />

          {/* 👇 THIS is the route you're navigating to */}
          <Route path="/test-runs/:runName" element={<TestRunDetails />} />
          <Route path="/create-test-run" element={<NewTestRunPage />} />
          <Route path="/continue-run/:runName" element={<ContinueRunPage />} />
          <Route path="/__dev/config" element={<DevConfigPage />} />
        </Routes>
     </div>

  );
}

export default App;
