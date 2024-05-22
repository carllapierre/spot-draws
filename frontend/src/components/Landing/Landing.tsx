import { Button } from "../Common/Button/Button";
import {
  LandingContainer,
  LandingLogo,
  LandingSection,
  LandingSubtitle,
  LandingTitle,
} from "./styles";

import SpotLogo from "../../assets/dog.png";

interface LandingProps {
  setStep: React.Dispatch<React.SetStateAction<number>>;
}

export const Landing: React.FC<LandingProps> = ({ setStep }) => {
  return (
    <LandingContainer>
      <LandingLogo src={SpotLogo} />
      <LandingSection>
        <LandingTitle>Welcome to</LandingTitle>
        <LandingSubtitle>Spot Draw</LandingSubtitle>
        <Button onClick={() => setStep(1)}>Start</Button>
      </LandingSection>
    </LandingContainer>
  );
};
