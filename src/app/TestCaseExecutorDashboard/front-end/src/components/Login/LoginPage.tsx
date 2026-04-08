import React, { useEffect } from "react";
import { getLoginUrl } from "../../utils/auth";

interface LoginPageProps {
  onLoginSuccess?: () => void;
}

const LoginPage: React.FC<LoginPageProps> = () => {
  useEffect(() => {
    const returnUrl = window.location.search
      ? `${window.location.origin}/${window.location.search}`
      : `${window.location.origin}/`;
    window.location.href = getLoginUrl(returnUrl);
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
