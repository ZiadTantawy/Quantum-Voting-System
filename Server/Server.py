import hashlib
import logging
from fastapi import FastAPI, HTTPException
import psycopg2
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from quantum_RNG import quantum_random_number_generator
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from hashlib import sha256
import base64
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram
import numpy as np
import matplotlib.pyplot as plt
import string

# Initialize FastAPI app
app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware setup
app.add_middleware(SessionMiddleware, secret_key="your-secret-key-here")

# Database connection setup (use connection pooling ideally)
def get_db_connection():
    try:
        connection = psycopg2.connect(
            dbname='Quantum-Voting',
            user='postgres',
            password='1234',
            host='localhost',
        )
        return connection
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

def create_tables():
    cursor = None  # Initialize cursor variable here
    try:
        # Connect to the PostgreSQL database
        connection = get_db_connection()
        cursor = connection.cursor()

        # SQL statements to create the tables
        create_ssns_table = '''
        CREATE TABLE IF NOT EXISTS ssns (
            ssn CHAR(14) PRIMARY KEY UNIQUE NOT NULL,
            CONSTRAINT valid_ssn_format CHECK (
                LENGTH(ssn) = 14 AND 
                (LEFT(ssn, 1) = '2' OR LEFT(ssn, 1) = '3') AND 
                ssn NOT LIKE '%[^0-9]%'
            )
        );
        '''

        create_candidates_table = '''
        CREATE TABLE IF NOT EXISTS candidates (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            party VARCHAR(50)
        );
        '''

        create_votes_table = '''
        CREATE TABLE IF NOT EXISTS votes (
            vote_id SERIAL PRIMARY KEY,  
            candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
            ssn CHAR(14) REFERENCES ssns(ssn) ON DELETE CASCADE
        );
        '''
        create_Hash_table = '''
            CREATE TABLE IF NOT EXISTS vote_hashes (
            vote_hash VARCHAR(64) PRIMARY KEY,  -- SHA-256 hash of SSN and candidate ID
            ssn CHAR(14) NOT NULL,  -- Store SSN of the voter
            candidate_id INTEGER NOT NULL,
            FOREIGN KEY (ssn) REFERENCES ssns(ssn),
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
            );
        '''

        # Execute the SQL statements to create the tables
        cursor.execute(create_ssns_table)
        cursor.execute(create_candidates_table)
        cursor.execute(create_votes_table)
        cursor.execute(create_Hash_table)

        # Commit the transaction
        connection.commit()

        logger.info("Tables created successfully")

    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise HTTPException(status_code=500, detail="Error creating tables")
    finally:
        # Ensure cursor and connection are closed properly
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Call the function to create tables
create_tables()
class VoteRequest(BaseModel):
    ssn: str
    candidate_id: int
class Candidate(BaseModel):
    name: str
    party: str = None
class ssn(BaseModel):
    ssn: str

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/candidates")
async def get_candidates():
    try:
        # Establish the connection to the database
        connection = get_db_connection()
        cursor = connection.cursor()

        # Query to get all candidates
        cursor.execute("SELECT id, name, party FROM candidates")
        candidates = cursor.fetchall()

        # Prepare a list to store candidate details
        candidate_list = []
        for candidate in candidates:
            candidate_list.append({
                "id": candidate[0],
                "name": candidate[1],
                "party": candidate[2]
            })

        # Close the cursor and connection
        cursor.close()
        connection.close()

        # Return the list of candidates as a response
        return {"candidates": candidate_list}

    except Exception as e:
        logger.error(f"Failed to retrieve candidates: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve candidates")

def validate_ssn(ssn: str) -> bool:
    # Ensure SSN is 14 digits and starts with 2 or 3
    if len(ssn) == 14 and ssn.isdigit() and ssn[0] in ('2', '3'):
        return True
    return False

def quantum_random_number_generator(num_bits):
  qc = QuantumCircuit(num_bits,num_bits)
  # apply H-gate to each qubit
  for qubit in range(num_bits):
    qc.h(qubit)
  # measure each qubit and store the result in classical bits
  qc.measure(range(num_bits),range(num_bits))
  # Use the Aer's qasm simulator to simulate the circuit
  simulator = AerSimulator()
  # Execute the circuit on the simulator and get the result
  result = simulator.run(qc, shots=1024).result()
  counts = result.get_counts()
  single_result = simulator.run(qc, shots=1).result()
  single_counts = single_result.get_counts()
  # Extract the random bits string from the single outcome
  random_bits = list(single_counts.keys())[0]
  return random_bits

@app.get("/candidate/{name}")
async def get_candidate_by_name(name: str):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id, name, party FROM candidates WHERE name = %s", (name,))
        candidate = cursor.fetchone()

        if candidate is None:
            raise HTTPException(status_code=404, detail="Candidate not found")

        return {"id": candidate[0], "name": candidate[1], "party": candidate[2]}
    
    except Exception as e:
        logger.error(f"Error fetching candidate by name: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/vote")
async def cast_vote(vote_request: VoteRequest):
    try:
        ssn = vote_request.ssn
        candidate_id = vote_request.candidate_id
        
        # 1. Check if SSN exists in the 'ssns' table
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM ssns WHERE ssn = %s", (ssn,))
        ssn_exists = cursor.fetchone()[0]

        if ssn_exists == 0:
            raise HTTPException(status_code=400, detail="SSN not found")

        # 2. Check if SSN has already voted
        cursor.execute("SELECT COUNT(*) FROM vote_hashes WHERE ssn = %s", (ssn,))
        already_voted = cursor.fetchone()[0]

        if already_voted > 0:
            raise HTTPException(status_code = 400, detail="You have already voted")

        # 3. Generate QRNG and hash SSN + candidate_id + QRNG
        qrng_value_bits = quantum_random_number_generator(32)  # Generate quantum random number
        qrng_value = int(qrng_value_bits, 2)  # Convert binary string to integer
        vote_data = f"{ssn}-{candidate_id}-{qrng_value}"
        vote_hash = hashlib.sha256(vote_data.encode('utf-8')).hexdigest()

        # 4. Insert the vote into the 'vote_hashes' table
        cursor.execute(
            "INSERT INTO vote_hashes (ssn, candidate_id, vote_hash) VALUES (%s, %s, %s)",
            (ssn, candidate_id, vote_hash)
        )
        connection.commit()

        # 5. Retrieve the candidate's name from the 'candidates' table
        cursor.execute("SELECT name FROM candidates WHERE id = %s", (candidate_id,))
        candidate = cursor.fetchone()

        if candidate is None:
            raise HTTPException(status_code=404, detail="Candidate not found")

        candidate_name = candidate[0]

        # Close connection
        cursor.close()
        connection.close()

        return {"message": f"Vote cast for {candidate_name}. Thank you for voting!"}

    except Exception as e:
        logger.error(f"Error casting vote: {e}")
        raise e