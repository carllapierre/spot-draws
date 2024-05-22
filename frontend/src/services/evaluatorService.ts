import axios from "axios";

const SPEECH_RECOGNITION_API_URL = import.meta.env
  .VITE_SPEECH_RECOGNITION_API_URL;

export const evalImages = async (base64images: Array<string>, item: string) => {
  try {
    const response = await axios.post(`${SPEECH_RECOGNITION_API_URL}/eval`, {
      images: base64images,
      item,
    });

    return response;
  } catch (error) {
    console.error("Error interpreting transcript", error);
  }
};
