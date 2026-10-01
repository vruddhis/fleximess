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
const MEAL_SCHEDULE = [
  { id: 'BREAKFAST', label: 'Breakfast', end: 10 },
  { id: 'LUNCH', label: 'Lunch', end: 14 },
  { id: 'SNACKS', label: 'Snacks', end: 18 },
  { id: 'DINNER', label: 'Dinner', end: 24 },
];

function today(){
    const today = new Date();
    const offset = today.getDay();
    return offset;
} 


function whichMealByTime() {
  const h = new Date().getHours();
  if (h < 10) return 'BREAKFAST';
  if (h < 14) return 'LUNCH';
  if (h < 18) return 'SNACKS';
  return 'DINNER';
} //also we should disable meals that have already passed

function aggregation(){ //after getting from API we aggregate to find what to show on the hostel lsit

}
function GuestDashboard(){
 //we can also use set in useState. so here we initialise it to empty state and then later as we expand or click on the expand button again we remove/add to set
  const hostel_list = [1, 2, 3];
  const [expandedHostelIds, setExpandedHostelIds] = useState(new Set());
  const [selectedMeal, setSelectedMeal] = useState(whichMealByTime);
  const currentHour = new Date().getHours();

  //also from search bar whatever we search should weauto expand that hostel's menu and then highlight? or should we give results separately in popup. ig autoexpansion will be easier

  function toggleHostel(hostelId) {
    setExpandedHostelIds((currentIds) => {
      const nextIds = new Set(currentIds);

      if (nextIds.has(hostelId)) {
        nextIds.delete(hostelId);
      } else {
        nextIds.add(hostelId);
      }

      return nextIds;
    });
  }

return (<Box className="dashboard-page">

    
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
          
          <Button>Breakfast</Button>
          <Button>Lunch</Button>
          <Button>Snacks</Button>
          <Button>Dinner</Button>
          {/* also we can hide what is already done */}
        </ButtonGroup>

        {/* a popout (drawer) for all filters */}
      </Box>
      
     {/* for hostels a for loop, and then we can expand also so that will need useState with parameter hostel id */}
      <Box id="hostel-list">
        {hostel_list.map((hostelId) => {
          const hostelName = `Hostel ${hostelId}`;


          const isExpanded = expandedHostelIds.has(hostelId);

          return (
            <Card key={hostelId} className="hostel-card">
              <CardContent className="hostel-card-header"> {/* in this display horizontal, name and aggregation to left, and arrow icon on right */}
                <Box className="hostel-card-info">
                  <Typography variant="h6">
                    {hostelName}
                  </Typography>
                  <Typography variant="body2">
                    some aggregation
                  </Typography>
                </Box>

                <IconButton
                  className="hostel-expand-button"
                  onClick={() => toggleHostel(hostelId)}
                >
                  <ExpandMoreIcon/>
                </IconButton>
              </CardContent>

              <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                <CardContent>
                  <Typography>here will be menu</Typography>
                </CardContent>
              </Collapse>

            </Card>
          );
        })}
      </Box>

    </Box>);

}

export default GuestDashboard;