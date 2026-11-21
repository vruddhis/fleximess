import {Alert,
  Box,
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
} from "@mui/material";

import SearchIcon from "@mui/icons-material/Search";
import CalendarMonthIcon from "@mui/icons-material/CalendarMonth";
import TuneIcon from "@mui/icons-material/Tune";
import CloseIcon from "@mui/icons-material/Close";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";


import { useNavigate, useSearchParams } from 'react-router-dom';
import { useEffect, useMemo, useState } from 'react';
import { getISTDay, getISTHour, getISTDateKey, formatISTDate } from '../utils/date';
import { useAuth } from '../auth/authContext';
import { apiGet } from '../api';

//food items and hostels all fetched by API

const MEALS = ['BREAKFAST', 'LUNCH', 'DINNER', 'SNACKS'];
const DEFAULT_KCAL = { BREAKFAST: 400, LUNCH: 600, DINNER: 500, SNACKS: 300 };
const MEAL_SCHEDULE = [{id: 'breakfast', label: 'Breakfast', end: 10}, {id: 'lunch', label: 'Lunch', end: 14}, {id: 'snacks', label: 'Snacks', end: 18}, {id: 'dinner', label: 'Dinner', end: 22}]; //ids match the backend meal_type

const SORT_OPTIONS = ['High protein', 'High fiber', 'Low sugar', 'Low calorie'];
const NO_MENUS = []; //stable empty list while menus load



function today(){
  return getISTDay();}//returns numbers 1 to 0, so we need to map these to monday, tuesday, etc

const WEEK_DAYS = [{id: 1, label: 'Monday'}, {id: 2, label: 'Tuesday'}, {id: 3, label: 'Wednesday'}, {id: 4, label: 'Thursday'}, {id: 5, label: 'Friday'}, {id: 6, label: 'Saturday'}, {id: 0, label: 'Sunday'}];

function whichMealByTime() {
  const h = getISTHour();
  if (h < 10) return 'breakfast';
  if (h < 14) return 'lunch';
  if (h < 18) return 'snacks';
  return 'dinner'; //what do we do 10 pm to midnight??
}

//turns a weekday id (0 = Sunday ... 6 = Saturday) into the actual date (YYYY-MM-DD) in the current Monday-Sunday week, in IST
function dateForWeekday(dayId) {
  const [year, month, day] = getISTDateKey().split('-').map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  const todayPosition = today() === 0 ? 6 : today() - 1;
  const dayPosition = dayId === 0 ? 6 : dayId - 1;
  date.setUTCDate(date.getUTCDate() + dayPosition - todayPosition);
  return date.toISOString().slice(0, 10);
}

function formatDateKey(dateKey) {
  return formatISTDate(new Date(`${dateKey}T12:00:00+05:30`));
} //also we should disable meals that have already passed

function aggregation(){ //after getting from API we aggregate to find what to show on the hostel lsit

}
function StudentDashboard(){
  //same as guest dashboard but i need to add header now
  //id of student is stored in a state
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [profileMenuAnchor, setProfileMenuAnchor] = useState(null); //open or closed
  const profileMenuOpen = Boolean(profileMenuAnchor);

 //we can also use set in useState. so here we initialise it to empty state and then later as we expand or click on the expand button again we remove/add to set
  const [expandedHostelIds,  setExpandedHostelIds] = useState(new Set());

  const [selectedMeal, setSelectedMeal] = useState(whichMealByTime); 
  const [selectedDay, setSelectedDay] = useState(today);
  const [showDays, setShowDays] = useState(false); //is calendar open or close
  const [filterOpen,setFilterOpen] = useState(false); //will open up the drawer
  const [searchQuery, setSearchQuery] = useState(''); //whenever even one character changes
  const [sortPreferences, setSortPreferences] = useState([]);

  const [messes, setMesses] = useState([]); //from GET /api/messes
  const [messError, setMessError] = useState('');
  const [menuResult, setMenuResult] = useState({ key: null, menus: [], error: '' }); //from GET /api/menus
  const [foodResult, setFoodResult] = useState({ query: '', names: null }); //from GET /api/foods?q=

  //?date=YYYY-MM-DD in the URL overrides the weekday picker (useful for looking at older menus)
  const [searchParams, setSearchParams] = useSearchParams();
  const dateOverride = /^\d{4}-\d{2}-\d{2}$/.test(searchParams.get('date') || '') ? searchParams.get('date') : null;
  const selectedDate = dateOverride || dateForWeekday(selectedDay);
  const isToday = selectedDate === getISTDateKey();

  //derived from the latest finished request, so no extra state updates are needed
  const menuKey = `${selectedDate}|${selectedMeal}`;
  const loadingMenus = menuResult.key !== menuKey;
  const menus = loadingMenus ? NO_MENUS : menuResult.menus;
  const loadError = messError || (loadingMenus ? '' : menuResult.error);
  const trimmedQuery = searchQuery.trim();
  const matchedFoods = trimmedQuery.length >= 2 && foodResult.query === trimmedQuery ? foodResult.names : null; //null = not searching

  useEffect(() => {
    const controller = new AbortController();
    apiGet('/messes', {}, { signal: controller.signal })
      .then((data) => setMesses([...data].sort((a, b) => a.mess_name.localeCompare(b.mess_name, undefined, { numeric: true }))))
      .catch((error) => { if (error.name !== 'AbortError') setMessError(error.message); });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const [menuDate, mealType] = menuKey.split('|');
    apiGet('/menus', { menu_date: menuDate, meal_type: mealType }, { signal: controller.signal })
      .then((data) => setMenuResult({ key: menuKey, menus: data, error: '' }))
      .catch((error) => {
        if (error.name !== 'AbortError') setMenuResult({ key: menuKey, menus: [], error: error.message });
      });
    return () => controller.abort();
  }, [menuKey]);

  //food search uses the backend food search (GET /api/foods?q=), waits 300ms after typing stops
  useEffect(() => {
    if (trimmedQuery.length < 2) return undefined;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      apiGet('/foods', { q: trimmedQuery, limit: 500 }, { signal: controller.signal })
        .then((foods) => setFoodResult({ query: trimmedQuery, names: new Set(foods.map((food) => food.name.toLowerCase())) }))
        .catch((error) => { if (error.name !== 'AbortError') setMessError(error.message); });
    }, 300);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [trimmedQuery]);

  //one entry per mess: its menu items for the selected meal (filtered by the search, if any)
  const hostelList = useMemo(() => {
    const menuByMess = new Map(menus.map((menu) => [menu.mess_id, menu]));
    const list = messes.map((mess) => {
      const menu = menuByMess.get(mess.mess_id);
      const items = menu ? menu.items : [];
      const shownItems = matchedFoods ? items.filter((item) => matchedFoods.has(item.name.toLowerCase())) : items;
      return { id: mess.mess_id, name: mess.mess_name, hasMenu: Boolean(menu), totalItems: items.length, items: shownItems };
    });
    return matchedFoods ? list.filter((hostel) => hostel.items.length > 0) : list;
  }, [messes, menus, matchedFoods]);

  const selectedMealLabel = MEAL_SCHEDULE.find((meal) => meal.id === selectedMeal)?.label;

  const currentHour = getISTHour(); 

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

  function toggleSortPreference(option) {
    setSortPreferences((currentPreferences) => {
      if (currentPreferences.includes(option)) {
        return currentPreferences.filter((preference) => preference !== option);
      }

      return currentPreferences.length < 2
        ? [...currentPreferences, option]
        : currentPreferences;
    });
  }

  async function handleLogout() {
    closeProfileMenu();
    if (await logout()) {
      navigate('/student-login', { replace: true });
    }
  }

return (<Box className="dashboard-page">
  <Box className="dashboard-header">

      <Typography variant="h5">
        Flexi Mess
      </Typography>
      <Typography variant="body1">Welcome, {user.username}</Typography>

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
        
        <MenuItem onClick={() => navigate('/student-log')} > Log a meal </MenuItem>
        <MenuItem onClick={() => navigate('/student-history')}> See history </MenuItem>

        <MenuItem onClick={handleLogout}> Log out </MenuItem>
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
              const currentDayPosition= today() === 0 ? 6 : today() - 1; //ugh why are there no if else statements in react
              const hasPassed = dayPosition < currentDayPosition;
              const isSelected = selectedDay === day.id;

              return (
                <Button
                  key={day.id}
                  variant={isSelected ? 'contained' : 'outlined'}
                  disabled={hasPassed}
                  onClick={() => { setSelectedDay(day.id); if (dateOverride) setSearchParams({}); }}>
                  {day.label}
                </Button>
              );
            })}
          </ButtonGroup>
        ) : null}

        <ButtonGroup variant="outlined"> 

          {MEAL_SCHEDULE.map((meal) => {
            {/*disabling is based on if end time has passed (only matters for today)*/}
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

          <Typography variant="subtitle1" sx={{ mt: 2 }}>
            Sort priorities
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Select up to two, in priority order.
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mt: 2 }}>
            {SORT_OPTIONS.map((option) => {
              const preferenceIndex = sortPreferences.indexOf(option);

              return (
                <Button
                  key={option}
                  variant={preferenceIndex === -1 ? 'outlined' : 'contained'}
                  onClick={() => toggleSortPreference(option)}
                  disabled={preferenceIndex === -1 && sortPreferences.length === 2}
                >
                  {preferenceIndex === -1
                    ? option
                    : `${preferenceIndex + 1}. ${option}`}
                </Button>
              );
            })}
          </Box>

        </Box>
      </Drawer>
      
     {/* for hostels a for loop, and then we can expand also so that will need useState with parameter hostel id */}
      <Box id="hostel-list">
        <Typography variant="body2" color="text.secondary">
          {formatDateKey(selectedDate)} · {selectedMealLabel}
        </Typography>

        {loadError && <Alert severity="error">{loadError}</Alert>}

        {loadingMenus && <Typography variant="body2">Loading menus…</Typography>}

        {!loadingMenus && !loadError && menus.length === 0 && (
          <Alert severity="info">
            No menus available for {formatDateKey(selectedDate)} ({selectedMealLabel}).
          </Alert>
        )}

        {!loadingMenus && menus.length > 0 && matchedFoods && hostelList.length === 0 && (
          <Alert severity="info">No dishes matching "{trimmedQuery}" in this meal.</Alert>
        )}

        {!loadingMenus && menus.length > 0 && hostelList.map((hostel) => {
          const hostelId = hostel.id;
          const hostelName = hostel.name;

          //while searching, messes with a matching dish open automatically
          const isExpanded = expandedHostelIds.has(hostelId) || Boolean(matchedFoods);

          return (
            <Card key={hostelId} className="hostel-card">
              <CardContent className="hostel-card-header"> {/* in this display horizontal, name and aggregation to left, and arrow icon on right */}
                <Box  className="hostel-card-info">
                  <Typography variant="h6">
                    {hostelName}
                  </Typography>
                  <Typography variant="body2">
                    {!hostel.hasMenu
                      ? 'No menu available'
                      : matchedFoods
                        ? `${hostel.items.length} matching of ${hostel.totalItems} dishes`
                        : `${hostel.totalItems} dishes`}
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
                  {hostel.items.length === 0 && (
                    <Typography variant="body2" color="text.secondary">No menu available for this meal.</Typography>
                  )}
                  {hostel.items.map((item) => (
                    <Typography key={item.food_id}>
                      {item.name}
                      {item.serving_description ? ` (${item.serving_description})` : ''}
                    </Typography>
                  ))}
                </CardContent>
              </Collapse>

            </Card>
          );
        })}
      </Box>

    </Box>);

}

export default StudentDashboard;
