from enum import Enum

class WAState(Enum):
    IDLE = "idle"
    PREPARING = "preparing"
    RESOLVING_CONTACT = "resolving_contact"
    OPENING_CHAT = "opening_chat"
    PREPARING_MESSAGE = "preparing_message"
    SENDING = "sending"
    INITIATING_CALL = "initiating_call"
    COMPLETED = "completed"
    FAILED = "failed"
    AWAITING_CONFIRMATION = "awaiting_confirmation"

class StateMachine:
    def __init__(self):
        self.state = WAState.IDLE

    def transition_to(self, new_state: WAState):
        self.state = new_state

    def get_state(self) -> WAState:
        return self.state
