import os
from openai import OpenAI
from dotenv import load_dotenv


def interpret_audio(audio_command: str):
    # Load the environment variables from the .env file
    load_dotenv()

    client = OpenAI(
        # Get the API key from the environment variables
        api_key=os.getenv("OPENAI_API_KEY")
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "I received this command: "
                + audio_command
                + ". Can you extract and tell me in one word, what I should draw?",
            }
        ],
        model="gpt-4o",
    )

    return chat_completion.choices[0].message.content
