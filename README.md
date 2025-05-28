# SmartCampus

**SmartCampus** is an open architecture designed to integrate educational environments into the broader ecosystem of smart cities. Built on **FIWARE components** and modern microservices, the system enables real-time data ingestion, processing, enrichment, and visualization through a modular, container-based infrastructure.

It empowers institutions with actionable insights in areas such as:

* **Service Demand Prediction** – Forecast peak usage periods (e.g., dining halls) using class schedule simulations.
* **Urban Mobility Analysis** – Monitor student density across time and space to inform transit and traffic planning.
* **Ride-Sharing Insights** – Predict demand for services like Uber or public transport by course cluster and schedule.
* **Public Resource Allocation** – Provide analytics to optimize campus staffing and service provisioning during peak times.

---

## Getting Started

To run the full environment locally, follow these steps:

### 1. Clone the Repository

```bash
git clone https://github.com/7robertodantas/smart-campus.git
cd smartcampus
```

### 2. Prerequisites

Make sure you have the following installed:

* [Docker](https://docs.docker.com/get-docker/)
* [Docker Compose](https://docs.docker.com/compose/)

### 3. Start the System

Spin up the core services:

```bash
docker-compose up --build
```

Then, run the custom sync service that transfers data from MongoDB to InfluxDB:

```bash
docker-compose run --rm mongo_to_influx
```

### 4. Accessing the Interfaces

* **Orion Context Broker**: [http://localhost:1026](http://localhost:1026)
* **Grafana Dashboards**: [http://localhost:3000](http://localhost:3000)
  Default credentials:

  ```
  Username: admin
  Password: admin
  ```

---

## Creating Initial Entities

To simulate real-world context, use the included script to create mock entities in Orion.

### Steps

1. Navigate to the appropriate folder:

   ```bash
   cd data/
   ```

2. Run the entity creation script:

   ```bash
   python create_entities.py
   ```

This script registers sample `WeatherStation` and `CourseInstance` entities using Orion's NGSI v2 API. Ensure that the Orion Broker is running before executing.

---

## Monitoring and Visualization

The system includes ready-to-use dashboards in Grafana at [http://localhost:3000](http://localhost:3000). Key panels include:

* **Realtime Weather Code** – Live weather updates per station
* **Course Summary** – Last 5 active course instances with enrollment info
* **Alerts by Course** – Panels that track course-specific weather severity
* **Enrollment History** – Historic trends per academic unit

---

## Useful Links

* [FIWARE Orion Docs](https://fiware-orion.readthedocs.io/en/latest/)
* [NGSI v2 Walkthrough](https://github.com/telefonicaid/fiware-orion/blob/master/doc/manuals/user/walkthrough_apiv2.md)
* [Orion Docker Setup](https://github.com/telefonicaid/fiware-orion/blob/master/docker/README.md)
* [Quick Start Guide](https://github.com/telefonicaid/fiware-orion/blob/master/doc/manuals/quick_start_guide.md)

---
