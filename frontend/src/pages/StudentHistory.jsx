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

//log can be in json
//this will have menu item ID, hostelID, grams, nutritional information from api, placeholder data for now
const LOG = [
    {itemID: 1, name: "helmet the crab", hostelID: 1, grams: 100, date: "2026-10-21T15:00:00Z", protein: 12, fibre: 23 }
]



function StudentHistory(){

return (
    <Box className="student-hstoryi-page">
      <Box className="dashboard-header log-header">
    
         
          <Box>
            <Typography variant="h5">Meal History</Typography>
          </Box>
          </Box>
          </Box>);
}


export default StudentHistory;