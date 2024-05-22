import { RecordingStatus } from "./RecordingStatus";

export interface RecordingState {
  stream: MediaStream | null;
  status: RecordingStatus;
  audioChunks: Blob[];
  audioUrl: string | null;
  audioBlob: Blob | null;
}
