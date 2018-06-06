///////////////////////////////////////////
// Cypher Script for PDU component
///////////////////////////////////////////

// ----------------------------------------
///// Outlet (Instance of the Simulator) /////
// ----------------------------------------
CREATE (out:Asset:Outlet { name: 'out',  key: 11112 })

// ----------------------------------------
///// PDU (Instance of the Simulator) /////
// ----------------------------------------
CREATE (pdu:Asset:PDU:SNMPSim { 
  name: 'pdu',
  key: 1111
})

// OIDs that belong to the PDU //
// - - - - - - - - - - - - - - - 
CREATE (SerialNumber:OID {
  name: "SerialNumber",
  OID: ".1.3.6.1.4.1.318.1.1.4.1.5.0",
  defaultValue: 1999201,
  type: "read"
})


CREATE (WattacheDraw:OID {
  name: "WattageDraw",
  OID: ".1.3.6.1.4.1.318.1.1.12.1.16.0",
  defaultValue: 14,
  type: "write"
})

CREATE (ModelNumber:OID {
  name: "ModelNumber",
  OID: ".1.3.6.1.4.1.318.1.1.4.1.4.0",
  defaultValue: "AAABBBCCC",
  type: "read"
})

// ---------------------
///// PDU outlets  /////
// ---------------------
CREATE (out1:Asset:Outlet:SNMPComponent { 
  name: 'out1',
  key: 11111
})

CREATE (out2:Asset:Outlet:SNMPComponent { 
  name: 'out2',  
  key: 11112
})

CREATE (out3:Asset:Outlet:SNMPComponent { 
  name: 'out3',
  key: 11113
})


// OIDs that belong to the PDU //
// - - - - - - - - - - - - - - - 
CREATE (out1State:OID {
  name: "CurrentState",
  OID: ".1.3.6.1.4.1.318.1.1.4.4.2.1.3.1",
  defaultValue: 1,
  type: "write"
})

CREATE (out2State:OID {
  name: "CurrentState",
  OID: ".1.3.6.1.4.1.318.1.1.4.4.2.1.3.2",
  defaultValue: 1,
  type: "write"
})

CREATE (out3State:OID {
  name: "CurrentState",
  OID: ".1.3.6.1.4.1.318.1.1.4.4.2.1.3.3",
  defaultValue: 1,
  type: "write"
})


// -------------------------------------------
///// Switch (Instance of the Simulator) /////
// -------------------------------------------
CREATE (switch:Asset:Switch:SNMPSim { 
  name: 'switch1',
   key: 11113
})


//////////////////////////////
// Connect Nodes/Components //
//////////////////////////////
CREATE (pdu)-[:POWERED_BY]->(out)
CREATE (pdu)-[:HAS_OID]->(SerialNumber)
CREATE (pdu)-[:HAS_OID]->(WattacheDraw)
CREATE (pdu)-[:HAS_OID]->(ModelNumber)
CREATE (pdu)-[:HAS_OID]->(out1State)
CREATE (pdu)-[:HAS_OID]->(out2State)
CREATE (pdu)-[:HAS_OID]->(out3State)

CREATE (pdu)-[:HAS_SNMP_COMPONENT]->(out1)
CREATE (pdu)-[:HAS_SNMP_COMPONENT]->(out2)
CREATE (pdu)-[:HAS_SNMP_COMPONENT]->(out3)

CREATE (switch)-[:POWERED_BY]->(out3)

CREATE (out1)-[:POWERED_BY]->(out1State)
CREATE (out2)-[:POWERED_BY]->(out2State)
CREATE (out3)-[:POWERED_BY]->(out3State)

CREATE (out1)-[:POWERED_BY]->(pdu)
CREATE (out2)-[:POWERED_BY]->(pdu)
CREATE (out3)-[:POWERED_BY]->(pdu)

