
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
} from "@mui/material";

import SearchIcon from "@mui/icons-material/Search";
import CalendarMonthIcon from "@mui/icons-material/CalendarMonth";
import TuneIcon from "@mui/icons-material/Tune";
import CloseIcon from "@mui/icons-material/Close";

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";


import { Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { getISTDateKey, getISTDay, getISTHour } from '../utils/date';

const API_BASE_URL = (
  'http://localhost:8000'
);

const MEAL_SCHEDULE = [{id: 'BREAKFAST', label: 'Breakfast', end: 10}, {id: 'LUNCH', label: 'Lunch', end: 14}, {id: 'SNACKS', label: 'Snacks', end: 18}, {id: 'DINNER', label: 'Dinner', end: 22}];

const SORT_OPTIONS = ['High protein', 'High fiber', 'Low sugar', 'Low calorie'];


function today(){
  return getISTDay();}//returns numbers 1 to 0, so we need to map these to monday, tuesday, etc

const WEEK_DAYS = [{id: 1, label: 'Monday'}, {id: 2, label: 'Tuesday'}, {id: 3, label: 'Wednesday'}, {id: 4, label: 'Thursday'}, {id: 5, label: 'Friday'}, {id: 6, label: 'Saturday'}, {id: 0, label: 'Sunday'}];

function whichMealByTime() {
  const h = getISTHour();
  if (h < 10) return 'BREAKFAST';
  if (h < 14) return 'LUNCH';
  if (h < 18) return 'SNACKS';
  return 'DINNER'; //what do we do 10 pm to midnight??
} //also we should disable meals that have already passed

//this below function is not written by me
function getDateForWeekday(weekday) {
  const [year, month, day] = getISTDateKey().split('-').map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  const daysAhead = (weekday - getISTDay() + 7) % 7;
  date.setUTCDate(date.getUTCDate() + daysAhead);
  return date.toISOString().slice(0, 10);
}

function aggregateNutrition(items) {
  return items.reduce(
    (totals, item) => ({
      calories: totals.calories + item.calories,
      protein: totals.protein + item.protein,
      fiber: totals.fiber + item.fiber,
      sugar: totals.sugar + item.sugar,
    }),
    { calories: 0, protein: 0, fiber: 0, sugar: 0 },
  );
}

function getSortValue(totals, preference) {
  if (preference === 'High protein') return { value: totals.protein, direction: 'desc' };
  if (preference === 'High fiber') return { value: totals.fiber, direction: 'desc' };
  if (preference === 'Low sugar') return { value: totals.sugar, direction: 'asc' };
  if (preference === 'Low calorie') return { value: totals.calories, direction: 'asc' };
  return null;
}

async function getJson(path, signal) {
  const response = await fetch(`${API_BASE_URL}${path}`, { signal });
  const result = await response.json();

  if (!response.ok) {
    throw new Error(result.detail || `Request failed (${response.status})`);
  }

  return result;
}

function GuestDashboard() {
  const [hostelList, setHostelList] = useState([]);
  const [menusByHostel, setMenusByHostel] = useState({});
  const [menusLoadedFor, setMenusLoadedFor] = useState('');
  const [loadingHostels, setLoadingHostels] = useState(true);
  const [apiError, setApiError] = useState('');
  const [expandedHostelIds, setExpandedHostelIds] = useState(new Set());

  const [selectedMeal, setSelectedMeal] = useState(whichMealByTime); 
  const [selectedDay, setSelectedDay] = useState(today);
  const [showDays, setShowDays] = useState(false); //is calendar open or close
  const [filterOpen, setFilterOpen] = useState(false); //will open up the drawer
  const [searchQuery, setSearchQuery] = useState(''); //to type
  const [submittedSearchQuery, setSubmittedSearchQuery] = useState('');
  const [searchMatchedHostelIds, setSearchMatchedHostelIds] = useState(new Set());
  const [sortPreferences, setSortPreferences] = useState([]);
  

  const currentHour = getISTHour();

  const selectedDate = getDateForWeekday(selectedDay);
  const menuRequestKey = `${selectedDate}:${selectedMeal}:${hostelList.map((hostel) => hostel.id).join(',')}`;
  const loadingMenus = hostelList.length > 0 && menusLoadedFor !== menuRequestKey;

  useEffect(() => {
    const controller = new AbortController();

    getJson('/api/messes', controller.signal)
      .then((messes) => {
        setHostelList(messes.map((mess) => ({
          id: mess.mess_id,
          name: mess.mess_name,
        })));
        setApiError('');
      })
      .catch((error) => {
        if (error.name !== 'AbortError') {
          setApiError(`Could not load hostels: ${error.message}`);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoadingHostels(false);
      });

    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (hostelList.length === 0) return undefined;

    const controller = new AbortController();
    const mealMenus = Object.fromEntries(hostelList.map((hostel) => [hostel.id, []]));
    const query = new URLSearchParams({
      menu_date: selectedDate,
      meal_type: selectedMeal.toLowerCase(),
    });

    Promise.all(hostelList.map(async (hostel) => {
      const menus = await getJson(
        `/api/menus?${query}&mess_id=${hostel.id}`,
        controller.signal,
      );
      mealMenus[hostel.id] = menus.flatMap((menu) => menu.items);
    }))
      .then(() => {
        setMenusByHostel(mealMenus);
        setMenusLoadedFor(menuRequestKey);
        setApiError('');
      })
      .catch((error) => {
        if (error.name !== 'AbortError') {
          setMenusByHostel(Object.fromEntries(hostelList.map((hostel) => [hostel.id, []])));
          setMenusLoadedFor(menuRequestKey);
          setApiError(`Could not load menus: ${error.message}`);
        }
      });

    return () => controller.abort();
  }, [hostelList, menuRequestKey, selectedDate, selectedMeal]);

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

  function submitSearch() {
    const keyword = searchQuery.trim().toLowerCase();
    setSubmittedSearchQuery(keyword);

    if (!keyword) {
      setExpandedHostelIds((currentIds) => {
        const nextIds = new Set(currentIds);
        searchMatchedHostelIds.forEach((hostelId) => nextIds.delete(hostelId));
        return nextIds;
      });
      setSearchMatchedHostelIds(new Set());
      return;
    }

    if (menusLoadedFor !== menuRequestKey) return;

    const matchingHostelIds = hostelList
      .filter((hostel) => {
        const menuItems = menusByHostel[hostel.id] || [];
        return menuItems.some((item) =>
          item.food_item.toLowerCase().includes(keyword),
        );
      })
      .map((hostel) => hostel.id);

    setExpandedHostelIds((currentIds) => {
      const nextIds = new Set(currentIds);
      searchMatchedHostelIds.forEach((hostelId) => nextIds.delete(hostelId));
      matchingHostelIds.forEach((hostelId) => nextIds.add(hostelId));
      return nextIds;
    });
    setSearchMatchedHostelIds(new Set(matchingHostelIds));
  }

  const sortedHostels = [...hostelList].sort((leftHostel, rightHostel) => {
    for (const preference of sortPreferences) {
      const leftMenu = menusLoadedFor === menuRequestKey
        ? menusByHostel[leftHostel.id] || []
        : [];
      const rightMenu = menusLoadedFor === menuRequestKey
        ? menusByHostel[rightHostel.id] || []
        : [];
      const leftTotals = aggregateNutrition(leftMenu);
      const rightTotals = aggregateNutrition(rightMenu);
      const leftSort = getSortValue(leftTotals, preference);
      const rightSort = getSortValue(rightTotals, preference);

      if (!leftSort || !rightSort) continue;

      const difference = leftSort.direction === 'asc'
        ? leftSort.value - rightSort.value
        : rightSort.value - leftSort.value;

      if (difference !== 0) return difference;
    }

    return 0;
  });

return (<Box className="dashboard-page">
  <Box className="dashboard-header">

      <Typography variant="h5">
        Flexi Mess
      </Typography>

      <Button
        component={Link}
        to="/student-login"
        variant="outlined"
      >
        Login
      </Button>

    </Box>
    
      <TextField
        fullWidth
        placeholder="Search for a food item"
        value={searchQuery}
        onChange={(event) => {
          const nextQuery = event.target.value;
          setSearchQuery(nextQuery);

          if (!nextQuery.trim()) {
            setSubmittedSearchQuery('');
            setExpandedHostelIds((currentIds) => {
              const nextIds = new Set(currentIds);
              searchMatchedHostelIds.forEach((hostelId) => nextIds.delete(hostelId));
              return nextIds;
            });
            setSearchMatchedHostelIds(new Set());
          }
        }}
        onKeyDown={(event) => {
          if (event.key === 'Enter') submitSearch();
        }}
        slotProps={{
          input: {
            endAdornment: (
              <InputAdornment position="end">
                <IconButton edge="end" onClick={submitSearch}>
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
            const hasPassed = selectedDay === today() && currentHour >= meal.end;

            return (
              <Button
                key={meal.id}
                variant={selectedMeal === meal.id ? 'contained' : 'outlined'}
                disabled={hasPassed} 
                onClick={() => setSelectedMeal(meal.id)}
                
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
       {apiError && <Typography color="error" role="alert">{apiError}</Typography>}
       {loadingHostels && <Typography>Loading hostels…</Typography>}
       {sortedHostels.map((hostel) => {
         const hostelId = hostel.id;
         const hostelName = hostel.name;
         const menuItems = menusLoadedFor === menuRequestKey
           ? menusByHostel[hostelId] || []
           : [];
         const visibleItems = menuItems.filter((item) =>
           item.food_item.toLowerCase().includes(submittedSearchQuery),
         );
         const totals = aggregateNutrition(menuItems);


          const isExpanded = expandedHostelIds.has(hostelId);

          return (
            <Card key={hostelId} className="hostel-card">
              <CardContent className="hostel-card-header"> {/* in this display horizontal, name and aggregation to left, and arrow icon on right */}
                <Box className="hostel-card-info">
                  <Typography variant="h6">
                    {hostelName}
                  </Typography>
                  <Typography variant="body2">
                    {totals.calories} kcal · {totals.protein} g protein ·{' '}
                    {totals.fiber} g fiber · {totals.sugar} g sugar
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
                  {loadingMenus ? (
                    <Typography>Loading menu…</Typography>
                  ) : visibleItems.length > 0 ? (
                    visibleItems.map((item) => (
                      <Typography key={item.food_id}>
                        {item.food_item} — {item.calories} kcal ·{' '}
                        {item.protein} g protein · {item.fiber} g fiber ·{' '}
                        {item.sugar} g sugar
                      </Typography>
                    ))
                  ) : (
                    <Typography>
                      {submittedSearchQuery ? 'No matching dishes.' : 'No menu available.'}
                    </Typography>
                  )}
                </CardContent>
              </Collapse>

            </Card>
          );
        })}
      </Box>

    </Box>);

}

export default GuestDashboard;