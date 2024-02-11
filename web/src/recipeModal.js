import { Modal, Box, Typography, List, ListItem, IconButton, Divider, Alert } from '@mui/material';
import { Close, Timer, Fastfood, Info } from '@mui/icons-material';

const RecipeModal = ({ open, handleClose, recipeNode }) => {
    const recipeInstructions = recipeNode.instructions ? recipeNode.instructions : [];

    const prettyTime = (time) => {
        let hours = Math.floor(time / 60);
        let minutes = time % 60;
        let timeString = '';

        if (hours > 0) {
            timeString += hours + ' hour' + (hours > 1 ? 's' : '');
        }

        if (minutes > 0) {
            if (timeString.length > 0) {
                timeString += ' & ';
            }
            timeString += minutes + ' minute' + (minutes > 1 ? 's' : '');
        }

        return timeString;
    }

    const makePrettyQuantity = (quantity) => {
        // Sometimes no quantity
        if (quantity === 0) {
            return '';
        }
        // If quantity is a whole number, return it as an integer
        if (quantity % 1 === 0) {
            return Number(quantity).toFixed(0);
        } else
        // Get closest fraction to the decimal
        {
            let closestFraction = { numerator: 0, denominator: 1 };
            for (let denominator = 1; denominator <= 64; denominator++) {
                let numerator = Math.round(quantity * denominator);
                if (Math.abs(quantity - numerator / denominator) < Math.abs(quantity - closestFraction.numerator / closestFraction.denominator)) {
                    closestFraction.numerator = numerator;
                    closestFraction.denominator = denominator;
                }
            }
            return (
            <>
            <sup>{closestFraction.numerator}</sup>&frasl;<sub>{closestFraction.denominator}</sub>
            </>);
        }
    }

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
                    height: '85%',
                    width: '75%',
                    bgcolor: '#FAF9F6',
                    boxShadow: 24,
                    p: 4,
                    borderRadius: 8,
                    overflow: 'auto',
                    display: 'flex',
                    flexDirection: 'column'
                }}
            >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="h5" id="modal-title" fontWeight={600} mb={2}>
                        {recipeNode.name}
                    </Typography>
                    <IconButton onClick={handleClose} size="small">
                        <Close />
                    </IconButton>
                </Box>
                <Box sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'space-between', mb: 2 }}>
                <Box mr={4} flexBasis="30%">
                {recipeNode.totalTime ? (
                            <Typography variant="body1" id="modal-description" fontStyle="italic">
                                <Timer sx={{ color: '#ff9800', fontSize: 20, verticalAlign: 'bottom', mr: 1 }} />
                                {prettyTime(recipeNode.totalTime)} to make
                            </Typography>
                        ) : null}
                <Box display='flex' height="100%" flexDirection="column" justifyContent='center' alignItems='center'>
                     {recipeNode.image && (
                            <img src={recipeNode.image} alt={recipeNode.name} style={{ width: '100%', border: '4px solid #ff9800', borderRadius: 4 }}
                            onError={(e) => {
                                e.target.src = '/placeholder.png';
                                e.target.style.border = 'none'; 
                            }}
                            />
                    )}
                    </Box>
                    </Box>
                    <Box flexBasis="70%" ml={4}>
                        {recipeNode.ingredients && recipeNode.ingredients.length > 0 ? (
                            <>
                                <Typography variant="body1" fontWeight={600}>
                                    <Fastfood sx={{ color: '#ff9800', fontSize: 20, verticalAlign: 'bottom', mr: 1 }} />
                                    Ingredients
                                </Typography>
                                <Box overflow="auto">
                                    <List sx={{ listStyleType: 'disc', pl: 6 }}>
                                        {recipeNode.ingredients.map((item, index) => (
                                            <ListItem key={index} sx={{ display: 'list-item', marginBottom: 1 }}>
                                                {makePrettyQuantity(item.relationship.quantity)} {item.relationship.measure} {item.ingredient.name}
                                            </ListItem>
                                        ))}
                                    </List>
                                </Box>
                            </>
                        ) : (
                            <Typography variant="body1" mb={2}>
                                No ingredients available.
                            </Typography>
                        )}
                    </Box>
                </Box>
                <Divider sx={{ my: 2 }} />
                {recipeInstructions && recipeInstructions.length > 0 ? (
                    <>
                        <Typography variant="body1" fontWeight={600} mb={1}>
                        <Info sx={{ color: '#ff9800', fontSize: 20, verticalAlign: 'bottom', mr: 1 }} />
                            Instructions
                        </Typography>
                        <List sx={{ listStyleType: 'decimal', pl: 6 }}>
                            {recipeInstructions.map((instruction, index) => (
                                <ListItem key={index} sx={{ display: 'list-item' }}>
                                    {instruction}
                                </ListItem>
                            ))}
                        </List>
                    </>
                ) : (
                    <Alert severity="warning" sx={{ mt: 2 }}>
                        No instructions available.
                    </Alert>
                )}
            </Box>
        </Modal>
    );
};

export default RecipeModal;
