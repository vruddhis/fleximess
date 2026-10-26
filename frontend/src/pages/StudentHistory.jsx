import { useState } from "react";

import {
  Box,
  Card,
  CardContent,
  Divider,
  Typography,
  IconButton,
  Collapse,
} from "@mui/material";

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { formatISTDate, getISTDateKey } from "../utils/date";

const LOG = [
  { itemID: 1, name: "helmet the crab", hostelID: 1, grams: 100, date: "2026-10-21", protein: 12, fibre: 23 },
  { itemID: 1, name: "vietnamese pho", hostelID: 2, grams: 300, date: "2026-10-21", protein: 32, fibre: 2 },
];

function getPastDates() {
  const dates = [];
  const today = new Date(`${getISTDateKey()}T00:00:00Z`);

  for (let daysAgo = 0; daysAgo < 30; daysAgo += 1) {
    const date = new Date(today);
    date.setUTCDate(today.getUTCDate() - daysAgo);
    dates.push({
      key: getISTDateKey(date),
      label: formatISTDate(date),
    });
  }

  return dates;
}

function StudentHistory() {
  const [expandedDates, setExpandedDates] = useState(new Set());
  const dates = getPastDates();

  function toggleDate(dateKey) {
    setExpandedDates((currentDates) => {
      const nextDates = new Set(currentDates);

      if (nextDates.has(dateKey)) {
        nextDates.delete(dateKey);
      } else {
        nextDates.add(dateKey);
      }

      return nextDates;
    });
  }

  return (
    <Box className="student-log-page">
      <Box className="dashboard-header log-header">
        <Typography variant="h5">Meal History</Typography>
      </Box>

      <Box id="hostel-list">
        {dates.map((date) => {
          const dayLogs = LOG.filter((item) => item.date.slice(0, 10) === date.key);
          const totals = {
            grams: 0,
            protein: 0,
            fibre: 0,
          };

          for (const item of dayLogs) {
            totals.grams += item.grams;
            totals.protein += item.protein;
            totals.fibre += item.fibre;
          }

          const isExpanded = expandedDates.has(date.key);

          //return inside the for loop only
          return ( 
            <Card key={date.key} className="hostel-card">
              <CardContent className="hostel-card-header">
                <Box className="hostel-card-info">
                  <Typography variant="h6">{date.label}</Typography>
                  {dayLogs.length === 0 ? (
                    <Typography>
                      No data available
                    </Typography>
                  ) : (
                    <Typography>
                      {dayLogs.length} dish{dayLogs.length === 1 ? "" : "es"} ·{" "}
                      {totals.grams} g · {totals.protein} g protein ·{" "}
                      {totals.fibre} g fibre
                    </Typography>
                  )}
                </Box>

                {dayLogs.length > 0 && (
                  <IconButton
                    className="hostel-expand-button"
                    onClick={() => toggleDate(date.key)}
                  >
                    <ExpandMoreIcon/>
                  </IconButton>
                )}
              </CardContent>

              <Collapse in={isExpanded}>
                <CardContent>
                  {dayLogs.map((item) => (
                    <Box key={item.itemID}>
                      <Typography>{item.name}</Typography>
                      <Typography variant="body2">
                        {item.grams} g · {item.protein} g protein · {item.fibre} g fibre
                      </Typography>
                      <Divider />
                    </Box>
                  ))}
                </CardContent>
              </Collapse>
            </Card>
          );
        })}
      </Box>
    </Box>
  );
}


export default StudentHistory;