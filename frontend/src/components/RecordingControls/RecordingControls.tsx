import { Button } from "../Common/Button/Button";

export const RecordingControls: React.FC<{
  recordingStatus: string;
  onStart: () => void;
  onStop: () => void;
}> = ({ recordingStatus, onStart, onStop }) => (
  <>
    {recordingStatus === "recording" ? (
      <>
        <Button onClick={onStop}>Stop</Button>
        <p>Listening...</p>
      </>
    ) : (
      <>
        <Button onClick={onStart}>Record</Button>
      </>
    )}
  </>
);
