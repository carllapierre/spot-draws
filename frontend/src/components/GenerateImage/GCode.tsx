import React, { useState } from "react";
import { evalImages } from "../../services/evaluatorService";
import { generateGCode } from "../../services/gcodeGenerationService";
import { commandSpotToDraw } from "../../services/spotAutomationService";
import { Button } from "../Common/Button/Button";

const SVGGCodeContainer: React.FC<{
  result: any;
  bestResult: any;
  idx: string;
}> = ({ result, bestResult, idx }) => {
  if (!result) {
    return null;
  }

  const isBest = bestResult === idx;

  return (
    <div style={{ display: "flex", flexDirection: "row", width: 800, gap: 15 }}>
      <div style={{ flex: 1 }}>
        <div className="container">
          <img
            src={`data:image/png;base64,${result.data.image}`}
            alt="Generated Image"
            style={{ width: "100%", height: "auto" }}
          />
        </div>
      </div>
      <div style={{ flex: 1 }}>
        <div className="container">
          <img
            src={`data:image/png;base64,${result.data.no_bg_image}`}
            alt="Generated Image"
            style={{ width: "100%", height: "auto" }}
          />
        </div>
      </div>
      <div style={{ flex: 1 }} className={isBest ? "is-best" : ""}>
        <div
          className={"container " + (isBest ? "is-best" : "")}
          dangerouslySetInnerHTML={{ __html: result.data.svg }}
        />
      </div>
      <div style={{ flex: 2 }} className={isBest ? "is-best" : ""}>
        <textarea
          value={result.data.gcode.join("\n")}
          style={{ height: "100%", width: "100%" }}
        />
      </div>
      <button onClick={() => commandSpotToDraw(result.data.gcode.join("\n"))}>
        Draw
      </button>
    </div>
  );
};

const GCode: React.FC<{ item: string | undefined }> = ({ item = "" }) => {
  const [input, setInput] = useState(item);
  const [loading, setLoading] = useState(false);

  const [result1, setResults1] = useState();
  const [result2, setResults2] = useState();
  const [result3, setResults3] = useState();
  const [result4, setResults4] = useState();

  const [bestResult, setBestResult] = useState();

  const handleGenerateGCode = async () => {
    setBestResult(undefined);
    setLoading(true);

    //reset results
    setResults1(undefined);
    setResults2(undefined);
    setResults3(undefined);
    setResults4(undefined);

    const promises = [
      generateGCode(input).then((results: any) => {
        setResults1(results);
        return results;
      }),
      generateGCode(input).then((results: any) => {
        setResults2(results);
        return results;
      }),
      generateGCode(input).then((results: any) => {
        setResults3(results);
        return results;
      }),
      generateGCode(input).then((results: any) => {
        setResults4(results);
        return results;
      }),
    ];

    const results = await Promise.all(promises);
    setLoading(false);
    await handleEvaluate(results);
  };

  const handleEvaluate = async (results: any) => {
    setLoading(true);

    const imagesToEval = results;
    const svgArray: string[] = [];

    // Type guard to check if result has data property
    const hasData = (result: any): result is { data: { image: string } } => {
      return (
        result &&
        typeof result === "object" &&
        "data" in result &&
        "image" in result.data
      );
    };

    for (let result of imagesToEval) {
      if (hasData(result)) {
        svgArray.push(result.data.svg);
      }
    }

    const imageArray = await processSvgsToBase64(svgArray, 1000, 1000);

    const res = await evalImages(imageArray, input);
    console.log("Evaluated Images", res.data.result);
    setBestResult(res.data.result);
    setLoading(false);
  };

  const svgToPngBase64 = (
    svgString: string,
    width: number,
    height: number
  ): Promise<string> => {
    return new Promise((resolve, reject) => {
      // Create an SVG element
      const svgBlob = new Blob([svgString], { type: "image/svg+xml" });
      const url = URL.createObjectURL(svgBlob);

      // Load SVG into an Image
      const img = new Image();
      img.onload = function () {
        // Create a canvas element
        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext("2d");

        if (!ctx) {
          reject(new Error("Could not get canvas context"));
          return;
        }

        // Draw a white background
        ctx.fillStyle = "white";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Draw the image onto the canvas
        ctx.drawImage(img, 0, 0, width, height);

        // Convert canvas to PNG
        const png = canvas.toDataURL("image/png");

        // Cleanup resources
        URL.revokeObjectURL(url);

        // Resolve with base64 PNG string
        resolve(png);
      };

      img.onerror = function () {
        reject(new Error("Failed to load SVG image"));
      };

      img.src = url;
    });
  };

  const processSvgsToBase64 = (
    svgArray: string[],
    width: number,
    height: number
  ): Promise<string[]> => {
    const promises = svgArray.map((svg) => svgToPngBase64(svg, width, height));
    return Promise.all(promises);
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "10px",
        margin: "auto",
      }}
    >
      <div>Enter an item to generate gcode</div>
      <input
        style={{
          padding: "10px",
          fontSize: "16px",
          borderRadius: "5px",
          border: "1px solid #ccc",
          background: "transparent",
          width: "100px",
          color: "black",
        }}
        type="text"
        placeholder="Item..."
        value={input}
        onChange={(e) => setInput(e.target.value)}
      />
      <Button onClick={handleGenerateGCode}>
        {loading ? "Loading..." : "Generate GCode"}
      </Button>
      <div
        style={{
          display: "flex",
          flexDirection: "row",
          gap: "10px",
          margin: "auto",
          maxWidth: "80%",
          flexWrap: "wrap",
        }}
      >
        <SVGGCodeContainer idx="1" result={result1} bestResult={bestResult} />
        <SVGGCodeContainer idx="2" result={result2} bestResult={bestResult} />
        <SVGGCodeContainer idx="3" result={result3} bestResult={bestResult} />
        <SVGGCodeContainer idx="4" result={result4} bestResult={bestResult} />
      </div>
    </div>
  );
};

export default GCode;
