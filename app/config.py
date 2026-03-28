import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
WANDB_API_KEY = os.getenv("WANDB_API_KEY")
LUMA_EVENT_URL = os.getenv("LUMA_EVENT_URL", "https://luma.com/hh5k4ahp")
PLATFORM_EMAIL = os.getenv("PLATFORM_EMAIL")
PLATFORM_PASSWORD = os.getenv("PLATFORM_PASSWORD")
FOURTHWALL_API_USERNAME = os.getenv("username")
FOURTHWALL_API_PASSWORD = os.getenv("password")
