import os
from groq import Groq

class GroqClient:
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            # Fallback or explicit error - for now, we'll initialize but calls will fail if key missing
            print("Warning: GROQ_API_KEY not found in environment variables.")
            self.client = None
        else:
            self.client = Groq(api_key=api_key)

    def generate(self, prompt: str, system_message: str = "You are a helpful travel assistant.") -> str:
        """
        Generates a response from Groq.
        """
        if not self.client:
            return "Error: GROQ_API_KEY not set."
            
        try:
            completion = self.client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4096,
                top_p=1,
                stream=False,
                stop=None,
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {str(e)}"
