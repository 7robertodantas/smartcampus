type ClassScheduleEntry = {
  day: string;
  startTime: string;
  endTime: string;
  startPeriod: string;
  endPeriod: string;
};

const scheduleTimes: Record<string, { start: string; end: string }> = {
  M1: { start: "07:00", end: "07:50" },
  M2: { start: "07:50", end: "08:40" },
  M3: { start: "08:55", end: "09:45" },
  M4: { start: "09:45", end: "10:35" },
  M5: { start: "10:50", end: "11:40" },
  M6: { start: "11:40", end: "12:30" },
  T1: { start: "13:00", end: "13:50" },
  T2: { start: "13:50", end: "14:40" },
  T3: { start: "14:55", end: "15:45" },
  T4: { start: "15:45", end: "16:35" },
  T5: { start: "16:50", end: "17:40" },
  T6: { start: "17:40", end: "18:30" },
  N1: { start: "18:45", end: "19:35" },
  N2: { start: "19:35", end: "20:25" },
  N3: { start: "20:35", end: "21:25" },
  N4: { start: "21:25", end: "22:15" },
};

const dayMap: Record<string, string> = {
  1: "Sunday",
  2: "Monday",
  3: "Tuesday",
  4: "Wednesday",
  5: "Thursday",
  6: "Friday",
  7: "Saturday",
};

export function expandFiwareClassPeriod(schedule: string) {
  if (!schedule) {
    return {
      classPeriod: {
        type: "StructuredValue",
        value: [],
      },
    };
  }

  const parseDate = (str: string) => {
    const [day, month, year] = str.split("/").map(Number);
    const date = new Date(year, month - 1, day);
    return date.toISOString().slice(0, 10); // "YYYY-MM-DD"
  };

  // Find all date ranges in the input string
  const matches = [...schedule.matchAll(/\(([^)]+)\)/g)];
  const periods = matches
    .map((m) => m[1])
    .map((dateRangeStr) => {
      const [startStr, endStr] = dateRangeStr.split("-").map((s) => s.trim());
      if (!startStr || !endStr) return null;
      return {
        startDate: parseDate(startStr),
        endDate: parseDate(endStr),
      };
    })
    .filter(Boolean);

  return {
    classPeriod: {
      type: "StructuredValue",
      value: periods,
    },
  };
}

export function expandFiwareSchedule(schedule: string) {
  if (!schedule) {
    return {
      classSchedule: {
        type: "StructuredValue",
        value: [],
      },
    };
  }

  const result: ClassScheduleEntry[] = [];

  // Split by comma to handle multiple periods
  const periods = schedule
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  for (const period of periods) {
    // Extract date range if present
    const match = period.match(/\(([^)]+)\)/);
    let startPeriod = "";
    let endPeriod = "";
    if (match) {
      const [startStr, endStr] = match[1].split("-").map((s) => s.trim());
      const parseDate = (str: string) => {
        const [day, month, year] = str.split("/").map(Number);
        const date = new Date(year, month - 1, day);
        return date.toISOString().slice(0, 10); // "YYYY-MM-DD"
      };
      if (startStr && endStr) {
        startPeriod = parseDate(startStr);
        endPeriod = parseDate(endStr);
      }
    }

    // Remove date range from period string
    const schedulePart = period.replace(/\(.*?\)/g, "").trim();
    // Split by spaces, filter out empty
    const blocks = schedulePart.split(/\s+/).filter(Boolean);

    for (const block of blocks) {
      // Match patterns like 7M2345 or 25M34 (multiple days)
      const matchBlock = block.match(/^(\d+)([MTN])([1-6]+)$/i);
      if (matchBlock) {
        const [, dayDigits, periodLetter, times] = matchBlock;
        // Group consecutive time digits
        const timeDigits = times.split("");
        const first = timeDigits[0];
        const last = timeDigits[timeDigits.length - 1];
        const keyStart = `${periodLetter.toUpperCase()}${first}`;
        const keyEnd = `${periodLetter.toUpperCase()}${last}`;
        for (const dayDigit of dayDigits.split("")) {
          if (scheduleTimes[keyStart] && scheduleTimes[keyEnd]) {
            result.push({
              day: dayMap[dayDigit] || "Unknown",
              startTime: scheduleTimes[keyStart].start,
              endTime: scheduleTimes[keyEnd].end,
              startPeriod,
              endPeriod,
            });
          }
        }
      }
    }
  }

  return {
    classSchedule: {
      type: "StructuredValue",
      value: result,
    },
  };
}
