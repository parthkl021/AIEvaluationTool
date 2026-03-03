import React from "react";
import "./Header.css";
import AppButton from "../common/Button/AppButton";
import { useNavigate } from "react-router-dom";
import testRun from "../../../src/assets/logo/Test-run.png"

const Header: React.FC = () => {
  const navigate = useNavigate();
  
  return (
    <div className="header-container">  
      <div className="header-content">
        <img src={testRun} alt="" />
        <h1 className="page-title">Test Runs</h1>
      </div>
    </div>
  );
};

export default Header;
