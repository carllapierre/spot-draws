import { useState } from "react";
import { DrawObject } from "../../models/DrawObject";
import { sendAudioFile } from "../../services/speechRecognitionService";
import { sendTranscription } from "../../services/transcriptionService";
import { Button } from "../Common/Button/Button";
import { Container } from "../Common/Container/Container";
import { ButtonsContainer } from "./styles";

interface ValidateProps {
  step: number;
  setStep: React.Dispatch<React.SetStateAction<number>>;
  drawObject: DrawObject;
  setDrawObject: React.Dispatch<React.SetStateAction<DrawObject>>;
}

export const Validate: React.FC<ValidateProps> = ({
  step,
  setStep,
  drawObject,
  setDrawObject,
}) => {
  const [isSending, setIsSending] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSendingAudioFile = () => {
    if (drawObject.audioBlob === null) {
      return;
    }

    setIsSending(true);
    sendAudioFile(drawObject.audioBlob)
      .then((result: any) => {
        setIsSending(false);

        if (result.transcription.text) {
          setDrawObject((prevState) => ({
            ...prevState,
            transcript: result.transcription.text,
          }));

          handleSendingTranscription(result.transcription.text);
        } else {
          setError("An error occured: No words detected.");
        }
      })
      .catch((error) => {
        setIsSending(false);
        setError("An error occured: " + error);
      });
  };

  const handleSendingTranscription = (transcript: string) => {
    setIsSending(true);

    sendTranscription(transcript)
      .then((result: any) => {
        setIsSending(false);

        if (result.result) {
          setDrawObject((prevState) => ({
            ...prevState,
            interpretation: result.result,
          }));
          setStep(3);
        } else {
          setError("An error occured: No words detected.");
        }
      })
      .catch((error) => {
        setIsSending(false);
        setError("An error occured: " + error);
      });
  };

  let content: React.ReactNode;

  if (isSending) {
    content = (
      <>
        <p>Sending audio...</p>
      </>
    );
  } else if (error) {
    content = (
      <>
        <p>{error}</p>
        <Button onClick={() => setStep(1)}>Try again</Button>
      </>
    );
  } else {
    content = (
      <>
        <p>Would you like to continue with this recording? </p>
        <ButtonsContainer>
          <Button onClick={() => setStep(0)} isSecondary>
            No, I want to start over
          </Button>
          <Button onClick={() => handleSendingAudioFile()}>
            Yes, validate
          </Button>
        </ButtonsContainer>
      </>
    );
  }

  return (
    <Container
      step={step}
      title="Confirm your request"
      subtitle="You can now listen to your recording to confirm that this is the correct request."
    >
      {drawObject.audioUrl && (
        <audio controls>
          <source src={drawObject.audioUrl} type="audio/webm" />
          Your browser does not support the audio element.
        </audio>
      )}
      {content}
    </Container>
  );
};
