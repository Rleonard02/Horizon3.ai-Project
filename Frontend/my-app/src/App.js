import React from 'react';
import RepoFetcher from './components/RepoFetcher'; 
import "./App.css";
import QueryForm from './components/query_interface';
//import Login from "./Pages/Login";
//import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

function App() {
  return (/*
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />

        <Route path="/login" element={<Login />} />
      </Routes>
    </Router>*/
    <div>
      <h1>GitHub Repository Fetcher</h1>
      <RepoFetcher />
      <h1>Query Metadata</h1>
      <QueryForm />
    </div>
  );
}

export default App;
