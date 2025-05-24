db = db.getSiblingDB("orion");

db.entities.createIndex(
  { "location.value": "2dsphere" },
  { name: "location_value_2dsphere" }
);
