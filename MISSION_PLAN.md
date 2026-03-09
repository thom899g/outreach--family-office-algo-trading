# OUTREACH: Family Office Algo Trading

## Objective
Automated outreach to hunt for a Family offices managing $50M+ in liquid assets seeking crypto exposure contract. Partner with wealth management firms, attend family office investment summits, offer exclusive beta access to proprietary trading signals.

## Strategy
Identify contact -> Draft personalized pitch -> Execute via social_agent.py

## Execution Output
[REASONING]: We are given a MISSION: OUTREACH to Family Offices for algo trading in crypto. We have a detailed master plan (Project Icarus) that outlines the architecture and implementation steps.

We are to start implementing Phase 1: Foundation (Weeks 1-2) which includes:
1. Firebase Project Setup
2. Core Data Pipeline Infrastructure
3. State Machine Framework

We are to write code for the autonomous agent to set up the Firebase project, initialize the Firestore database, and create the initial data structures and state machines.

However, note that we are an autonomous agent and we must operate within the given constraints. We cannot use the browser to create the Firebase project because we are writing code. Instead, we assume that the Firebase project has been created and we have the service account key.

We are to create the initial Firestore schema and the state machine framework.

Let's break down the tasks:

1. **Firebase Project Setup**: We assume that the Firebase project is already created and we have the service account key in a file called `service-account-key.json`. We will initialize the Firebase app and set up Firestore.

2. **Core Data Pipeline Infrastructure**: We will create the initial data collection scripts and the multi-source verification skeleton. However, note that we are in the foundation phase, so we will set up the structure for the data pipeline without implementing the actual data sources.

3. **State Machine Framework**: We will design the Firestore schema for entity state machines and build basic state transition logic.

We are to generate code files for the project.

Let's create the following files:

1. `firebase_setup.py`: To initialize Firebase and set up the Firestore client.
2. `data_pipeline.py`: The core data pipeline infrastructure.
3. `state_machine.py`: The state machine framework for outreach.
4. `requirements.txt`: To list the dependencies.
5. `.env.example`: To show the required environment variables.

We will also create a main script that ties everything together.

We must remember to use robust logging, error handling, and type hints.

Let's start by creating the `requirements.txt` file.

### FILE: requirements.txt
```
firebase-admin==6.2.0
pandas==2.0.3
numpy==1.24.3
requests==2.31.0
beautifulsoup4==4.12.2
scikit-learn==1.3.0
python-dotenv==1.0.0
```

Now, let's create the `.env.example` file. We assume that the service account key file is provided, but we might also have other configuration.

### FILE: .env.example
```
GOOGLE_APPLICATION_CREDENTIALS=service-account-key.json
```

Now, let's create the `firebase_setup.py` file.

### FILE: firebase_setup.py
```python
"""
Firebase setup and initialization.
This module initializes the Firebase app and provides a Firestore client.
"""

import os
import logging
from typing import Optional

import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FirebaseSetup:
    """Class to handle Firebase initialization and Firestore client."""

    _app: Optional[firebase_admin.App] = None
    _db: Optional[firestore.Client] = None

    @classmethod
    def initialize(cls, credential_path: Optional[str] = None) -> None:
        """
        Initialize the Firebase app.

        Args:
            credential_path: Path to the service account key JSON file.
                If not provided, uses GOOGLE_APPLICATION_CREDENTIALS environment variable.

        Raises:
            FileNotFoundError: If the credential file is not found.
            ValueError: If the credential file is invalid.
        """
        if cls._app is not None:
            logger.warning("Firebase app already initialized.")
            return

        if credential_path is None:
            credential_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if credential_path is None:
                raise ValueError(
                    "Credential path must be provided or set in GOOGLE_APPLICATION_CREDENTIALS environment variable."
                )

        if not os.path.exists(credential_path):
            raise FileNotFoundError(f"Credential file not found at {credential_path}")

        try:
            cred = credentials.Certificate(credential_path)
            cls._app = firebase_admin.initialize_app(cred)
            logger.info("Firebase app initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase app: {e}")
            raise

    @classmethod
    def get_firestore_client(cls) -> firestore.Client:
        """
        Get the Firestore client.

        Returns:
            firestore.Client: The Firestore client.

        Raises:
            RuntimeError: If the Firebase app is not initialized.
        """
        if cls._app is None:
            raise RuntimeError("Firebase app not initialized. Call initialize() first.")

        if cls._db is None:
            cls._db = firestore.client(cls._app)
            logger.info("Firestore client created.")

        return cls._db

    @classmethod
    def close(cls) -> None:
        """Close the Firebase app."""
        if cls._app is not None:
            firebase_admin.delete_app(cls._app)
            cls._app = None
            cls._db = None
            logger.info("Firebase app closed.")


# Example usage
if __name__ == "__main__":
    try:
        FirebaseSetup.initialize()
        db = FirebaseSetup.get_firestore_client()
        # Test connection by getting a reference to a collection
        test_ref = db.collection("test").document("test")
        test_ref.set({"test": "test"})
        print("Test write successful.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        FirebaseSetup.close()
```

Now, let's create the `data_pipeline.py` file. This is the core data pipeline infrastructure. We will set up the structure for the data sources and the multi-source verification.

### FILE: data_pipeline.py
```python
"""
Core data pipeline for Project Icarus.
This module handles data collection from various sources and multi-source verification.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime

import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup

from firebase_setup import FirebaseSetup

logger = logging.getLogger(__name__)


class DataSource(ABC):
    """Abstract base class for data sources."""

    @abstractmethod
    def fetch_data(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Fetch data for a given identifier.

        Args:
            identifier: The identifier for the entity (e.g., name, SEC CIK).

        Returns:
            Dictionary of data or None if not found.
        """
        pass

    @abstractmethod
    def source_name(self) -> str:
        """Return the name of the data source."""
        pass


class SECEdgarSource(DataSource):
    """Data source for SEC EDGAR filings."""

    def __init__(self):
        self.base_url = "https://www.sec.gov/edgar/searchedgar/companysearch.html"

    def fetch_data(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Fetch SEC EDGAR data for a given CIK (Central Index Key).

        Args:
            identifier: The CIK number (as string, padded with zeros to 10 digits).

        Returns:
            Dictionary containing filing data.
        """
        cik = identifier.zfill(10)
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"

        headers = {
            "User-Agent": "Project Icarus (contact@example.com)",
            "Accept-Encoding": "gzip, deflate",
            "Host": "data.sec.gov"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return {
                "cik": cik,
                "data": data
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch SEC data for CIK {cik}: {e}")
            return None

    def source_name(self) -> str:
        return "SEC EDGAR"


class FAAAircraftSource(DataSource):
    """Data source for FAA aircraft registry."""

    def __init__(self):
        # The FAA registry is available as a CSV download
        self.csv_url = "https://registry.faa.gov/database/ReleasableAircraft.zip"

    def fetch_data(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Fetch FAA aircraft data for a given N-Number.

        Args:
            identifier: The N-Number (e.g., 'N12345').

        Returns:
            Dictionary containing aircraft data.
        """
        # Note: The FAA registry is a large CSV. We would typically download and index it.
        # For now, we'll simulate by reading from a local file if it exists.
        # We assume the CSV has been downloaded and saved as 'faa_aircraft.csv'
        try:
            df = pd.read_csv('faa_aircraft.csv')
            record = df[df['N-Number'] == identifier].to_dict('records')
            if record:
                return {
                    "n_number": identifier,
                    "data": record[0]
                }
            else:
                logger.warning(f"No FAA aircraft data found for {identifier}")
                return None
        except FileNotFoundError:
            logger.error("FAA aircraft CSV file not found. Please download from https://registry.faa.gov/database/ReleasableAircraft.zip")
            return None

    def source_name(self) -> str:
        return "FAA Aircraft Registry"


class DataPipeline:
    """Main data pipeline for multi-source data collection and verification."""

    def __init__(self, db: Any):
        """
        Initialize the data pipeline.

        Args:
            db: Firestore client.
        """
        self.db = db
        self.sources: List[DataSource] = [
            SECEdgarSource(),
            FAAAircraftSource()
        ]

    def collect_data(self, entity_id: str, identifiers: Dict[str, str]) -> Dict[str, Any]:
        """
        Collect data from all sources for the given entity.

        Args:
            entity_id: The Firestore document ID for the entity.
            identifiers: A dictionary mapping source names to identifiers.

        Returns:
            Dictionary containing collected data and verification status.
        """
        collected_data = {}
        for source in self.sources:
            source_name = source.source_name()
            if source_name in identifiers:
                data = source.fetch_data(identifiers[source_name])
                if data:
                    collected_data[source_name] = data
                else:
                    collected_data[source_name] = None
            else:
                collected_data[source_name] = None
                logger.warning(f"No identifier provided for {source_name}")

        # Store the collected data in Firestore
        entity_ref = self.db.collection("familyOffices").document(entity_id)
        entity_ref.set({
            "collectedData": collected_data,
            "lastUpdated": datetime.utcnow()
        }, merge=True)

        # Run verification
        verification_result = self.verify_data(collected_data)
        entity_ref.set({
            "verification": verification_result
        }, merge=True)

        logger.info(f"Data collected for entity {entity_id}")
        return collected_data

    def verify_data(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify data consistency across sources.

        Args:
            collected_data: Dictionary of data collected from sources.

        Returns:
            Dictionary with verification results.
        """
        # Placeholder for verification logic
        # For now, we just check that we have at least one source with data
        sources_with_data = [k for k, v in collected_data.items() if v is not None]
        confidence = len(sources_with_data) / len(self.sources) if self.sources else 0

        return {
            "sourcesWithData": sources_with_data,
            "confidenceScore": confidence,
            "verificationTimestamp": datetime.utcnow()
        }


if __name__ == "__main__":
    # Example usage
    FirebaseSetup.initialize()
    db = FirebaseSetup.get_firestore_client()
    pipeline = DataPipeline(db)

    # Example entity: a family office with known SEC CIK and FAA N-Number
    entity_id = "example_family_office"
    identifiers = {
        "SEC EDGAR": "0001234567",  # Example CIK
        "FAA Aircraft Registry": "N12345"
    }

    data = pipeline.collect_data(entity_id, identifiers)
    print(f"Collected data: {data}")
```

Now, let's create the `state_machine.py` file for the state machine framework.

### FILE: state_machine.py
```python
"""
State machine framework for outreach in Project Icarus.
Each entity (family office) has a state machine that tracks the outreach process.
"""

import logging
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from firebase_setup import FirebaseSetup

logger = logging.getLogger(__name__)


class OutreachState(Enum):
    """Enum for the possible states in the outreach state machine."""
    IDENTIFIED = "IDENTIFIED"
    RESEARCHING = "RESEARCHING"
    VALUE_CRAFTED = "VALUE_CRAFTED"
    DELIVERED = "DELIVERED"
    ENGAGED = "ENGAGED"
    CLOSED = "CLOSED"  # Added a closed state for completion


class OutreachStateMachine:
    """State machine for outreach to a single entity."""

    def __init__(self, db: Any, entity_id: str):
        """
        Initialize the state machine for an entity.

        Args:
            db: Firestore client.
            entity_id: The Firestore document ID for the entity.
        """
        self.db = db
        self.entity_id = entity_id
        self.state_machine_ref = db.collection("outreachStateMachines").document(entity_id)

    def get_current_state(self) -> Optional[OutreachState]:
        """
        Get the current state of the state machine.

        Returns:
            The current state as an OutreachState, or None if not found.
        """
        doc = self.state_machine_ref.get()
        if doc.exists:
            data = doc.to_dict()
            state_str = data.get("currentState")
            if state_str:
                return OutreachState(state_str)
        return None

    def set_state(self, state: OutreachState, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Set the state of the state machine.

        Args:
            state: The new state.
            metadata: Additional metadata to store.
        """
        update_data = {
            "currentState": state.value,
            "lastUpdated": datetime.utcnow()
        }
        if metadata:
            update_data.update(metadata)

        self.state_machine_ref.set(update_data, merge=True)
        logger.info(f"State for entity {self.entity_id} set to {state.value}")

    def transition(self, new_state: OutreachState, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Transition to a new state if valid.

        Args:
            new_state: The desired new state.
            metadata: Additional metadata.

        Returns:
            True if the transition was successful, False otherwise.
        """
        current_state = self.get_current_state()

        # Define valid transitions
        valid_transitions = {
            OutreachState.IDENTIFIED: [OutreachState.RESEARCHING],
            OutreachState.RESEARCHING: [OutreachState.VALUE_CRAFTED, OutreachState.CLOSED],
            OutreachState.VALUE_CRAFTED: [OutreachState.DELIVERED, OutreachState.CLOSED],
            OutreachState.DELIVERED: [OutreachState.ENGAGED, OutreachState.CLOSED],
            OutreachState.ENGAGED: [OutreachState.CLOSED],
            OutreachState.CLOSED: []  # No transitions out of CLOSED
        }

        if current_state is None:
            # If no current state, assume starting at IDENTIFIED
            current_state = OutreachState.IDENTIFIED
            self.set_state(current_state)

        if new_state in valid_transitions.get(current_state, []):
            self.set_state(new_state, metadata)
            logger.info(f"Transitioned entity {self.entity_id} from {current_state.value} to {new_state.value}")
            return True
        else:
            logger.warning(f"Invalid transition from {current_state.value} to {new_state.value} for entity {self.entity_id}")
            return False

    def schedule_next_action(self, action_type: str, scheduled_time: datetime, 
                             content_hash: Optional[str] = None) -> None:
        """
        Schedule the next action for the entity.

        Args:
            action_type: The type of action (e.g., 'deliver_insight').
            scheduled_time: When the action should be performed.
            content_hash: Optional hash of the content to be delivered.
        """
        next_action = {
            "scheduled": scheduled_time,
            "type": action_type,
            "contentHash": content_hash
        }
        self.state_machine_ref.set({
            "nextAction": next_action
        }, merge=True)
        logger.info(f"Scheduled {action_type} for entity {self.entity_id} at {scheduled_time}")

    def set_patience_clock(self, min_days: int = 42, max_days: int = 90) -> None:
        """
        Set the patience clock for the entity.

        Args:
            min_days: Minimum wait days.
            max_days: Maximum wait days.
        """
        now = datetime.utcnow()
        next_checkin = now + timedelta(days=min_days)
        patience_clock = {
            "minimumWaitDays": min_days,
            "maximumWaitDays": max_days,
            "nextCheckin": next_checkin
        }
        self.state_machine_ref.set({
            "patienceClock": patience_clock
        }, merge=True)
        logger.info(f"Patience clock set for entity {self.entity_id