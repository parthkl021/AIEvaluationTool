import { Home, Users, LogOut } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import ceraiLogo from "../../../assets/logo/cerai-logo.png";
import { LOGIN_URL } from "../../../config/api";
import "./sidebar.css";

interface UserInfo {
  user_name: string;
  email: string;
  role: string;
}

interface NavItem {
  icon: typeof Home;
  label: string;
  path: string;
  externalUrl?: string;
}

interface SidebarProps {
  onLogout?: () => void;
}

const Sidebar = ({ onLogout }: SidebarProps) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [userInfo, setUserInfo] = useState<UserInfo>({ user_name: "UserName", email: "", role: "Admin" });
  const [isLoading, setIsLoading] = useState(true);
  const loginUrl = LOGIN_URL;
  const testDataUrl = process.env.REACT_APP_TEST_DATA_URL || "http://localhost:8080/dashboard";
  const userListUrl = process.env.REACT_APP_USER_LIST_URL || "http://localhost:8080/users";
  const tdmsBaseUrl =
    process.env.REACT_APP_TDMS_API_BASE_URL || "http://localhost:8000";
  const currentUserUrl =
    process.env.REACT_APP_CURRENT_USER_URL ||
    `${tdmsBaseUrl}/api/users/me`;
  const handleLogout = async () => {
    const refreshToken = localStorage.getItem("refresh_token");

    if (refreshToken) {
      try {
        await fetch(`${process.env.REACT_APP_AUTH_SERVICE_URL || "http://localhost:7500"}/logout`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      } catch (error) {
        console.warn("Logout request failed", error);
      }
    }

    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user_name");
    localStorage.removeItem("role");
    onLogout?.();
    navigate("/login");
  };

  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const token = localStorage.getItem("access_token");
        if (!token) {
          navigate("/login");
          return;
        }

        const response = await fetch(currentUserUrl, {
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          credentials: "include",
        });

        if (response.ok) {
          const data: UserInfo = await response.json();
          setUserInfo(data);
        } else if (response.status === 401) {
          // Token expired or invalid
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user_name");
    localStorage.removeItem("role");
    onLogout?.();
    navigate("/login");
        } else {
          // Use fallback values from localStorage if API fails
          const storedUsername = localStorage.getItem("user_name");
          if (storedUsername) {
            setUserInfo({ user_name: storedUsername, email: "", role: "User" });
          }
        }
      } catch (error) {
        // Use fallback values from localStorage if API fails
        const storedUsername = localStorage.getItem("user_name");
        if (storedUsername) {
          setUserInfo({ user_name: storedUsername, email: "", role: "User" });
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserInfo();
  }, [currentUserUrl, navigate]);

  const navItems: NavItem[] = [
    { icon: Home, label: "Home", path: "/" },
    { icon: Home, label: "Test Data", path: "", externalUrl: testDataUrl },
    { icon: Users, label: "User's List", path: "", externalUrl: userListUrl },
  ];

  return (
    <aside className="sidebar-shell">
      <div className="sidebar-brand-wrap">
        <div className="sidebar-brand-pill">
          <img src={ceraiLogo} alt="CeRAI" className="sidebar-brand-image" />
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = !item.externalUrl && location.pathname === item.path;

          if (item.externalUrl) {
            return (
              <a
                key={`${item.label}-${item.externalUrl}`}
                href={item.externalUrl}
                className="sidebar-nav-item sidebar-nav-item-link"
              >
                <Icon className="sidebar-nav-icon" />
                <span>{item.label}</span>
              </a>
            );
          }

          return (
            <Link
              key={item.path}
              to={item.path}
              className={`sidebar-nav-item ${isActive ? "sidebar-nav-item-active" : "sidebar-nav-item-link"}`}
            >
              <Icon className="sidebar-nav-icon" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user-row">
          <div className="sidebar-user-icon-wrap">
            <Users className="sidebar-user-icon" />
          </div>
          <div className="sidebar-user-meta">
            <div className="sidebar-user-name">{isLoading ? "Loading..." : userInfo.user_name}</div>
            <div className="sidebar-user-role">
              {isLoading ? "" : userInfo.role.charAt(0).toUpperCase() + userInfo.role.slice(1)}
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={handleLogout}
          className="sidebar-nav-item sidebar-nav-item-link sidebar-nav-button"
        >
          <LogOut className="sidebar-nav-icon" />
          <span>Log out</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
