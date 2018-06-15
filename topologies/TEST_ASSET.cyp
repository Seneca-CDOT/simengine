
match (out6:Outlet {key: 20134})

CREATE (microwave:Asset:StaticAsset {
  type: "microwave",
  key: 1527,
  name: "Panasonic",
  powerSource: 120,
  powerConsumption: 1500
}) -[:POWERED_BY]->(out6)