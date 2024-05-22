import { HeaderContainer, HeaderOsedeaLogo } from "./styles";

import OsedeaLightLogo from "../../assets/light-logo.png";
import { Branding } from "../Common/Branding/Branding";

interface HeaderProps {
  setStep: React.Dispatch<React.SetStateAction<number>>;
}

export const Header: React.FC<HeaderProps> = ({ setStep }) => {
  return (
    <HeaderContainer>
      <Branding setStep={setStep} />
      <HeaderOsedeaLogo src={OsedeaLightLogo} />
    </HeaderContainer>
  );
};
