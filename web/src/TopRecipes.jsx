import React, { useState } from "react";
import {
  Typography,
  IconButton,
  Collapse,
  List,
  ListItem,
  ListItemText,
  Box,
} from "@mui/material";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import CircleIcon from "@mui/icons-material/Circle";
import generateColorMap from "./colorMap";

function TopRecipes({ graphData }) {
  const [showDropdown, setShowDropdown] = useState(false);

  const toggleDropdown = () => {
    setShowDropdown(!showDropdown);
  };

  const getCuisineFlag = (recipe) => {
    // Map cuisine types to flag emojis
    const cuisineFlags = {
      italian: "🇮🇹",
      mexican: "🇲🇽",
      indian: "🇮🇳",
      chinese: "🇨🇳",
      japanese: "🇯🇵",
      thai: "🇹🇭",
      greek: "🇬🇷",
      french: "🇫🇷",
      spanish: "🇪🇸",
      german: "🇩🇪",
      american: "🇺🇸",
      british: "🇬🇧",
      irish: "🇮🇪",
      russian: "🇷🇺",
      brazilian: "🇧🇷",
      cuban: "🇨🇺",
      argentinian: "🇦🇷",
      peruvian: "🇵🇪",
      colombian: "🇨🇴",
      venezuelan: "🇻🇪",
      chilean: "🇨🇱",
      moroccan: "🇲🇦",
      egyptian: "🇪🇬",
      ethiopian: "🇪🇹",
      nigerian: "🇳🇬",
      kenyan: "🇰🇪",
      southafrican: "🇿🇦",
      australian: "🇦🇺",
      newzealand: "🇳🇿",
    };
    let cuisines = graphData.recipeNodes[recipe].cuisineType;

    for (let cuisine of cuisines) {
      if (cuisineFlags[cuisine]) {
        return cuisineFlags[cuisine];
      }
    }

    return "🏳️";
  };

  const recipeNodes = Object.values(graphData.recipeNodes);
  const colorMap = generateColorMap(recipeNodes);

  return (
    <Box
      sx={{
        border: "1px solid rgba(0, 0, 0, 0.87)",
        borderRadius: 4, // Adjust the border radius as needed
        position: "fixed",
        top: 145,
        right: 20,
        backgroundColor: colorMap(0),
        width: "20%",
        minWidth: 200,
        overflow: "hidden", // Ensure the border-radius doesn't cause peeking
      }}
    >
      <div
        onClick={toggleDropdown}
        style={{
          display: "flex",
          alignItems: "center",
          cursor: "pointer",
        }}
      >
        <Typography sx={{ ml: 2, flexGrow: 1, fontSize: 14 }}>
          Top Recipes
        </Typography>
        <IconButton size="small">
          {showDropdown ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </div>
      <Collapse in={showDropdown} sx={{ overflowY: "auto", maxHeight: 400 }}>
        <List sx={{ backgroundColor: "white", paddingY: 0 }}>
          {graphData.topRecipes.map((pair, index) => {
            const [recipe, score] = pair;
            return (
              <ListItem
                key={index}
                sx={{
                  display: "flex",
                  alignItems: "center",
                  paddingX: "1em",
                  "&:hover": { backgroundColor: "rgba(0, 0, 0, 0.1)" },
                  borderRadius: 0,
                }}
              >
                <CircleIcon
                  sx={{
                    color: colorMap(score),
                    mr: 2,
                    fontSize: 16,
                  }}
                />
                <ListItemText
                  primary={recipe}
                  secondary={`${score} ingredients`}
                  primaryTypographyProps={{
                    variant: "body2",
                    noWrap: true,
                    sx: { overflow: "hidden", textOverflow: "ellipsis" },
                  }}
                  secondaryTypographyProps={{
                    variant: "caption",
                    noWrap: true,
                    sx: { overflow: "hidden", textOverflow: "ellipsis" },
                  }}
                />
                <Typography sx={{ ml: 2, fontSize: 18 }}>
                  {getCuisineFlag(recipe)}
                </Typography>
              </ListItem>
            );
          })}
        </List>
      </Collapse>
    </Box>
  );
}

export default TopRecipes;
