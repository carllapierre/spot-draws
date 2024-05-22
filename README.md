# Osedea Hackathon - AI-Powered Drawing with SPOT

This repository contains the code developed during a 16-hour hackathon at [Osedea](https://www.osedea.com/), sponsored by [Modal Labs](https://modal.com/). The goal of the project was to enable our Boston Dynamics robot, SPOT, to register a vocal command to draw something and then execute the drawing.

![Demo](./assets/demo.gif)

## Project Description

Our project aims to create a seamless pipeline where SPOT can take a vocal command, understand it, generate an image based on the command, and finally draw it. The workflow involves several key components:

1. **Stable Diffusion XL Modal**: Used to generate images from text prompts.
2. **Whisper**: Captures voice audio and transcribes it to text.
3. **OpenAI**: Analyzes the intent and pulls the item to draw.
4. **Modal**: Runs the entire process on serverless GPU compute for efficiency.

## Repository Structure

This monorepo consists of four main sections (though it ideally should have five):

### 1. Frontend

A React TypeScript frontend for the app to visualize the workflow from voice input to image generation to SPOT drawing.

**Setup:**

```sh
npm install
```

Setup your `.env` file:

```
VITE_SPEECH_RECOGNITION_API_URL=<url_of_the_speech_recognition_backend>
```

### 2. Automation

Contains the code to send GCODE commands to SPOT.

### 3. Image Processing

Contains the Modal code for image diffusion and image-to-GCODE conversion.

**Setup:**

```
pip install modal 
modal setup 
modal deploy diffusion.py 
modal deploy vectorizer.py
```

This sets up live endpoints for the serverless functions, one for generating images on an A10G GPU and the other for image processing on the CPU.

### 4. Speech Recognition

Integrates Whisper for detecting voice commands and extracting intent. Also includes an evaluator using GPT Vision to find the best drawing.

**Setup:** Create a virtual environment and install requirements:

```
python -m venv venv source venv/bin/activate pip install -r requirements.txt`
```

Copy the example environment file and set up your OpenAI API 
```
cp .env_example .env 
```

Launch backend with 
```
python main.py
```


## Code Quality

Please note that the code is slightly dirty due to the limited time we had to write it. Improvements and refactoring are planned for the future.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgements

We would like to thank Modal Labs for sponsoring this hackathon and providing the resources necessary to bring this project to life.

---

Feel free to contribute, open issues, or submit pull requests to improve this project. Happy hacking!
