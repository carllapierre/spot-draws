import SpotLogo from "../../../assets/dog.png";
import { BrandingContainer, BrandingLogo, BrandingName } from "./styles";

interface BrandingProps {
  setStep: React.Dispatch<React.SetStateAction<number>>;
}

export const Branding: React.FC<BrandingProps> = ({ setStep }) => {
  return (
    <BrandingContainer>
      <BrandingLogo src={SpotLogo} onClick={() => setStep(3)} />
      <BrandingName>Spot Draw</BrandingName>
    </BrandingContainer>
  );
};
