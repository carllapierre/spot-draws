import styled from "styled-components";

export const LandingTitle = styled.h1`
  font-family: Inter;
  font-size: 72px;
  font-style: normal;
  font-weight: 700;
  line-height: normal;
  margin: 0;
`;

export const LandingSubtitle = styled.h3`
  font-family: Inter;
  font-size: 46px;
  font-style: normal;
  font-weight: 700;
  line-height: normal;
  margin: 0;
  margin-bottom: 32px;
`;

export const LandingContainer = styled.div`
  display: flex;
  flex-direction: row;
  gap: 40px;
  margin: auto;
  width: fit-content;
  height: 100vh;
`;

export const LandingSection = styled.div`
  flex: 3;
  height: fit-content;
  margin: auto 0;
`;

export const LandingLogo = styled.img`
  max-width: 300px;
  max-height: 300px;
  margin: auto 0;
`;
