import { LOGIN_URL } from "../config/api";

export const clearSession = (): void => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user_name");
  localStorage.removeItem("role");
};

export const redirectToLogin = (): void => {
  clearSession();
  window.location.replace(LOGIN_URL);
};
