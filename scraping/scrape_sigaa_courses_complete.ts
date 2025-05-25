import { existsSync, mkdirSync, writeFileSync } from "fs";
import { chromium } from "playwright"; // or 'firefox' or 'webkit'

type ClassScheduleEntry = {
  day: string;
  startTime: string;
  endTime: string;
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

function mapToFiwareEntity(course: any) {
  return {
    id: `CourseInstance:UFRN:${course.courseCode}:${course.period}`,
    type: "CourseInstance",
    refOrganization: {
      value: "Organization-UFRN",
      type: "Relationship",
    },
    academicUnit: { type: "Text", value: course.academicUnit },
    courseCode: { type: "Text", value: course.courseCode },
    courseName: { type: "Text", value: course.courseName },
    courseLevel: { type: "Text", value: course.courseLevel },
    turmaId: { type: "Text", value: course.turmaId },
    period: { type: "Text", value: course.period },
    classGroup: { type: "Text", value: course.classGroup },
    instructor: { type: "Text", value: course.instructor },
    courseType: { type: "Text", value: course.type },
    modality: { type: "Text", value: course.modality },
    status: { type: "Text", value: course.status },
    scheduleText: { type: "Text", value: course.scheduleText },
    locationText: { type: "Text", value: course.location },
    content: { type: "Text", value: course.content },
    enrollments: { type: "Number", value: course.enrollments },
    capacity: { type: "Number", value: course.capacity },
  };
}

function expandFiwareClassPeriod(schedule: string) {
  const match = schedule.match(/\(([^)]+)\)/);
  if (!match) {
    return {
      classPeriod: {
        type: "StructuredValue",
        value: [],
      },
    };
  }
  const [_, dateRangeStr] = match;
  const [startStr, endStr] = dateRangeStr.split("-").map((s) => s.trim());
  const parseDate = (str: string) => {
    const [day, month, year] = str.split("/").map(Number);
    const date = new Date(year, month - 1, day);
    return date.toISOString().slice(0, 10); // "YYYY-MM-DD"
  };
  if (!startStr || !endStr) {
    return {
      classPeriod: {
        type: "StructuredValue",
        value: [],
      },
    };
  }
  return {
    classPeriod: {
      type: "StructuredValue",
      value: [
        {
          startDate: parseDate(startStr),
          endDate: parseDate(endStr),
        },
      ],
    },
  };
}

function expandFiwareSchedule(schedule: string) {
  if (!schedule) {
    return {
      classSchedule: {
        type: "StructuredValue",
        value: [],
      },
    };
  }
  const result: ClassScheduleEntry[] = [];
  // Remove date range if present
  const schedulePart = schedule.replace(/\(.*?\)/g, "").trim();
  // Split by spaces, filter out empty
  const blocks = schedulePart.split(/\s+/).filter(Boolean);

  for (const block of blocks) {
    // Match patterns like 7M2345 (day, period, times)
    const match = block.match(/^(\d)([MTN])([1-6]+)$/i);
    if (match) {
      const [, dayDigit, period, times] = match;
      // Group consecutive time digits
      const timeDigits = times.split("");
      const first = timeDigits[0];
      const last = timeDigits[timeDigits.length - 1];
      const keyStart = `${period.toUpperCase()}${first}`;
      const keyEnd = `${period.toUpperCase()}${last}`;
      if (scheduleTimes[keyStart] && scheduleTimes[keyEnd]) {
        result.push({
          day: dayMap[dayDigit] || "Unknown",
          startTime: scheduleTimes[keyStart].start,
          endTime: scheduleTimes[keyEnd].end,
        });
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

(async () => {
  if (
    !process.env.USERNAME ||
    !process.env.PASSWORD ||
    !process.env.MATRICULA
  ) {
    throw new Error(
      "Missing required environment variables: USERNAME, PASSWORD, or MATRICULA"
    );
  }

  // Launch browser (set headless: false to see browser UI)
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  // Go to a website
  await page.goto("https://sigaa.ufrn.br/sigaa/");

  // Fill the username input
  const username = process.env.USERNAME || "";
  await page.fill('input[name="username"]', username);

  const password = process.env.PASSWORD || "";
  await page.fill('input[name="password"]', password);

  const matricula = process.env.MATRICULA || "";

  await page.getByRole("button", { name: "Entrar" }).click();

  await page.getByRole("button", { name: "Ciente" }).click();

  if (page.url().includes("vinculos.jsf")) {
    // Wait for the table to be visible
    await page.waitForSelector("table.tabela-selecao-vinculo");
    // Find the link with the identifier and click it
    const vinculoLink = await page
      .locator("table.tabela-selecao-vinculo td a.withoutFormat", {
        hasText: matricula,
      })
      .first();
    await vinculoLink.click();
  }

  // Wait for the main menu to be visible
  await page.waitForSelector("span.ThemeOfficeMainFolderText", {
    state: "visible",
  });

  // Click the "Ensino" menu item
  await page
    .locator("span.ThemeOfficeMainFolderText", { hasText: "Ensino" })
    .click();

  // Wait for the menu to be visible in the DOM
  await page.waitForSelector("td.ThemeOfficeMenuFolderText", {
    state: "visible",
  });

  // Find and click the "Consultas Gerais" menu item
  await page
    .locator("td.ThemeOfficeMenuFolderText", { hasText: "Consultas Gerais" })
    .click();

  // Wait for the submenu to appear
  await page.waitForSelector("td.ThemeOfficeMenuItemText", {
    state: "visible",
  });

  // Click the "Consultar Turma" menu item
  await page
    .locator("td.ThemeOfficeMenuItemText", { hasText: "Consultar Turma" })
    .click();

  // Wait for the checkbox to be visible
  await page.waitForSelector("input#form\\:checkUnidade", { state: "visible" });

  // Select the option containing "TECNOLOGIA DA INFORMAÇÃO"
  const unidadeValue = await page.$eval(
    "select#form\\:selectUnidade",
    (select) => {
      const options = Array.from((select as HTMLSelectElement).options);
      const target = options.find((o) =>
        o.textContent?.includes("TECNOLOGIA DA INFORMAÇÃO")
      );
      // Save the textContent to a variable in the browser context
      (window as any).__unidadeOptionText = target?.textContent || "";
      return target?.value || "";
    }
  );
  await page.selectOption("select#form\\:selectUnidade", unidadeValue);

  // Click the checkbox
  await page.check("input#form\\:checkUnidade");

  await page.click("input#form\\:buttonBuscar");

  // Extract table as JSON
  const courses = await page.evaluate(scrapeCourseDetails());

  const finalCourses = courses.map((course) => ({
    ...mapToFiwareEntity(course),
    ...expandFiwareSchedule(course.scheduleText),
    ...expandFiwareClassPeriod(course.scheduleText),
  }));

  const outputDir = "outputs";
  if (!existsSync(outputDir)) {
    mkdirSync(outputDir);
  }
  for (const course of finalCourses) {
    const periodFilename = course.period.value
      .replace(/\./g, "-")
      .replace(/\s+/g, "-")
      .toLowerCase();
    const filename = `${outputDir}/course-instance-ufrn-${course.courseCode.value}-${periodFilename}.json`;
    // This will overwrite the file if it already exists
    writeFileSync(filename, JSON.stringify(course, null, 2), "utf-8");
  }

  console.log(JSON.stringify(finalCourses, null, 2));

  await page.pause();

  await browser.close();
})();

function scrapeCourseDetails() {
  return () => {
    const unidade = document.querySelector(
      "select#form\\:selectUnidade"
    ) as HTMLSelectElement | null;
    let unidadeName = "";
    if (unidade) {
      const selectedOption = unidade.options[unidade.selectedIndex];
      unidadeName = selectedOption
        ? selectedOption.textContent?.trim() || ""
        : "";
    }

    const rows = Array.from(
      document.querySelectorAll("#lista-turmas tbody tr")
    );
    const result: any[] = [];
    let currentCourse: { code: string; name: string; level: string } | null =
      null;

    for (const row of rows) {
      if (row.classList.contains("destaque")) {
        // Header row with course code and name
        const text = row.textContent?.trim() || "";
        const match = text.match(/^([A-Z0-9]+)\s*-\s*(.+?)\s*\((.+)\)/i);
        if (match) {
          currentCourse = {
            code: match[1],
            name: match[2].replace(/\s+$/, ""),
            level: match[3].replace(/\)/, ""),
          };
        }
      } else if (
        row.classList.contains("linhaPar") ||
        row.classList.contains("linhaImpar")
      ) {
        const cells = row.querySelectorAll("td");
        if (cells.length >= 11 && currentCourse) {
          // Extract turma id from onclick attribute
          const turmaLink = cells[1].querySelector("a");
          let turmaId = null;
          if (turmaLink && turmaLink.getAttribute("onclick")) {
            const onclick = turmaLink.getAttribute("onclick")!;
            const idMatch = onclick.match(/PainelTurma\.show\((\d+)\)/);
            if (idMatch) turmaId = idMatch[1];
          }
          // Extract enrollment/capacity
          const matCap = cells[9].textContent?.trim().match(/(\d+)\/(\d+)/);
          result.push({
            academicUnit: unidadeName,
            courseCode: currentCourse.code,
            courseName: currentCourse.name,
            courseLevel: currentCourse.level,
            turmaId,
            period: cells[0].textContent?.trim(),
            classGroup: turmaLink?.textContent?.trim(),
            instructor: cells[2].textContent?.trim(),
            type: cells[3].textContent?.trim(),
            modality: cells[4].textContent?.trim(),
            status: cells[5].textContent?.trim(),
            scheduleText: cells[6].textContent?.trim() || "",
            location: cells[7].textContent?.trim(),
            content: cells[8].textContent?.trim(),
            enrollments: matCap ? Number(matCap[1]) : null,
            capacity: matCap ? Number(matCap[2]) : null,
          });
        }
      }
    }
    return result;
  };
}
