import React from 'react';
import Autocomplete from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import Loader from './IngredientLoad';

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
      loading
      loadingText={<Loader loaded={ingredients.length > 0}/>}
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
  );
};

export default IngredientSelect;
