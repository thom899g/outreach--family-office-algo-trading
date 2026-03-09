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