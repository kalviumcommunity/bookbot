import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load API key from backend/.env (same directory as this file)
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError(f"GEMINI_API_KEY is not set (looked in {env_path})")

# Configure Gemini client
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

def zero_shot_chat():
    print("🤖 Zero-Shot AI Chatbot (type 'exit' to quit)\n")

    while True:
        query = input("You: ")
        if query.lower() == "exit":
            print("Goodbye 👋")
            break

        try:
            # Generate a response using Gemini
            response = model.generate_content(query)
            print("AI:", response.text.strip(), "\n")
        except Exception as e:
            print("Error:", e, "\n")

if __name__ == "__main__":
    zero_shot_chat()
