import './dashboard.css';

import {Box,
  Button,
  ButtonGroup,
  Card,
  CardContent,
  Chip,
  Collapse,
  Divider,
  IconButton,
  InputAdornment,
  TextField,
  Typography,
  Drawer

} from "@mui/material";

import SearchIcon from "@mui/icons-material/Search";
import CalendarMonthIcon from "@mui/icons-material/CalendarMonth";

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";


import { Link } from 'react-router-dom';
import {useState} from 'react';

//food items and hostels all fetched by API

//drawer for filters
//const [filterOpen, setFilterOpen] = useState(false);

const MEALS = ['BREAKFAST', 'LUNCH', 'DINNER', 'SNACKS'];
const DEFAULT_KCAL = { BREAKFAST: 400, LUNCH: 600, DINNER: 500, SNACKS: 300 };

function today(){
    const today = new Date();
    const offset = today.getDay();
    return offset;
} 


function nextMealByTime() {
  const h = new Date().getHours();
  if (h < 10) return 'BREAKFAST';
  if (h < 14) return 'LUNCH';
  if (h < 18) return 'SNACKS';
  return 'DINNER';
} 

function aggregation(){ //after getting from API we aggregate to find what to show on the hostel lsit

}
function GuestDashboard(){
return (<Box sx={{ maxWidth: 1100, mx: "auto", p: 3 }}>

    
      <TextField
        fullWidth
        placeholder="Search for a food item"
      />

 {/* we will highlight whichever one is chosen */}
      <Box id="whatmeal">
        <IconButton>
  <CalendarMonthIcon />
</IconButton>
        <ButtonGroup variant="outlined"> 
          {/* maybe a calendar icon here for the week */}
          <Button>Breakfast</Button>
          <Button>Lunch</Button>
          <Button>Snacks</Button>
          <Button>Dinner</Button>
          {/* also we can hide what is already done */}
        </ButtonGroup>

        {/* a popout (drawer) for all filters */}
      </Box>

      {/* Hostel list */}
      <Box id="hostel-list">
  {/* for hostel in hostel_list (which we get from API) make the jsx*/}
       
      </Box>

    </Box>);

}

export default GuestDashboard;