import React from "react";
import { ButtonContainer } from "./styles";

interface ButtonProps {
  onClick: () => void;
  children: React.ReactNode;
  isSecondary?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  isSecondary,
}) => {
  return (
    <ButtonContainer onClick={onClick} isSecondary={isSecondary}>
      {children}
    </ButtonContainer>
  );
};
