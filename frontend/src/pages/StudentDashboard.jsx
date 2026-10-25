import './dashboard.css';

import {Box,
  Button,
  ButtonGroup,
  Card,
  CardContent,
  Collapse,
  IconButton,
  InputAdornment,
  TextField,
  Typography,
  Drawer,
  Divider,
  Menu,
  MenuItem,
  Slider,
} from "@mui/material";

import SearchIcon from "@mui/icons-material/Search";
import CalendarMonthIcon from "@mui/icons-material/CalendarMonth";
import TuneIcon from "@mui/icons-material/Tune";
import CloseIcon from "@mui/icons-material/Close";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";


import { useNavigate } from 'react-router-dom';
import { useState } from 'react';

//food items and hostels all fetched by API

const MEALS = ['BREAKFAST', 'LUNCH', 'DINNER', 'SNACKS'];
const DEFAULT_KCAL = { BREAKFAST: 400, LUNCH: 600, DINNER: 500, SNACKS: 300 };
const MEAL_SCHEDULE = [{id: 'BREAKFAST', label: 'Breakfast', end: 10}, {id: 'LUNCH', label: 'Lunch', end: 14}, {id: 'SNACKS', label: 'Snacks', end: 18}, {id: 'DINNER', label: 'Dinner', end: 22}];
//const ratios = 

//const [calorieTarget, setCalorieTarget] = useState(2000);


function today(){
  return new Date().getDay();}//returns numbers 1 to 0, so we need to map these to monday, tuesday, etc

const WEEK_DAYS = [{id: 1, label: 'Monday'}, {id: 2, label: 'Tuesday'}, {id: 3, label: 'Wednesday'}, {id: 4, label: 'Thursday'}, {id: 5, label: 'Friday'}, {id: 6, label: 'Saturday'}, {id: 0, label: 'Sunday'}];

function whichMealByTime() {
  const h = new Date().getHours();
  if (h < 10) return 'BREAKFAST';
  if (h < 14) return 'LUNCH';
  if (h < 18) return 'SNACKS';
  return 'DINNER'; //what do we do 10 pm to midnight??
} //also we should disable meals that have already passed

function aggregation(){ //after getting from API we aggregate to find what to show on the hostel lsit

}
function StudentDashboard(){
  //same as guest dashboard but i need to add header now
  //id of student is stored in a state
  const navigate = useNavigate();
  const [profileMenuAnchor, setProfileMenuAnchor] = useState(null); //open or closed
  const profileMenuOpen = Boolean(profileMenuAnchor);

 //we can also use set in useState. so here we initialise it to empty state and then later as we expand or click on the expand button again we remove/add to set
  const hostel_list = [
    { id: 1, name: 'Hostel 1'},
    { id: 2, name: 'Hostel 2'},
    { id: 3, name: 'Hostel 3'},
  ];
  const [expandedHostelIds, setExpandedHostelIds] = useState(new Set());

  const [selectedMeal, setSelectedMeal] = useState(whichMealByTime); 
  const [selectedDay, setSelectedDay] = useState(today);
  const [showDays, setShowDays] = useState(false); //is calendar open or close
  const [filterOpen, setFilterOpen] = useState(false); //will open up the drawer
  const [searchQuery, setSearchQuery] = useState(''); //whenever even one character changes
  

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

  function closeProfileMenu() {
    setProfileMenuAnchor(null);
  }

  function handleLogout()
  {
    closeProfileMenu();
    navigate('/student-login');
  }

return (<Box className="dashboard-page">
  <Box className="dashboard-header">

      <Typography variant="h5">
        Flexi Mess
      </Typography>

      <IconButton
        id="profile-menu-button"
        onClick={(event) => setProfileMenuAnchor(event.currentTarget)}
      >
        <AccountCircleIcon />
      </IconButton>

      <Menu
        id="profile-menu"
        anchorEl={profileMenuAnchor}
        open={profileMenuOpen}
        onClose={closeProfileMenu}
      >

        <MenuItem onClick={() => navigate('/preferences')}>Edit preferences</MenuItem>
        
        <MenuItem onClick={() => navigate('/student-log')}> Log a meal </MenuItem>
        <MenuItem onClick={() => navigate('/student-history')}> See history </MenuItem>

        <MenuItem onClick={() => navigate('/student-login')}> Log out </MenuItem>
      </Menu>

    </Box>

    
      <TextField
        fullWidth
        placeholder="Search for a food item"
        value={searchQuery}
        onChange={(event) => setSearchQuery(event.target.value)}
        slotProps={{
          input: {
            endAdornment: (
              <InputAdornment position="end">
                <IconButton aria-label="Search food items" edge="end">
                  <SearchIcon />
                </IconButton>
              </InputAdornment>
            ),
          },
        }}
      />

 {/* we will highlight whichever one is chosen */}
      <Box id="whatmeal">


        <IconButton onClick={() => setShowDays((isVisible) => !isVisible)}>
          <CalendarMonthIcon />
        </IconButton>


        {showDays ? 
          (<ButtonGroup variant="outlined">

            {WEEK_DAYS.map((day) => {
              const dayPosition = day.id === 0 ? 6 : day.id - 1;
              const currentDayPosition = today() === 0 ? 6 : today() - 1; //ugh why are there no if else statements in react
              const hasPassed = dayPosition < currentDayPosition;
              const isSelected = selectedDay === day.id;

              return (
                <Button
                  key={day.id}
                  variant={isSelected ? 'contained' : 'outlined'}
                  disabled={hasPassed}
                  onClick={() => setSelectedDay(day.id)}>
                  {day.label}
                </Button>
              );
            })}
          </ButtonGroup>
        ) : null}

        <ButtonGroup variant="outlined"> 

          {MEAL_SCHEDULE.map((meal) => {
            {/*disabling is based on if end time has passed*/}

            const isToday = selectedDay === today();

            const hasPassed = isToday && currentHour >= meal.end;

            return (
              <Button
                key={meal.id}
                variant={selectedMeal === meal.id ? 'contained' : 'outlined'}
                disabled={hasPassed} 
                onClick={() => setSelectedMeal(meal.id)}
                aria-pressed={selectedMeal === meal.id}
              >
                {meal.label}
              </Button>
            );
          })}
          
        </ButtonGroup>

        <Button
          className="filter-trigger"
          variant="outlined"
          startIcon={<TuneIcon />}
          onClick={() => setFilterOpen(true)}>
          Sort & filter
        </Button>
      </Box>

      <Drawer
        anchor="right"
        open={filterOpen}
        onClose={() => setFilterOpen(false)}
      >
        <Box className="filter-drawer">
          <Box className="filter-drawer-header">
            <Typography variant="h6">Sort & filter</Typography>
            <IconButton onClick={() => setFilterOpen(false)}>
              <CloseIcon />
            </IconButton>
          </Box>
          <Divider />
          {/* maybe a for loop now for all the sorting and filtering criteria*/}
       
        </Box>
      </Drawer>

    <Box className="note">
    <Typography variant="body2">
   Dislaimer: This uses default meal portion ratios
    and a daily reference intake of 2000 kcal.
    Actual nutrition varies by serving size.
  </Typography>
</Box>
     {/* for hostels a for loop, and then we can expand also so that will need useState with parameter hostel id */}
      <Box id="hostel-list">
        {hostel_list.map((hostel) => {
          const hostelId = hostel.id;
          const hostelName = hostel.name;


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

export default StudentDashboard;