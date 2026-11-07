import { useState } from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  IconButton,
  Menu,
  MenuItem,
  TextField,
  Typography,
} from "@mui/material";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import { useNavigate } from "react-router-dom";

const MEALS = ["Breakfast", "Lunch", "Snacks", "Dinner"];
const NUTRITION_PREFERENCES = [
  "High protein",
  "High fiber",
  "Low sugar",
  "Low carbohydrate",
];

function StudentPreferences() {
  const navigate = useNavigate();

  const [profileMenuAnchor, setProfileMenuAnchor] = useState(null);

  //keep as strings for now later in API we can conveert to numbers

  const [calorieTargets, setCalorieTargets] = useState({Breakfast: "", Lunch: "", Snacks: "", Dinner: ""});

  const [nutritionPreferences, setNutritionPreferences] = useState([]); //up to 2, can be 0

  const profileMenuOpen = Boolean(profileMenuAnchor);

  function toggleNutritionPreference(preference) {
    setNutritionPreferences((currentPreferences) => {
      if (currentPreferences.includes(preference)) {
        return currentPreferences.filter((item) => item !== preference);
      }

      return currentPreferences.length < 2 //for future scope maybe we can add more to this
        ? [...currentPreferences, preference]
        : currentPreferences;
    });
  }

  function savePreferences() {}

  return (
    <Box className="student-log-page">
      <Box className="dashboard-header log-header">
        <Typography variant="h5">Preferences</Typography>

        <IconButton
          id="profile-menu-button"
          aria-label="Open profile menu"
          onClick={(event) => setProfileMenuAnchor(event.currentTarget)}
        >
          <AccountCircleIcon />
        </IconButton>

        <Menu
          id="profile-menu"
          anchorEl={profileMenuAnchor}
          open={profileMenuOpen}
          onClose={() => setProfileMenuAnchor(null)}
        >
          <MenuItem onClick={() => navigate("/preferences")}>
            Edit preferences
          </MenuItem>
          <MenuItem onClick={() => navigate("/student-log")}>
            Log a meal
          </MenuItem>
          <MenuItem onClick={() => navigate("/student-history")}>
            See history
          </MenuItem>
          <MenuItem onClick={() => navigate("/student-login")}>
            Log out
          </MenuItem>
        </Menu>
      </Box>

      <Box className="preferences-content">
        <Card>
          <CardContent>
            <Typography variant="h6">
              Target calories per meal
            </Typography>

            <Box className="calorie-target-list">
              {MEALS.map((meal) => (
                <TextField
                  key={meal}
                  label={`${meal} calories`}
                  type="number"
                  fullWidth
                  value={calorieTargets[meal]}
                  onChange={(event) =>
                    setCalorieTargets((currentTargets) => ({
                      ...currentTargets,
                      [meal]: event.target.value,
                    }))
                  }
                />
              ))}
            </Box>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="h6">
              Nutrition preferences
            </Typography>
            <Typography variant="body2">
              Select up to two preferences in priority order
            </Typography>
            <Box className="nutrition-preference-list">

              {NUTRITION_PREFERENCES.map((preference) => {

                const preferenceIndex = nutritionPreferences.indexOf(preference);

                return (
                  <Button

                    key={preference}
                    variant={preferenceIndex === -1 ? "outlined" : "contained"}

                    disabled={
                      preferenceIndex === -1 &&
                      nutritionPreferences.length === 2
                    }

                    onClick={() => toggleNutritionPreference(preference)}
                    
                  >
                    {preferenceIndex === -1
                      ? preference
                      : `${preferenceIndex + 1}. ${preference}`}
                  </Button>
                );
              })}
            </Box>
          </CardContent>
        </Card>

        <Button
          className="preferences-save-button"
          variant="contained"
          onClick={savePreferences}
        >
          Save preferences
        </Button>
      </Box>
    </Box>
  );
}

export default StudentPreferences;
