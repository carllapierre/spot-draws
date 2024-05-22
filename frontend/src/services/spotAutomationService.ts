import axios from "axios";

const SPOT_AUTOMATION_API_URL = "http://localhost:8080/gcode";

export const commandSpotToDraw = async (gcode: string | undefined) => {
  try {
    const formData = new FormData();
    formData.append('gcode', gcode);
    const response = await axios.post(SPOT_AUTOMATION_API_URL, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });

    if (response) {
      console.log("Commanded Spot successfully");
    } else {
      console.error("Failed commanding Spot");
    }
    return response;
  } catch (error) {
    console.error("Error commanding Spot", error);
  }
};