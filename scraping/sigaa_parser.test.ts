import {
  expandFiwareClassPeriod,
  expandFiwareSchedule,
  parseInstructors,
  parseWorkload,
} from "./sigaa_parser";

describe("parseInstructors", () => {
  it("should parse multiple instructors separated by 'e' and remove workload", () => {
    const input =
      "ANTONIO BATISTA DA SILVA OLIVEIRA e MIGUEL EDUARDO MORENO ANEZ (15h)";
    expect(parseInstructors(input)).toEqual([
      "ANTONIO BATISTA DA SILVA OLIVEIRA",
      "MIGUEL EDUARDO MORENO ANEZ",
    ]);
  });

  it("should parse multiple instructors separated by 'e' and remove workload", () => {
    const input =
      "ANTONIO BATISTA DA SILVA OLIVEIRA (15h) e MIGUEL EDUARDO MORENO ANEZ";
    expect(parseInstructors(input)).toEqual([
      "ANTONIO BATISTA DA SILVA OLIVEIRA",
      "MIGUEL EDUARDO MORENO ANEZ",
    ]);
  });

  it("should parse single instructor and remove workload", () => {
    const input = "JANAYNNA DE MOURA FERRAZ (50h)";
    expect(parseInstructors(input)).toEqual(["JANAYNNA DE MOURA FERRAZ"]);
  });

  it("should parse single instructor without 'e' and remove workload", () => {
    const input = "GUSTAVO GIRAO BARRETO DA SILVA (30h)";
    expect(parseInstructors(input)).toEqual(["GUSTAVO GIRAO BARRETO DA SILVA"]);
  });
});

describe("parseWorkload", () => {
  it("should extract workload from string with hours", () => {
    expect(
      parseWorkload(
        "ANTONIO BATISTA DA SILVA OLIVEIRA e MIGUEL EDUARDO MORENO ANEZ (15h)"
      )
    ).toBe(15);
    expect(parseWorkload("JANAYNNA DE MOURA FERRAZ (50h)")).toBe(50);
    expect(parseWorkload("GUSTAVO GIRAO BARRETO DA SILVA (30h)")).toBe(30);
  });

  it("should return undefined if no workload present", () => {
    expect(parseWorkload("GUSTAVO GIRAO BARRETO DA SILVA")).toBeUndefined();
  });
});

describe("expandFiwareClassPeriod", () => {
  it("parses a single date range correctly", () => {
    const result = expandFiwareClassPeriod("6M456 (17/03/2025 - 27/03/2025)");
    expect(result).toEqual({
      classPeriod: {
        type: "StructuredValue",
        value: [
          {
            startDate: "2025-03-17",
            endDate: "2025-03-27",
          },
        ],
      },
    });
  });

  it("returns empty value for missing date range", () => {
    const result = expandFiwareClassPeriod("6M456");
    expect(result).toEqual({
      classPeriod: {
        type: "StructuredValue",
        value: [],
      },
    });
  });

  it("returns empty value for malformed date range", () => {
    const result = expandFiwareClassPeriod("6M456 (17/03/2025)");
    expect(result).toEqual({
      classPeriod: {
        type: "StructuredValue",
        value: [],
      },
    });
  });

  it("parses all date ranges if multiple are present", () => {
    const result = expandFiwareClassPeriod(
      "6M456 (17/03/2025 - 27/03/2025), 6M456 (31/03/2025 - 16/05/2025), 6M456 (26/05/2025 - 26/07/2025)"
    );
    expect(result).toEqual({
      classPeriod: {
        type: "StructuredValue",
        value: [
          {
            startDate: "2025-03-17",
            endDate: "2025-03-27",
          },
          {
            startDate: "2025-03-31",
            endDate: "2025-05-16",
          },
          {
            startDate: "2025-05-26",
            endDate: "2025-07-26",
          },
        ],
      },
    });
  });
});

describe("expandFiwareSchedule edge cases", () => {
  it("returns empty classSchedule for empty input", () => {
    const result = expandFiwareSchedule("");
    expect(result).toEqual({
      classSchedule: {
        type: "StructuredValue",
        value: [],
      },
    });
  });

  it("returns empty classSchedule for input with only spaces", () => {
    const result = expandFiwareSchedule("   ");
    expect(result).toEqual({
      classSchedule: {
        type: "StructuredValue",
        value: [],
      },
    });
  });

  it("ignores invalid schedule blocks", () => {
    const result = expandFiwareSchedule("invalid (01/01/2025 - 02/01/2025)");
    expect(result.classSchedule.value).toEqual([]);
  });

  it("handles missing date range gracefully", () => {
    const result = expandFiwareSchedule("7M2345 6T2345");
    expect(result.classSchedule.value.length).toBeGreaterThan(0);
    for (const entry of result.classSchedule.value) {
      expect(entry.startPeriod).toBe("");
      expect(entry.endPeriod).toBe("");
    }
  });

  it("handles malformed date range gracefully", () => {
    const result = expandFiwareSchedule("7M2345 6T2345 (09/05/2025)");
    expect(result.classSchedule.value.length).toBeGreaterThan(0);
    for (const entry of result.classSchedule.value) {
      expect(entry.startPeriod).toBe("");
      expect(entry.endPeriod).toBe("");
    }
  });

  it("handles unknown day digits", () => {
    const result = expandFiwareSchedule("9M12 (01/01/2025 - 02/01/2025)");
    expect(result.classSchedule.value[0].day).toBe("Unknown");
  });
});

describe("expandFiwareSchedule", () => {
  it("should parse all example schedules without error and return non empty classSchedule value", () => {
    const cases = [
      "7M2345 6T2345 (09/05/2025 - 31/05/2025)",
      "7T1234 6N1234 (09/05/2025 - 31/05/2025)",
      "3M3456 (22/06/2025 - 25/07/2025)",
      "5N1234 (24/04/2025 - 22/05/2025)",
      "2N1234 (22/06/2025 - 25/07/2025)",
      "25M34 (17/03/2025 - 26/07/2025)",
      "7T123456 (15/03/2025 - 15/03/2025), 7T123456 (29/03/2025 - 29/03/2025), 7T123456 (12/04/2025 - 12/04/2025), 7T123456 (26/04/2025 - 26/04/2025), 7T123456 (10/05/2025 - 10/05/2025), 7T123456 (24/05/2025 - 24/05/2025), 7T123456 (07/06/2025 - 07/06/2025), 7T123456 (14/06/2025 - 14/06/2025), 7T123456 (28/06/2025 - 28/06/2025)",
      "6T3456 6N12 (14/03/2025 - 14/03/2025), 6T3456 6N12 (28/03/2025 - 28/03/2025), 6T3456 6N12 (11/04/2025 - 11/04/2025), 6T3456 6N12 (25/04/2025 - 25/04/2025), 6T3456 6N12 (09/05/2025 - 09/05/2025), 6T3456 6N12 (23/05/2025 - 23/05/2025), 6T3456 6N12 (06/06/2025 - 06/06/2025), 6T3456 6N12 (13/06/2025 - 13/06/2025), 6T3456 6N12 (27/06/2025 - 27/06/2025)",
      "6M456 (17/03/2025 - 27/03/2025), 6M456 (31/03/2025 - 16/05/2025), 6M456 (26/05/2025 - 26/07/2025)",
    ];

    for (const input of cases) {
      const result = expandFiwareSchedule(input);
      expect(result).toHaveProperty("classSchedule");
      expect(result.classSchedule).toHaveProperty("type", "StructuredValue");
      expect(Array.isArray(result.classSchedule.value)).toBe(true);
      expect(result.classSchedule.value.length).toBeGreaterThan(0);
    }
  });

  it("parses 7M2345 6T2345 09052025 31052025 correctly", () => {
    const result = expandFiwareSchedule(
      "7M2345 6T2345 (09/05/2025 - 31/05/2025)"
    );
    expect(result.classSchedule.value).toEqual([
      {
        day: "Saturday",
        startTime: "07:50", // M2
        endTime: "11:40", // M5
        startPeriod: "2025-05-09",
        endPeriod: "2025-05-31",
      },
      {
        day: "Friday",
        startTime: "13:50", // T2
        endTime: "17:40", // T5
        startPeriod: "2025-05-09",
        endPeriod: "2025-05-31",
      },
    ]);
  });

  it("parses 7T1234 6N1234 09052025 31052025 correctly", () => {
    const result = expandFiwareSchedule(
      "7T1234 6N1234 (09/05/2025 - 31/05/2025)"
    );
    expect(result.classSchedule.value).toEqual([
      {
        day: "Saturday",
        startTime: "13:00", // T1
        endTime: "16:35", // T4
        startPeriod: "2025-05-09",
        endPeriod: "2025-05-31",
      },
      {
        day: "Friday",
        startTime: "18:45", // N1
        endTime: "22:15", // N4
        startPeriod: "2025-05-09",
        endPeriod: "2025-05-31",
      },
    ]);
  });

  it("parses 3M3456 22062025 25072025 correctly", () => {
    const result = expandFiwareSchedule("3M3456 (22/06/2025 - 25/07/2025)");
    expect(result.classSchedule.value).toEqual([
      {
        day: "Tuesday",
        startTime: "08:55", // M3
        endTime: "12:30", // M6
        startPeriod: "2025-06-22",
        endPeriod: "2025-07-25",
      },
    ]);
  });

  it("parses 5N1234 24042025 22052025 correctly", () => {
    const result = expandFiwareSchedule("5N1234 (24/04/2025 - 22/05/2025)");
    expect(result.classSchedule.value).toEqual([
      {
        day: "Thursday",
        startTime: "18:45", // N1
        endTime: "22:15", // N4
        startPeriod: "2025-04-24",
        endPeriod: "2025-05-22",
      },
    ]);
  });

  it("parses 2N1234 22062025 25072025 correctly", () => {
    const result = expandFiwareSchedule("2N1234 (22/06/2025 - 25/07/2025)");
    expect(result.classSchedule.value).toEqual([
      {
        day: "Monday",
        startTime: "18:45", // N1
        endTime: "22:15", // N4
        startPeriod: "2025-06-22",
        endPeriod: "2025-07-25",
      },
    ]);
  });

  it("parses 25M34 17032025 26072025 correctly", () => {
    const result = expandFiwareSchedule("25M34 (17/03/2025 - 26/07/2025)");
    expect(result.classSchedule.value).toEqual([
      {
        day: "Monday",
        startTime: "08:55", // M3
        endTime: "10:35", // M4
        startPeriod: "2025-03-17",
        endPeriod: "2025-07-26",
      },
      {
        day: "Thursday",
        startTime: "08:55", // M3
        endTime: "10:35", // M4
        startPeriod: "2025-03-17",
        endPeriod: "2025-07-26",
      },
    ]);
  });

  it("parses multiple blocks with same pattern correctly", () => {
    const input =
      "7T123456 (15/03/2025 - 15/03/2025), 7T123456 (29/03/2025 - 29/03/2025), 7T123456 (12/04/2025 - 12/04/2025), 7T123456 (26/04/2025 - 26/04/2025), 7T123456 (10/05/2025 - 10/05/2025), 7T123456 (24/05/2025 - 24/05/2025), 7T123456 (07/06/2025 - 07/06/2025), 7T123456 (14/06/2025 - 14/06/2025), 7T123456 (28/06/2025 - 28/06/2025)";
    const expected = [
      "2025-03-15",
      "2025-03-29",
      "2025-04-12",
      "2025-04-26",
      "2025-05-10",
      "2025-05-24",
      "2025-06-07",
      "2025-06-14",
      "2025-06-28",
    ].map((date) => ({
      day: "Saturday",
      startTime: "13:00", // T1
      endTime: "18:30", // T6
      startPeriod: date,
      endPeriod: date,
    }));
    const result = expandFiwareSchedule(input);
    expect(result.classSchedule.value).toEqual(expected);
  });

  it("parses multiple blocks with different patterns correctly", () => {
    const input =
      "6T3456 6N12 (14/03/2025 - 14/03/2025), 6T3456 6N12 (28/03/2025 - 28/03/2025), 6T3456 6N12 (11/04/2025 - 11/04/2025), 6T3456 6N12 (25/04/2025 - 25/04/2025), 6T3456 6N12 (09/05/2025 - 09/05/2025), 6T3456 6N12 (23/05/2025 - 23/05/2025), 6T3456 6N12 (06/06/2025 - 06/06/2025), 6T3456 6N12 (13/06/2025 - 13/06/2025), 6T3456 6N12 (27/06/2025 - 27/06/2025)";
    const dates = [
      "2025-03-14",
      "2025-03-28",
      "2025-04-11",
      "2025-04-25",
      "2025-05-09",
      "2025-05-23",
      "2025-06-06",
      "2025-06-13",
      "2025-06-27",
    ];
    const expected = dates.flatMap((date) => [
      {
        day: "Friday",
        startTime: "14:55", // T3
        endTime: "18:30", // T6
        startPeriod: date,
        endPeriod: date,
      },
      {
        day: "Friday",
        startTime: "18:45", // N1
        endTime: "20:25", // N2
        startPeriod: date,
        endPeriod: date,
      },
    ]);
    const result = expandFiwareSchedule(input);
    expect(result.classSchedule.value).toEqual(expected);
  });

  it("parses 6M456 17032025 27032025 31032025 16052025 26052025 26072025 correctly", () => {
    const input =
      "6M456 (17/03/2025 - 27/03/2025), 6M456 (31/03/2025 - 16/05/2025), 6M456 (26/05/2025 - 26/07/2025)";
    const expected = [
      {
        day: "Friday",
        startTime: "09:45", // M4
        endTime: "12:30", // M6
        startPeriod: "2025-03-17",
        endPeriod: "2025-03-27",
      },
      {
        day: "Friday",
        startTime: "09:45", // M4
        endTime: "12:30", // M6
        startPeriod: "2025-03-31",
        endPeriod: "2025-05-16",
      },
      {
        day: "Friday",
        startTime: "09:45", // M4
        endTime: "12:30", // M6
        startPeriod: "2025-05-26",
        endPeriod: "2025-07-26",
      },
    ];
    const result = expandFiwareSchedule(input);
    expect(result.classSchedule.value).toEqual(expected);
  });
});
