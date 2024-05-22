import {
  ContainerStep,
  ContainerStyle,
  ContainerSubtitle,
  ContainerTitle,
} from "./styles";

interface ContainerProps {
  children: React.ReactNode;
  step: number;
  title: string;
  subtitle: string;
}

export const Container: React.FC<ContainerProps> = ({
  children,
  step,
  title,
  subtitle,
}) => {
  return (
    <ContainerStyle>
      <ContainerStep>Step {step} of 3</ContainerStep>
      <ContainerTitle>{title}</ContainerTitle>
      <ContainerSubtitle>{subtitle}</ContainerSubtitle>
      {children}
    </ContainerStyle>
  );
};
