# SIGAA Scraping

This project scrapes course data from SIGAA.

## Setup

1. **Install dependencies:**
    ```bash
    npm install
    ```

2. **Create a `.env` file** in the root directory with the following variables:
    ```
    SIGAA_USERNAME=your_username
    SIGAA_PASSWORD=your_password
    SIGAA_MATRICULA=your_matricula
    ```

    **Example:**
    ```
    SIGAA_USERNAME=johndoe
    SIGAA_PASSWORD=supersecretpassword
    SIGAA_MATRICULA=202312345
    ```

## Running the Scraper

To execute `scrape_sigaa_courses_complete`, run:
```bash
npm run start
```

This will start the scraping process using the credentials provided in your `.env` file.

## Output

After running the scraper, the output files containing the course data will be generated in the `outputs` folder. Each file corresponds to a course instance and is saved in JSON format. You can find and use the scraped data in this directory.

### Sample Output

Below is an example of a generated output file:

```json
{
  "id": "CourseInstance:UFRN:PPGTI1004:2025.1",
  "type": "CourseInstance",
  "refOrganization": {
    "value": "Organization-UFRN",
    "type": "Relationship"
  },
  "academicUnit": {
    "type": "Text",
    "value": "PROGRAMA DE PÓS-GRADUAÇÃO EM TECNOLOGIA DA INFORMAÇÃO - NATAL - 11.00.05.02.03.06"
  },
  "courseCode": {
    "type": "Text",
    "value": "PPGTI1004"
  },
  "courseName": {
    "type": "Text",
    "value": "DESENVOLVIMENTO WEB 2"
  },
  "courseLevel": {
    "type": "Text",
    "value": "PÓS-GRADUAÇÃO"
  },
  "turmaId": {
    "type": "Text",
    "value": "57760365"
  },
  "period": {
    "type": "Text",
    "value": "2025.1"
  },
  "classGroup": {
    "type": "Text",
    "value": "Turma 01"
  },
  "instructor": {
    "type": "Text",
    "value": "JEAN MARIO MOREIRA DE LIMA (30h)"
  },
  "courseType": {
    "type": "Text",
    "value": "REGULAR"
  },
  "modality": {
    "type": "Text",
    "value": "Presencial"
  },
  "status": {
    "type": "Text",
    "value": "ABERTA"
  },
  "scheduleText": {
    "type": "Text",
    "value": "7T1234  6N1234 (09/05/2025 - 31/05/2025)"
  },
  "locationText": {
    "type": "Text",
    "value": "A304"
  },
  "content": {
    "type": "Text",
    "value": ""
  },
  "enrollments": {
    "type": "Number",
    "value": 25
  },
  "capacity": {
    "type": "Number",
    "value": 30
  },
  "classSchedule": {
    "type": "StructuredValue",
    "value": [
      {
        "day": "Saturday",
        "startTime": "13:00",
        "endTime": "16:35",
        "startPeriod": "2025-05-09",
        "endPeriod": "2025-05-31"
      },
      {
        "day": "Friday",
        "startTime": "18:45",
        "endTime": "22:15",
        "startPeriod": "2025-05-09",
        "endPeriod": "2025-05-31"
      }
    ]
  },
  "classPeriod": {
    "type": "StructuredValue",
    "value": [
      {
        "startDate": "2025-05-09",
        "endDate": "2025-05-31"
      }
    ]
  },
  "location": {
    "type": "geo:json",
    "value": {
      "coordinates": [
        -35.20545452790071,
        -5.832295943261201
      ],
      "type": "Point"
    }
  }
}
```

