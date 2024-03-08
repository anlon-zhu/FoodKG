import React, { useState, useEffect } from "react";
import CircularProgress from "@mui/material/CircularProgress";

const Loader = () => {
  const [loadingText, setLoadingText] = useState("spinning up application...");
  const loadingMessages = [
    "gathering ingredients...",
    "raiding pantry...",
    "browsing cookbooks...",
    "locating recipes...",
    "preheating oven...",
    "preparing mise en place...",
    "chopping veggies...",
    "stirring the pot...",
    "seasoning to taste...",
    "measuring spices...",
    "boiling water...",
    "sharpening knives...",
    "washing hands...",
    "measuring ingredients...",
    "checking expiration dates...",
    "checking grocery list...",
    "pouring a glass of wine...",
    "heating oil...",
    "grating cheese...",
    "picking fresh herbs...",
    "peeling garlic...",
    "brewing coffee...",
    "cleaning produce...",
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setLoadingText(
        loadingMessages[Math.floor(Math.random() * loadingMessages.length)]
      );
    }, 4000);

    return () => clearInterval(interval); // Cleanup interval on component unmount
  });

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
      }}
    >
      <CircularProgress size={20} style={{ marginRight: "1em" }} />
      <span style={{ fontSize: "15px" }}>{loadingText}</span>
    </div>
  );
};

export default Loader;
