import React, { useEffect } from "react";
import { AUTH_PAGE_URL } from "../../config/api";

interface LoginPageProps {
  onLoginSuccess?: () => void;
}

const LoginPage: React.FC<LoginPageProps> = () => {
  useEffect(() => {
    const returnUrl = `${window.location.origin}/`;
    window.location.href = `${AUTH_PAGE_URL}?return_url=${encodeURIComponent(returnUrl)}`;
  }, []);

  return (
    <div className="login-page">
      <div className="login-form">
        <h2>Redirecting to centralized login...</h2>
        <p>Please sign in using the shared authentication portal.</p>
      </div>
    </div>
  );
};

export default LoginPage;
