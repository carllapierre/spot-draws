import axios from "axios";

const SPEECH_RECOGNITION_API_URL = import.meta.env
  .VITE_SPEECH_RECOGNITION_API_URL;

export const sendTranscription = async (transcript: string) => {
  try {
    const response = await axios.post(
      `${SPEECH_RECOGNITION_API_URL}/interpret`,
      transcript
    );

    if (response) {
      console.log("Transcription interpreted successfully");
      return response.data;
    } else {
      console.error("Failed to interpret transcript");
    }
  } catch (error) {
    console.error("Error interpreting transcript", error);
  }
};
