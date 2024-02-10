import React from 'react';
import Autocomplete from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import { createTheme, ThemeProvider } from '@mui/material/styles';

const IngredientSelect = ({ ingredients, selectedIngredients, handleIngredientChange }) => {
    const options = ingredients.map((option) => {
        if (!option.category) {
          option.category = 'Other';
        }
        const category = option.category.toUpperCase();
        return {
            category: category,
          ...option,
        };
      });

  // Define custom theme
  const theme = createTheme({
      palette: {
          primary: {
              main: '#ff9800', // Change the main color to your desired color
          },
      },
  });
      
  return (
    <ThemeProvider theme={theme}>
    <Autocomplete
      multiple
      limitTags={10}
      id="tags-outlined"
      options={options.sort((a, b) => -b.category.localeCompare(a.category))}
      groupBy={(option) => option.category.toUpperCase()} // Group by ingredient category
      getOptionLabel={(option) => option.name}
      value={selectedIngredients}
      onChange={handleIngredientChange}
      filterSelectedOptions
      openOnFocus={true} // Make the dropdown stay open
      renderInput={(params) => (
        <TextField
          {...params}
          label="Ingredients"
          placeholder="Select Ingredients"
        />
      )}
      isOptionEqualToValue={(option, value) => option.id === value.id}
    />
    </ThemeProvider>
  );
};

export default IngredientSelect;
