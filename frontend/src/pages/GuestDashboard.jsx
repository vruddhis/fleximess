import './dashboard.css';

import { Link } from 'react-router-dom';
import {useState} from 'react';

//food items and hostels all fetched by API

const MEALS = ['BREAKFAST', 'LUNCH', 'DINNER', 'SNACKS'];
const DEFAULT_KCAL = { BREAKFAST: 400, LUNCH: 600, DINNER: 500, SNACKS: 300 };

function today(){
    const today = new Date();
    const offset = today.getDay() % 7;
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
return ()

}

export default GuestDashboard;