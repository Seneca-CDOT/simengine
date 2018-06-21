
match (out6:Outlet {key: 20134})

CREATE (microwave:Asset:StaticAsset {
  type: "microwave",
  key: 1527,
  name: "Panasonic",
  imgUrl: "https://cdn.pixabay.com/photo/2013/07/13/12/03/microwave-159076_640.png",
  powerSource: 120,
  powerConsumption: 1500
}) -[:POWERED_BY]->(out6)