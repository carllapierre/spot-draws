import { useState } from "react";
import GCode from "./components/GenerateImage/GCode";
import { Header } from "./components/Header/Header";
import { Landing } from "./components/Landing/Landing";
import { Record } from "./components/Record/Record";
import { Validate } from "./components/Validate/Validate";
import { DrawObject } from "./models/DrawObject";

function App() {
  const [step, setStep] = useState<number>(0);
  /** State to manage the recording process */
  const [drawObject, setDrawObject] = useState<DrawObject>({
    audioUrl: null,
    audioBlob: null,
    transcript: "",
    interpretation: "",
  });

  return (
    <>
      <Header setStep={setStep} />

      {step === 0 && <Landing setStep={setStep} />}
      {step === 1 && (
        <Record step={step} setStep={setStep} setDrawObject={setDrawObject} />
      )}
      {step === 2 && (
        <Validate
          step={step}
          setStep={setStep}
          drawObject={drawObject}
          setDrawObject={setDrawObject}
        />
      )}
      {/* {step === 3 && (
        <GenerateImage
          step={step}
          setStep={setStep}
          drawObject={drawObject}
          setDrawObject={setDrawObject}
        />
      )} */}
      {step === 3 && <GCode item={drawObject.interpretation} />}

      {/* {step === 1 && <Record />}
      {step === 2 && <Validate />}
      {step === 3 && <GenerateImage />} */}
    </>
  );
}

export default App;
