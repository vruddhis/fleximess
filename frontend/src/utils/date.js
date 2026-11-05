const IST_TIME_ZONE = "Asia/Kolkata";

function getISTParts(date = new Date()) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: IST_TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    hourCycle: "h23",
    weekday: "short",
  }).formatToParts(date).reduce((parts, part) => {
    parts[part.type] = part.value;
    return parts;
  }, {});
}

export function getISTDateKey(date = new Date()) {
  const parts = getISTParts(date);
  return `${parts.year}-${parts.month}-${parts.day}`;
}

export function getISTHour(date = new Date()) {
  return Number(getISTParts(date).hour);
}

export function getISTDay(date = new Date()) {
  const day = getISTParts(date).weekday;
  return ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].indexOf(day);
}

export function formatISTDate(date) {
  return new Intl.DateTimeFormat("en-IN", {
    timeZone: IST_TIME_ZONE,
    weekday: "long",
    month: "short",
    day: "numeric",
  }).format(date);
}

export { IST_TIME_ZONE };
