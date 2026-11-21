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
import { useAuth } from "../auth/authContext";

const MEALS = ["Breakfast", "Lunch", "Snacks", "Dinner"];
const NUTRITION_PREFERENCES = [
  "High protein",
  "High fiber",
  "Low sugar",
  "Low carbohydrate",
];

function StudentPreferences() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const [profileMenuAnchor, setProfileMenuAnchor] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  const [saveError, setSaveError] = useState('');

  //keep as strings for now later in API we can conveert to numbers

  const [calorieTargets, setCalorieTargets] = useState({Breakfast: "", Lunch: "", Snacks: "", Dinner: ""});

  const [nutritionPreferences, setNutritionPreferences] = useState([]); //up to 2, can be 0

  const profileMenuOpen = Boolean(profileMenuAnchor);

  async function handleLogout() {
    setProfileMenuAnchor(null);
    if (await logout()) {
      navigate("/student-login", { replace: true });
    }
  }

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

  async function savePreferences() {
    setSaving(true);
    setSaveMessage('');
    setSaveError('');

    const payload = {
      username: user.username,
      nutrition_preferences: nutritionPreferences,
    };

    for (const [meal, field] of [
      ["Breakfast", "breakfast_calories"],
      ["Lunch", "lunch_calories"],
      ["Snacks", "snacks_calories"],
      ["Dinner", "dinner_calories"],
    ]) {
      if (calorieTargets[meal] !== '') {
        payload[field] = Number(calorieTargets[meal]);
      }
    }

    try {
      const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000")
        .replace(/\/+$/, "");
      const response = await fetch(`${apiBaseUrl}/api/preferences`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || `Request failed (${response.status})`);
      }

      setSaveMessage("Preferences saved.");
    } catch (error) {
      setSaveError(`Could not save preferences: ${error.message}`);
    } finally {
      setSaving(false);
    }
  }

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
          <MenuItem onClick={handleLogout}>
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

        {saveError && <Typography color="error" role="alert">{saveError}</Typography>}
        {saveMessage && <Typography role="status">{saveMessage}</Typography>}
        <Button
          className="preferences-save-button"
          variant="contained"
          onClick={savePreferences}
          disabled={saving}
        >
          Save preferences
        </Button>
      </Box>
    </Box>
  );
}

export default StudentPreferences;
