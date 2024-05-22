import os
from openai import OpenAI
from dotenv import load_dotenv


# takes in a list of base64 encoded images and returns a winner, a sungle choice as JSON
def evaluate_images(images, item):

    # Load the environment variables from the .env file
    load_dotenv()

    client = OpenAI(
        # Get the API key from the environment variables
        api_key=os.getenv("OPENAI_API_KEY")
    )

    # create the payload
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Which image the best and simplest outline and represents a {item} the best. Simply answer with an integer represening the image number. The images are as follows:",
                }
            ],
        }
    ]

    # add the images to the payload
    for image in images:
        messages[0]["content"].append(
            {"type": "image_url", "image_url": {"url": image}}
        )

    # send the payload to the API
    response = client.chat.completions.create(
        messages=messages,
        model="gpt-4o",
    )

    # return the result
    return response.choices[0].message.content
