import axios from "axios";

const SPEECH_RECOGNITION_API_URL = import.meta.env
  .VITE_SPEECH_RECOGNITION_API_URL;

export const sendAudioFile = async (audioBlob: Blob) => {
  console.log(SPEECH_RECOGNITION_API_URL);
  const formData = new FormData();
  formData.append("audio_file", audioBlob, "recording.wav");

  try {
    const response = await axios.post(
      `${SPEECH_RECOGNITION_API_URL}/recognize`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );

    if (response) {
      console.log("Audio uploaded successfully");
      return response.data;
    } else {
      console.error("Failed to upload audio");
    }
  } catch (error) {
    console.error("Error uploading audio", error);
  }
};
