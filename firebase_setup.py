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