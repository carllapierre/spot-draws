import { DrawObject } from "../../models/DrawObject";
import { Container } from "../Common/Container/Container";
import GCode from "./GCode";

interface ValidateProps {
  step: number;
  setStep: React.Dispatch<React.SetStateAction<number>>;
  drawObject: DrawObject;
  setDrawObject: React.Dispatch<React.SetStateAction<DrawObject>>;
}

export const GenerateImage: React.FC<ValidateProps> = ({
  step,
  setStep,
  drawObject,
  setDrawObject,
}) => {
  return (
    <Container
      step={step}
      title="Generate image"
      subtitle="The word below has been generate from your request. Press click on generate to create image outlines or back to start over."
    >
      <input
        style={{
          padding: "10px",
          fontSize: "16px",
          borderRadius: "5px",
          border: "1px solid #ccc",
          marginBottom: "10px",
          background: "transparent",
          color: "black",
        }}
        type="text"
        placeholder="Item..."
        value={drawObject.interpretation}
        onChange={(e) =>
          setDrawObject({ ...drawObject, interpretation: e.target.value })
        }
      />
      <GCode item={drawObject.interpretation} />
    </Container>
  );
};
