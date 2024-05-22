import axios from "axios";

const GCODE_GENERATION_API_URL =
  "https://osedea-team-5--smart-diffusion-xl-model-web-inference.modal.run/";

export const generateGCode = async (item: string | undefined) => {
  try {
    const response = await axios.get(
      `${GCODE_GENERATION_API_URL}?item=${item}&max_lines=100`
    );

    if (response) {
      console.log("G-code generated successfully");
    } else {
      console.error("Failed to generate G-code");
    }
    return response;
  } catch (error) {
    console.error("Error generating G-code", error);
  }
};