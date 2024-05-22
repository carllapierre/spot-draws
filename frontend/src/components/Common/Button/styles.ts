import styled from "styled-components";

interface ButtonContainerProps {
  isSecondary?: boolean;
}
export const ButtonContainer = styled.div<ButtonContainerProps>`
  padding: 16px 28px;
  background: #7f56d9;
  width: fit-content;
  color: white;
  border-radius: 8px;
  box-shadow: 0px 1px 2px 0px rgba(16, 24, 40, 0.05);
  cursor: pointer;
  font-family: Inter;
  font-size: 16px;
  font-style: normal;
  font-weight: 600;
  line-height: 24px;

  &:hover {
    background: #2c1c5f;
  }

  ${({ isSecondary }) =>
    isSecondary &&
    `
  background: #E9D7FE;
  color: #42307D;
  border: 1px solid #6941C6;
  
  &:hover {
    background: #E9D7FE;
  }
`}
`;
