import "dotenv/config";
import { existsSync, mkdirSync, writeFileSync } from "fs";
import { chromium, Page } from "playwright"; // or 'firefox' or 'webkit'
import {
  academicUnits,
  expandFiwareClassPeriod,
  expandFiwareSchedule,
  expandFiwareWorkload,
  expandInstructorsFiware,
  parseWorkload,
} from "./sigaa_parser";

function mapToFiwareEntity(course: any) {
  // Remove special characters from scheduleText (keep only letters, numbers, spaces, and common punctuation)
  const cleanedScheduleText = course.scheduleText
    ? course.scheduleText.replace(/[^\w\s.,:;-]/g, "")
    : "";

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
    courseType: { type: "Text", value: course.type },
    modality: { type: "Text", value: course.modality },
    status: { type: "Text", value: course.status },
    scheduleText: { type: "Text", value: cleanedScheduleText },
    locationText: { type: "Text", value: course.location },
    content: { type: "Text", value: course.content },
    enrollments: { type: "Number", value: course.enrollments },
    capacity: { type: "Number", value: course.capacity },
  };
}

(async () => {
  if (
    !process.env.SIGAA_USERNAME ||
    !process.env.SIGAA_PASSWORD ||
    !process.env.SIGAA_MATRICULA
  ) {
    throw new Error(
      "Missing required environment variables: SIGAA_USERNAME, SIGAA_PASSWORD, or SIGAA_MATRICULA"
    );
  }

  // Launch browser (set headless: false to see browser UI)
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  // Go to a website
  await page.goto("https://sigaa.ufrn.br/sigaa/");

  // Fill the username input
  const username = process.env.SIGAA_USERNAME || "";
  await page.fill('input[name="username"]', username);

  const password = process.env.SIGAA_PASSWORD || "";
  await page.fill('input[name="password"]', password);

  const matricula = process.env.SIGAA_MATRICULA || "";

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

  for (const academicUnit of Object.keys(academicUnits)) {
    await scrapeAcademicUnit(academicUnit, page);
  }

  await browser.close();
})();

async function scrapeAcademicUnit(academicUnitName: string, page: Page) {
  const academicUnit = academicUnits[academicUnitName];

  console.log(`Scraping academic unit: ${academicUnitName}`);

  const unidadeValue = await page.$eval(
    "select#form\\:selectUnidade",
    (select, academicUnitName) => {
      const options = Array.from((select as HTMLSelectElement).options);
      const target = options.find((o) =>
        o.textContent?.includes(academicUnitName)
      );
      console.log(`Selected option: ${target?.textContent}`);
      // Save the textContent to a variable in the browser context
      (window as any).__unidadeOptionText = target?.textContent || "";
      return target?.value || "";
    },
    academicUnitName // Pass as argument to the page function
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
    ...expandInstructorsFiware(course.instructor),
    ...expandFiwareWorkload(parseWorkload(course.instructor)),
    location: academicUnit.location,
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
    const filename = `${outputDir}/course-instance-ufrn-${academicUnit.shortName}-${course.courseCode.value}-${periodFilename}.json`;
    // This will overwrite the file if it already exists
    writeFileSync(filename, JSON.stringify(course, null, 2), "utf-8");
  }

  console.log(JSON.stringify(finalCourses));
}

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
          // Parse instructor and workload from instructor field
          let instructorRaw = cells[2].textContent?.trim() || "";

          result.push({
            academicUnit: unidadeName,
            courseCode: currentCourse.code,
            courseName: currentCourse.name,
            courseLevel: currentCourse.level,
            turmaId,
            period: cells[0].textContent?.trim(),
            classGroup: turmaLink?.textContent?.trim(),
            instructor: instructorRaw,
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
