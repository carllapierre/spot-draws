export const PermissionRequest: React.FC<{
  onRequestPermission: () => void;
}> = ({ onRequestPermission }) => (
  <>
    <p>Before we start, we need access to your microphone.</p>
    <p>Please click on the button below and accept permission.</p>
    <button onClick={onRequestPermission} type="button">
      Allow Microphone
    </button>
  </>
);
