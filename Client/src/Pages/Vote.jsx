import React, { useState, useEffect } from "react";
import "../Voting.css";

export default function VotingForm() {
  const [candidates, setCandidates] = useState([]);
  const [ssn, setSsn] = useState("");
  const [selectedCandidate, setSelectedCandidate] = useState("");
  const [error, setError] = useState("");
  const [isSsnHidden, setIsSsnHidden] = useState(true);
  const [loading, setLoading] = useState(true);

  // Fetch the candidates when the component mounts
  useEffect(() => {
    fetch("http://localhost:8000/candidates")
      .then((response) => response.json())
      .then((data) => {
        setCandidates(data.candidates);  // Set candidates in state
        setLoading(false);  // Set loading to false after data is fetched
      })
      .catch((error) => {
        console.error("Error fetching candidates:", error);
        setError("An error occurred while fetching candidates.");
        setLoading(false);  // Set loading to false even on error
      });
  }, []);

  const fetchCandidateId = (name) => {
    fetch(`http://localhost:8000/candidate/${name}`)
        .then(response => response.json())
        .then(data => {
            setSelectedCandidate(data.id); // Save candidate ID
            setError('');
        })
        .catch(err => setError("Candidate not found"));
};

const handleVoteSubmit = (event) => {
    event.preventDefault();
    if (!selectedCandidate) {
        setError("Please select a valid candidate.");
        return;
    }

    // Validate SSN (must be 14 digits)
    if (!ssn || ssn.length !== 14 || !/^\d+$/.test(ssn)) {
      setError("Please enter a valid 14-digit SSN.");
      return;
    }

    // Ensure a candidate is selected
    if (!selectedCandidate) {
      setError("Please select a candidate.");
      return;
    }

    // Create the payload to send to the backend
    const payload = {
      ssn: ssn,
      candidate_id: selectedCandidate,
    };

    // Submit the vote (send the request to backend)
    fetch('http://localhost:8000/vote', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => { throw new Error(data.detail); });
            }
            return response.json();
        })
        .then(data => {
            alert("Vote cast successfully!"); // If no error, show success
        })
        .catch(err => {
            // Display error message returned from backend
            setError(err.message); // Set the error message state
        });
};


  const toggleSsnVisibility = () => {
    setIsSsnHidden(!isSsnHidden);
  };

  // Loading spinner while candidates are being fetched
  if (loading) {
    return <div>Loading candidates...</div>;
  }

  return (
    <div className="voting-form-container">
      <div className="voting-form">
        <h2>Cast Your Vote</h2>
        <p>Enter your SSN and select a candidate to vote.</p>
        <form onSubmit={handleVoteSubmit}>
          <div className="form-group">
            <label htmlFor="ssn" style={{ fontWeight: "bold" }}>
              Social Security Number
            </label>
            <div className="input-container">
              <input
                id="ssn"
                type={isSsnHidden ? "password" : "text"}
                placeholder="Enter your SSN"
                value={ssn}
                onChange={(e) => setSsn(e.target.value)}
                maxLength={14}
              />
              <button
                type="button"
                onClick={toggleSsnVisibility}
                className="toggle-visibility-btn"
                aria-label={isSsnHidden ? "Show SSN" : "Hide SSN"}
              >
                {isSsnHidden ? (
                  <svg
                    fill="#000000"
                    width="15px"
                    height="15px"
                    viewBox="0 0 35 35"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path d="M17.5,23.625A6.125,6.125,0,1,1,23.624,17.5,6.132,6.132,0,0,1,17.5,23.625Zm0-9.749A3.625,3.625,0,1,0,21.124,17.5,3.629,3.629,0,0,0,17.5,13.876Z" />
                    <path d="M17.494,29.079A19.508,19.508,0,0,1,.831,19.616a4.119,4.119,0,0,1,0-4.232,19.269,19.269,0,0,1,16.66-9.463,19.54,19.54,0,0,1,16.672,9.462,4.118,4.118,0,0,1,0,4.234A19.517,19.517,0,0,1,17.494,29.079Zm0-20.658A16.792,16.792,0,0,0,2.978,16.669a1.643,1.643,0,0,0,0,1.666,16.994,16.994,0,0,0,14.516,8.244,16.784,16.784,0,0,0,14.528-8.244,1.644,1.644,0,0,0,0-1.668A16.8,16.8,0,0,0,17.494,8.421Z" />
                  </svg>
                ) : (
                  <svg
                    fill="#000000"
                    width="15px"
                    height="15px"
                    viewBox="0 0 1024 1024"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path d="M844.877 118.781L567.185 396.47c-16.708-7.997-35.426-12.474-55.185-12.474-70.694 0-128 57.309-128 128 0 19.763 4.478 38.477 12.474 55.185l-270.69 270.69 60.34 60.339 158.277-158.276C395.54 757.159 452.19 767.996 512 767.996c115.823 0 219.797-40.64 294.839-89.6 37.559-24.499 69.001-51.81 91.575-78.532 20.809-24.627 40.252-55.979 40.252-87.868 0-31.885-19.443-63.241-40.252-87.868-22.575-26.722-54.016-54.031-91.575-78.533a547.946 547.946 0 00-42.859-25.24l141.235-141.233-60.339-60.34zM700.322 384.012c21.666 9.997 41.749 21.215 59.895 33.052 31.932 20.832 56.725 42.857 73.015 62.134 8.145 9.643 13.589 17.92 16.819 24.371 2.483 4.958 3.089 7.684 3.238 8.427-.149.742-.755 3.469-3.238 8.427-3.23 6.451-8.674 14.729-16.819 24.371-16.29 19.277-41.084 41.301-73.015 62.135-63.936 41.711-151.966 75.733-248.218 75.733-34.155 0-67.277-4.284-98.651-11.678l43.466-43.465c16.708 8 35.426 12.476 55.185 12.476 70.694 0 128-57.306 128-128 0-19.759-4.48-38.477-12.476-55.185l72.798-72.799zM263.783 606.929c1.53.998 3.074 1.993 4.631 2.978l-61.579 61.581c-33.009-22.669-60.776-47.386-81.251-71.625-20.809-24.627-40.251-55.979-40.251-87.868 0-31.885 19.443-63.241 40.251-87.868 22.576-26.722 54.016-54.031 91.574-78.533 75.044-48.957 179.017-89.598 294.841-89.598 34.641 0 68.22 3.635 100.284 10.041l-76.006 76.009A413.57 413.57 0=" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          <div className="form-group">
            <label style={{ fontWeight: "bold" }}>Select a Candidate</label>
            <select onChange={(e) => fetchCandidateId(e.target.value)}>
              <option value="">Select a Candidate</option>
              {candidates.map((candidate) => (
                <option key={candidate.id} value={candidate.name}>
                  {candidate.name}
                </option>
              ))}
            </select>
          </div>

          {error && <p className="error">{error}</p>}

          <button type="submit" className="submit-btn">
            Submit Vote
          </button>
        </form>
        <p className="confidentiality-note">
          Your vote is confidential and secure. Your SSN is used for verification purposes only.
        </p>
      </div>
    </div>
  );
}
