import React from 'react';
import Autocomplete from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';

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
      
  return (
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
    />
  );
};

export default IngredientSelect;
