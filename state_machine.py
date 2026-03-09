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