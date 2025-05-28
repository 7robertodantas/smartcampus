# Smart Campus

## Overview

Smart Campus is a project designed to integrate educational institutions to smart cities context. It leverages FIWARE components to enable real-time data collection, processing, and visualization.

Smart Campus can provide valuable insights and applications in various scenarios:

- **Service Demand Prediction**: Based on class schedules, the system can predict peak times for services like dining facilities, especially during lunch hours.
- **Urban Mobility Analysis**: High concentrations of students in specific areas during certain times can impact urban mobility, influencing traffic and public transportation planning.
- **Ride-Sharing Insights**: The system can analyze and predict ride-sharing demand (e.g., Uber) for specific regions and times.
- **Public Administration Support**: Insights from the system can help allocate additional staff or resources to the institution during peak hours, improving operational efficiency.

## Getting Started

To get started with Smart Campus, follow these steps:

1. Clone the repository:
    ```bash
    git clone https://github.com/7robertodantas/smart-campus.git
    cd smart-campus
    ```

2. Set up the required environment:
    - Install Docker and Docker Compose.

3. Start the services:
    ```bash
    docker-compose up --build
    ```
    ```bash
    docker-compose run --rm mongo_to_influx
    ```

4. Access the application at `http://orion:1026`.

## Creating entities

To create entities in the Smart Campus project, you can use the `data/create_entities.py` script. This script interacts with the FIWARE Orion Context Broker to register entities.

#### Steps to Create Entities

1. Run the `create_entities.py` script:
    ```bash
    python create_entities.py
    ```

2. The script will send HTTP POST requests to the Orion Context Broker to create predefined entities. Ensure the broker is running and accessible at `http://orion:1026`.


## Useful Links

- https://fiware-orion.readthedocs.io/en/latest/index.html
- https://github.com/telefonicaid/fiware-orion/blob/master/doc/manuals/user/walkthrough_apiv2.md
- https://github.com/telefonicaid/fiware-orion/blob/master/docker/README.md
- https://github.com/telefonicaid/fiware-orion/blob/master/doc/manuals/quick_start_guide.md
