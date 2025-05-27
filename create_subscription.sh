#!/bin/bash

curl -X POST http://orion:1026/v2/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Enviar atualizações da WeatherStation para o Cygnus",
    "subject": {
      "entities": [
        {
          "idPattern": ".*",
          "type": "WeatherStation"
        }
      ],
      "condition": {
        "attrs": ["temperature", "weathercode"]
      }
    },
    "notification": {
      "http": {
        "url": "http://cygnus:5050/notify"
      },
      "attrsFormat": "legacy"
    },
    "throttling": 1
  }'
