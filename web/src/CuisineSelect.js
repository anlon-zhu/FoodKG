import React from 'react';
import Autocomplete from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import { createTheme, ThemeProvider } from '@mui/material/styles';

const CuisineSelect = ({ cuisines, selectedCuisines, handleCuisineChange }) => {
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
            size="small"
            limitTags={10}
            id="tags-outlined"
            options={cuisines}
            value={selectedCuisines}
            onChange={handleCuisineChange}
            filterSelectedOptions
            openOnFocus={true} // Make the dropdown stay open
            renderInput={(params) => (
            <TextField
                {...params}
                label="Cuisines"
                placeholder="Select Cuisines"
            />
            )}
            isOptionEqualToValue={(option, value) => option.id === value.id}
        />
        </ThemeProvider>
    );
}

export default CuisineSelect;
