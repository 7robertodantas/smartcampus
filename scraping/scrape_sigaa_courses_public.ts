import { chromium } from "playwright"; // or 'firefox' or 'webkit'

(async () => {
  // Launch browser (set headless: false to see browser UI)
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  // Go to a website
  await page.goto("https://sigaa.ufrn.br/sigaa/public/turmas/listar.jsf");

  // Select the "STRICTO SENSU" option in the dropdown
  await page.selectOption("#formTurma\\:inputNivel", "S"); // STRICTO SENSU

  // Select "PROGRAMA DE PÓS-GRADUAÇÃO EM TECNOLOGIA DA INFORMAÇÃO - NATAL" by visible text
  await page.selectOption(
    "#formTurma\\:inputDepto",
    await page.$eval("#formTurma\\:inputDepto", (select) => {
      const options = Array.from((select as HTMLSelectElement).options);
      const target = options.find((o) =>
        o.textContent?.includes("TECNOLOGIA DA INFORMAÇÃO")
      );
      return target?.value || "";
    })
  );

  // Select "2025" in the "Ano" dropdown
  await page.fill("#formTurma\\:inputAno", "2025");

  // Select "1" in the "Periodo" dropdown
  await page.selectOption("#formTurma\\:inputPeriodo", "1");

  // Click the "Buscar" button by its value attribute
  await page.click('input[type="submit"][value="Buscar"]');

  // Wait for the table to be loaded
  await page.waitForSelector("table.listagem tr.agrupador");

  const courses = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll("table.listagem tr"));
    const courses: any[] = [];
    let currentCourse: any = null;

    for (const row of rows) {
      if (row.classList.contains("agrupador")) {
        // New course
        const a = row.querySelector("a");
        const span = a?.querySelector("span.tituloDisciplina");
        const onclick = a?.getAttribute("onclick") || "";
        const idMatch = onclick.match(/'id':'(\d+)'/);
        const [code, ...nameParts] = (span?.textContent || "").split(" - ");
        currentCourse = {
          id: idMatch ? idMatch[1] : null,
          code: code?.trim() || null,
          name: nameParts.join(" - ").trim() || null,
          classes: [],
        };
        courses.push(currentCourse);
      } else if (
        row.classList.contains("linhaPar") ||
        row.classList.contains("linhaImpar")
      ) {
        // Class info for the last course
        if (currentCourse) {
          const tds = row.querySelectorAll("td");
          currentCourse.classes.push({
            turma: tds[0]?.textContent?.trim() || null,
            anoPeriodo: tds[1]?.textContent?.trim() || null,
            docente: tds[2]?.textContent?.trim() || null,
            local: tds[3]?.textContent?.trim() || null,
          });
        }
      }
    }
    return courses;
  });

  // Extract course data from the table
  //   const courses = await page.$$eval("tr.agrupador", (rows) => {
  //     return rows.map((row) => {
  //       const a = row.querySelector("a");
  //       const span = a?.querySelector("span.tituloDisciplina");
  //       // Extract course id from onclick attribute
  //       const onclick = a?.getAttribute("onclick") || "";
  //       const idMatch = onclick.match(/'id':'(\d+)'/);
  //       return {
  //         id: idMatch ? idMatch[1] : null,
  //         code: span?.textContent?.split(" - ")[0].trim() || null,
  //         name: span?.textContent?.split(" - ")[1]?.trim() || null,
  //       };
  //     });
  //   });

  console.log(JSON.stringify(courses, null, 2));

  await page.pause();

  await browser.close();
})();
