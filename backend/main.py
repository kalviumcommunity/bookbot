import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load API key from backend/.env
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError(f"GEMINI_API_KEY is not set (looked in {env_path})")

# Configure Gemini client
genai.configure(api_key=api_key)

# Create model with temperature parameter and function-calling tool
model = genai.GenerativeModel(
    "gemini-1.5-flash",
    generation_config={"temperature": 0.7},
    tools=[
        {
            "function_declarations": [
                {
                    "name": "get_weather",
                    "description": "Get the current weather for a city",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string", "description": "The name of the city"}
                        },
                        "required": ["city"]
                    }
                }
            ]
        }
    ]
)

# Example function the AI can call
def get_weather(city: str):
    """Mock weather function — replace with real API if you want"""
    fake_weather_data = {
        "Berlin": "Cloudy, 18°C",
        "Paris": "Sunny, 22°C",
        "New York": "Rainy, 25°C"
    }
    return fake_weather_data.get(city, f"Sorry, I don't have weather data for {city}.")

# ---- Prompt templates ----
one_shot_example = """
You are a helpful assistant.

Example:
User: What is the capital of Germany?
AI: Berlin

Now answer the following query in the same way.
"""

multi_shot_examples = """
You are a helpful assistant.

Examples:
User: What is the capital of France?
AI: Paris

User: What is 5 + 7?
AI: 12

User: Convert 'Hello' to Python print statement.
AI: print("Hello")

Now answer the following query in the same way.
"""

# Safe Chain-of-Thought (CoT) prompting:
# Ask the model to reason privately, but only output a final answer + brief high-level rationale.
def build_cot_prompt(user_query: str) -> str:
    return f"""
You are a careful reasoning assistant.
Think through the problem step-by-step in your private scratchpad, but DO NOT reveal those internal steps.
Only return:
1) Final answer
2) A brief high-level rationale (2–4 short bullets, no detailed step-by-step math or hidden chain-of-thought).

Question: {user_query}

Return format:
Final: <final answer>
Why (brief):
- <bullet 1>
- <bullet 2>
- <bullet 3>
"""

def extract_function_call(response):
    """Safely find a function_call (if any) in the response."""
    try:
        for cand in response.candidates:
            for part in cand.content.parts:
                fc = getattr(part, "function_call", None)
                if fc:
                    return fc
    except Exception:
        pass
    return None

def ai_chat():
    print("🤖 AI Chatbot (Dynamic Prompting + Function Calling + Safe CoT)  — type 'exit' to quit\n")
    print("Tips:")
    print(" • Type '/cot <your question>' to force Chain-of-Thought mode")
    print(" • Ask 'why/how/solve/explain' to auto-trigger CoT")
    print(" • Ask 'convert/code/format' to trigger multi-shot\n")

    while True:
        query = input("You: ")
        if query.lower() == "exit":
            print("Goodbye 👋")
            break

        try:
            use_cot = False
            raw_query = query

            # Manual CoT toggle with prefix
            if query.strip().lower().startswith("/cot "):
                use_cot = True
                raw_query = query.strip()[5:]  # remove '/cot '

            # Auto CoT for reasoning-heavy queries
            reasoning_triggers = ["why", "how", "explain", "prove", "derive", "solve", "estimate", "plan"]
            if any(w in raw_query.lower() for w in reasoning_triggers):
                use_cot = True

            # Decide prompting strategy
            if use_cot:
                prompt = build_cot_prompt(raw_query)
                print("🧠 Using Chain-of-Thought (safe) Prompting")
            elif "capital" in raw_query.lower():   # One-shot for factual Q&A
                prompt = one_shot_example + "\nUser: " + raw_query + "\nAI:"
                print("🟢 Using One-Shot Prompting")
            elif any(word in raw_query.lower() for word in ["convert", "example", "code", "format"]):
                prompt = multi_shot_examples + "\nUser: " + raw_query + "\nAI:"
                print("🟣 Using Multi-Shot Prompting")
            else:
                prompt = raw_query
                print("🔵 Using Zero-Shot Prompting")

            # Generate response
            response = model.generate_content(prompt)

            # Function call handling (if the model chose to call a tool)
            fn_call = extract_function_call(response)
            if fn_call:
                fn_name = fn_call.name
                args = fn_call.args or {}
                if fn_name == "get_weather":
                    result = get_weather(args.get("city", ""))
                    print(f"🌦️ Weather result: {result}\n")
                else:
                    print(f"⚠️ Function {fn_name} not implemented.\n")
            else:
                print("AI:", response.text.strip(), "\n")

        except Exception as e:
            print("Error:", e, "\n")

if __name__ == "__main__":
    ai_chat()
