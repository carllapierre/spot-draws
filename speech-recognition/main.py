from fastapi import FastAPI, UploadFile, File, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from whisper_recognition import transcribe_audio
from open_ai_recognition import interpret_audio
from open_ai_eval import evaluate_images
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Welcome to AI Hackathon 2024!"}


@app.post("/recognize")
async def recognize(audio_file: UploadFile = File(...)):
    try:
        # Log the filename and content type
        print(
            f"Received file: {audio_file.filename}, Content-Type: {audio_file.content_type}"
        )

        # Save the uploaded audio file temporarily (for debugging purposes)
        with open(audio_file.filename, "wb") as buffer:
            buffer.write(await audio_file.read())

        # Call the transcribe_audio function with the path of the saved audio file
        transcription = transcribe_audio(audio_file.filename)

        # Return the transcription result
        return {
            "message": "Audio file received and transcribed successfully",
            "transcription": transcription,
        }
    except Exception as e:
        # Log any errors that occur during processing
        print(f"Error processing audio file: {e}")
        # Return a 500 Internal Server Error response with error details
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error", "details": str(e)},
        )


@app.post("/interpret")
async def interpret(transcript: str = Body(...)):
    try:
        result = interpret_audio(transcript)
        return {
            "message": "Transcription interpreted successfully",
            "result": result,
        }
    except Exception as e:
        # Log and return error response
        print(f"Error interpreting transcript: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error", "details": str(e)},
        )


@app.post("/eval")
async def eval(item: str = Body(...), images: list = Body(...)):
    result = evaluate_images(images, item)
    return {
        "message": "Evaluation interpreted successfully",
        "result": result,
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)
