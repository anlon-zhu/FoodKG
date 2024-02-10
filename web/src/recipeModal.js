import { Modal, Box, Typography, List, IconButton } from '@mui/material';
import { Close } from '@mui/icons-material';

const RecipeModal = ({ open, handleClose, recipeNode }) => {
    const recipeInstructions = recipeNode.instructions ? recipeNode.instructions : [];

    return (
        <Modal
            open={open}
            onClose={handleClose}
            aria-labelledby="modal-title"
            aria-describedby="modal-description"
        >
            <Box
                sx={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    height: '80%',
                    bgcolor: 'white',
                    boxShadow: 24,
                    p: 4,
                    borderRadius: 4,
                    overflow: 'auto',
                }}
            >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="h6" id="modal-title" fontWeight={600}>
                        {recipeNode.name} {recipeNode.recipeTime ? ' | ' + recipeNode.recipeTime + ' minutes' : ''}
                    </Typography>
                    <IconButton onClick={handleClose} size="small">
                        <Close />
                    </IconButton>
                </Box>

                {recipeNode.image && (
                            <Box mb={2}>
                                <img src={recipeNode.image} alt={recipeNode.name} style={{ width: '50%', border: '1px solid #ccc', borderRadius: '4px' }} />
                            </Box>
                        )}
                {recipeNode.ingredients && 
                    recipeNode.ingredients.length > 0 ?
                    <>
                        <Typography variant="body1" id="modal-description" fontWeight={600}>
                            Ingredients:
                        </Typography>
                        <List>
                            {recipeNode.ingredients.map((ingredient, index) => (
                                <Typography key={index} variant="body1">
                                    {ingredient.name}
                                </Typography>
                            ))}
                        </List>
                    </>
                    :
                    <Typography variant="body1" id="modal-description">
                        No ingredients available.
                    </Typography>
                }

                {recipeInstructions && recipeInstructions.length > 0 ?
                    <>
                        <Typography variant="body1" id="modal-description" fontWeight={600}>
                            Instructions:
                        </Typography>
                        <List>
                            {recipeNode.instructions.map((instruction, index) => (
                                <Typography key={index} variant="body1">
                                    {index + 1}. {instruction}
                                </Typography>
                            ))}
                        </List>
                    </>
                    :
                    <Typography variant="body1" id="modal-description">
                        No instructions available.
                    </Typography>
                }
            </Box>
        </Modal>
    );
};

export default RecipeModal;
