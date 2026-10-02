import os

class WhatsAppConfig:
    # UI Interaction delays (in seconds) depending on machine speed
    APP_LAUNCH_DELAY = float(os.getenv("WA_APP_LAUNCH_DELAY", "2.0"))
    MODAL_OPEN_DELAY = float(os.getenv("WA_MODAL_OPEN_DELAY", "2.0"))
    SEARCH_TYPE_DELAY = float(os.getenv("WA_SEARCH_TYPE_DELAY", "2.0"))
    ACTION_DELAY = float(os.getenv("WA_ACTION_DELAY", "2.0"))

    # Safety Policies
    REQUIRE_CALL_CONFIRMATION = True
    REQUIRE_MESSAGE_CONFIRMATION = False

    # Retries
    MAX_RETRIES = 2
    TIMEOUT_SECONDS = 15

    # App Names
    APP_NAME = "WhatsApp"
