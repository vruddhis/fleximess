import { useState } from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  MenuItem,
  TextField,
  Typography,
  IconButton,
} from "@mui/material";


import DeleteOutlinedIcon from "@mui/icons-material/DeleteOutlined";
import "./studentlog.css";
import { getISTDateKey } from "../utils/date";

const HOSTELS  = ["1", "2"]

//the api should fetch this after the person adds the date and meal. will add other fields like fiber later. 
const MENU_ITEMS = [ 
  { id: 1, name: "item 1", calories: 180, protein: 10, category: "Sabji" },
  { id: 2, name: "2", calories: 120, protein: 3, category: "Sabji" },
  { id: 3, name: "abc", calories: 110, protein: 7, category: "Dal" },
  { id: 4, name: "xyz", calories: 130, protein: 2.5, category: "Rice" },
];

const MEALS = ["BREAKFAST", "LUNCH", "SNACKS", "DINNER"];

function StudentLogMeal() {

  const [date, setDate] = useState(getISTDateKey());

  const [mess, setMess] = useState("");

  const [meal, setMeal] = useState("BREAKFAST"); 

  const [selectedFood, setSelectedFood] = useState("");
  const [quantity, setQuantity] = useState(100);
  const [loggedItems, setLoggedItems] = useState([]);
  const [saved, setSaved] = useState(false);

  //after clicking on the button everything that has been selected
  const addFood = () => {
    if (!selectedFood|| Number(quantity) == 0) return;

    const food = MENU_ITEMS.find(
      (item) => item.id === Number(selectedFood)
    );

    if (!food) return;

    setLoggedItems((previous) => [
      ...previous, //this means old values from array, and whatever after comma we are appending
      {
        ...food,
        logId: food.id,
        quantity: Number(quantity),
      },
    ]);

    setSelectedFood("");
    setQuantity(100);
    setSaved(false);
  };

  const removeFood = (logId) => {
    setLoggedItems((previous) =>
      previous.filter((item) => item.logId !== logId)
    );
    setSaved(false);
  };

  const totals = {
  calories: 0,
  protein: 0,
  weight: 0,
};

for (const item of loggedItems) {
  totals.calories += (item.calories * item.quantity) / 100;
  totals.protein += (item.protein * item.quantity) / 100;
  totals.weight += item.quantity;
}

  const saveMeal = () => {
    if (!date || !mess || !meal || loggedItems.length === 0) return;

   //api to backend

    const mealLog = {
      date,
      mess,
      meal,
      items: loggedItems,
    };

    void mealLog;
    setSaved(true);
  };

  return (
    <Box className="student-log-page">
      <Box className="dashboard-header  log-header">
        <Box>
         
          <Box>
            <Typography variant="h5">Log your Meals</Typography>
          </Box>
        </Box>
      </Box>

      <Box className="log-content">

        <Card  className="log-card"> {/* this is where we put in date and which meal*/}
          <CardContent>
            <Typography variant="h6">
              Meal details
            </Typography>

            <TextField className = "input-field"
              label="Date"
              type="date"
              fullWidth
              value={date}
              disabled={loggedItems.length > 0}
              onChange={(event) => {
                setDate(event.target.value);
                setSaved(false);
              }}
            />

            <TextField className = "input-field"
              select
              label="Hostel"
               fullWidth
              value={mess}
              disabled={loggedItems.length > 0}
              onChange={(event) => {
                setMess(event.target.value);
                setSaved(false);
              }}
            >
              {HOSTELS.map((name) => (
                <MenuItem key={name} value={name}>
                  {name}
                </MenuItem>
              ))}
            </TextField>

            <TextField className = "input-field"
              select
              label="Meal"
              fullWidth
              value={meal}
              disabled={loggedItems.length > 0}
              onChange={(event) => {
                setMeal(event.target.value);
                setSaved(false);
              }}
            >
              {MEALS.map((name) => (
                <MenuItem key={name} value={name}>
                  {name.charAt(0) + name.slice(1).toLowerCase()}
                </MenuItem>
              ))}
            </TextField>
          </CardContent>
        </Card>

        <Card className="log-card">
          <CardContent>
            <Typography variant="h6">
              Add food items
            </Typography>

            <TextField
              select
              label="Choose a dish"
              fullWidth
              value={selectedFood}
              onChange={(event) => setSelectedFood(event.target.value)}
            >
              {MENU_ITEMS.map((food) => (
                <MenuItem key={food.id}  value={food.id}>
                  {food.name} — {food.category}
                </MenuItem>
              ))}
            </TextField>

            <TextField
              label="Grams eaten"
              fullWidth
              value={quantity}
              onChange={(event) => setQuantity(event.target.value)}
            />

            <Button
              variant="contained"
              fullWidth
              onClick={addFood}
              
              disabled={
                !selectedFood ||
                Number(quantity) <= 0
              }
            >
              Add food
            </Button>
          </CardContent>
        </Card>

        <Card className="log-card">
          <CardContent>
            <Typography variant="h6">
              Your meal
            </Typography>

            {loggedItems.length=== 0 ? (
              <Typography>
                No food items added yet
              </Typography>
            ) : (
              <Box className="logged-food-list">
                {loggedItems.map((item) => (
                  <Box key={item.logId} className="logged-food">
                    <Box>
                      <Typography>
                        {item.name}
                      </Typography>
                      <Typography variant="body2">
                        {item.quantity} g ·{" "} {Math.round(item.calories * item.quantity / 100)} kcal
                      </Typography>
                    </Box>

                    <IconButton
                      onClick={() => removeFood(item.logId)}
                    >
                      <DeleteOutlinedIcon />
                    </IconButton>
                  </Box>
                ))}
              </Box>
            )}

            <Divider />

            <Box className="nutrition-totals">
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Total calories
                </Typography>
                <Typography variant="h5">
                  {Math.round(totals.calories)} kcal
                </Typography>
              </Box>

              <Box>
                <Typography variant="body2">
                  Total protein
                </Typography>
                <Typography variant="h5">
                  {totals.protein.toFixed(1)} g
                </Typography>
              </Box>

              <Box>
                <Typography variant="body2">
                  Total weight
                </Typography>
                <Typography variant="h5">
                  {totals.weight} g
                </Typography>
              </Box>
            </Box>

            <Button
              variant="contained"
              fullWidth


              disabled={!date || !mess || !meal || loggedItems.length === 0}
              onClick={saveMeal}
            >
              Save meal
            </Button>

            {saved && (
              <Typography>
                Meal saved successfully!
              </Typography>
            )}
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
}

export default StudentLogMeal;