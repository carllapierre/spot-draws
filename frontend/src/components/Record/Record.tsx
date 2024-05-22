import { useCallback, useEffect, useRef, useState } from "react";
import { DrawObject } from "../../models/DrawObject";
import { RecordingState } from "../../models/RecordingState";
import { RecordingStatus } from "../../models/RecordingStatus";
import { Container } from "../Common/Container/Container";
import { Loading } from "../Common/Loading/Loading";
import { PermissionRequest } from "../PermissionRequest/PermissionRequest";
import { RecordingControls } from "../RecordingControls/RecordingControls";

interface RecordProps {
  step: number;
  setStep: React.Dispatch<React.SetStateAction<number>>;
  setDrawObject: React.Dispatch<React.SetStateAction<DrawObject>>;
}

const mimeType = "audio/webm";

export const Record: React.FC<RecordProps> = ({
  step,
  setStep,
  setDrawObject,
}) => {
  /** State to check if the user has granted permission to access the microphone */
  const [permission, setPermission] = useState<boolean | undefined>(undefined);

  /** State to manage the recording process */
  const [recordingState, setRecordingState] = useState<RecordingState>({
    stream: null,
    status: RecordingStatus.INACTIVE,
    audioChunks: [],
    audioUrl: null,
    audioBlob: null,
  });

  /** Reference to the MediaRecorder instance */
  const mediaRecorder = useRef<MediaRecorder | null>(null);

  /** Request permission to access the microphone */
  const getMicrophonePermission = useCallback(async () => {
    if ("MediaRecorder" in window) {
      try {
        const streamData = await navigator.mediaDevices.getUserMedia({
          audio: true,
          video: false,
        });
        setPermission(true);
        setRecordingState((prevState) => ({
          ...prevState,
          stream: streamData,
        }));
      } catch (err: any) {
        alert(`Error accessing microphone: ${err.message}`);
      }
    } else {
      alert("The MediaRecorder API is not supported in your browser.");
    }
  }, []);

  useEffect(() => {
    getMicrophonePermission();
  }, []);

  /** Start recording audio */
  const startRecording = () => {
    const { stream } = recordingState;
    if (!stream) return;

    setRecordingState((prevState) => ({
      ...prevState,
      status: RecordingStatus.RECORDING,
      audioChunks: [],
    }));

    const media = new MediaRecorder(stream, { mimeType });
    mediaRecorder.current = media;
    mediaRecorder.current.start();

    let localAudioChunks: Blob[] = [];
    mediaRecorder.current.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        localAudioChunks.push(event.data);
      }
    };

    mediaRecorder.current.onstop = () => {
      const audioBlob = new Blob(localAudioChunks, { type: mimeType });
      const audioUrl = URL.createObjectURL(audioBlob);
      setDrawObject((prevState) => ({
        ...prevState,
        audioUrl,
        audioBlob,
        transcript: "",
      }));
      setStep(2);
    };
  };

  /** Stop recording audio */
  const stopRecording = () => {
    setRecordingState((prevState) => ({
      ...prevState,
      status: RecordingStatus.INACTIVE,
    }));
    if (mediaRecorder.current) {
      mediaRecorder.current.stop();
    }
  };

  let content: React.ReactNode = null;

  if (permission === undefined) {
    content = <Loading />;
  } else if (permission === false) {
    content = (
      <PermissionRequest onRequestPermission={getMicrophonePermission} />
    );
  } else if (permission) {
    content = (
      <RecordingControls
        recordingStatus={recordingState.status}
        onStart={startRecording}
        onStop={stopRecording}
      />
    );
  }

  return (
    <Container
      step={step}
      title="Record your ask"
      subtitle="Press the record button and ask spot to draw you an object. When finish recording, press stop."
    >
      {content}
    </Container>
  );
};
