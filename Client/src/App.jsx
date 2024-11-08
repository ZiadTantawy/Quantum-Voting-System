import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import VotingForm from './Pages/Vote';
import './index.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route exact path="/" element={<VotingForm />} />
      </Routes>
    </Router>
  );
}

export default App;