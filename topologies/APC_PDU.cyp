///////////////////////////////////////////
// Cypher Script for PDU component
///////////////////////////////////////////

// ----------------------------------------
///// Outlet (Instance of the Simulator) /////
// ----------------------------------------
CREATE (out:Asset:Outlet { name: 'out',  key: 1116 })

// ----------------------------------------
///// PDU (Instance of the Simulator) /////
// ----------------------------------------
CREATE (pdu:Asset:PDU:SNMPSim { 
  name: 'APC PDU',
  key: 2013,
  staticOidFile: 'pdu/apc-pdu.snmprec'
})

// OIDs that belong to the PDU //
// - - - - - - - - - - - - - - - 

CREATE (OutletCount:OID {
  name: "OutletCount",
  OID: "1.3.6.1.4.1.13742.4.1.2.1.0",
  defaultValue: 8,
  dataType: 2  
})

// ---------------------
///// PDU outlets  /////
// ---------------------

CREATE (out1:Asset:Outlet:SNMPComponent { 
  name: 'out1',
  key: 20131
})

CREATE (out2:Asset:Outlet:SNMPComponent { 
  name: 'out2',  
  key: 20132
})

CREATE (out3:Asset:Outlet:SNMPComponent { 
  name: 'out3',
  key: 20133
})

CREATE (out4:Asset:Outlet:SNMPComponent { 
  name: 'out4',
  key: 20134
})

CREATE (out5:Asset:Outlet:SNMPComponent { 
  name: 'out5',
  key: 20135
})

CREATE (out6:Asset:Outlet:SNMPComponent { 
  name: 'out6',
  key: 20136
})

CREATE (out7:Asset:Outlet:SNMPComponent { 
  name: 'out7',
  key: 20137
})

CREATE (out8:Asset:Outlet:SNMPComponent { 
  name: 'out8',
  key: 20138
})


// OIDs that belong to the PDU //
// - - - - - - - - - - - - - - - 


///////// Socket States - on/off ////////////
CREATE (OutletStateDetails:OIDDesc {
  `1`: "switchOn",
  `2`: "switchOff"
}) 

CREATE (out1State:OID {
  name: "OutletState",
  OID: "1.3.6.1.4.1.318.1.1.12.3.3.1.1.4.1",
  OIDName: "OutletState", 
  defaultValue: 1, // on by default
  dataType: 2 // INTEGER dt   
})

CREATE (out2State:OID {
  name: "OutletState2",
  OID: "1.3.6.1.4.1.318.1.1.12.3.3.1.1.4.2",
  OIDName: "OutletState", 
  defaultValue: 1,
  dataType: 2
})

CREATE (out3State:OID {
  name: "OutletState3",
  OID: "1.3.6.1.4.1.318.1.1.12.3.3.1.1.4.3",
  OIDName: "OutletState", 
  defaultValue: 1,
  dataType: 2
})

CREATE (out4State:OID {
  name: "OutletState4",
  OID: "1.3.6.1.4.1.318.1.1.12.3.3.1.1.4.4",
  OIDName: "OutletState", 
  defaultValue: 1,
  dataType: 2
})

CREATE (out5State:OID {
  name: "OutletState5",
  OID: "1.3.6.1.4.1.318.1.1.12.3.3.1.1.4.5",
  OIDName: "OutletState", 
  defaultValue: 1,
  dataType: 2
})

CREATE (out6State:OID {
  name: "OutletState6",
  OID: "1.3.6.1.4.1.318.1.1.12.3.3.1.1.4.6",
  OIDName: "OutletState", 
  defaultValue: 1,
  dataType: 2
})

CREATE (out7State:OID {
  name: "OutletState7",
  OID: "1.3.6.1.4.1.318.1.1.12.3.3.1.1.4.7",
  OIDName: "OutletState", 
  defaultValue: 1,
  dataType: 2
})

CREATE (out8State:OID {
  name: "OutletState8",
  OID: "1.3.6.1.4.1.318.1.1.12.3.3.1.1.4.8",
  OIDName: "OutletState", 
  defaultValue: 1,
  dataType: 2
})



//////////////////////////////
// Connect Nodes/Components //
//////////////////////////////
CREATE (pdu)-[:POWERED_BY]->(out)
CREATE (pdu)-[:HAS_OID]->(OutletCount)

CREATE (pdu)-[:HAS_OID]->(out1State)
CREATE (pdu)-[:HAS_OID]->(out2State)
CREATE (pdu)-[:HAS_OID]->(out3State)
CREATE (pdu)-[:HAS_OID]->(out4State)
CREATE (pdu)-[:HAS_OID]->(out5State)
CREATE (pdu)-[:HAS_OID]->(out6State)
CREATE (pdu)-[:HAS_OID]->(out7State)
CREATE (pdu)-[:HAS_OID]->(out8State)

CREATE (out1State)-[:HAS_STATE_DETAILS]->(OutletStateDetails)
CREATE (out2State)-[:HAS_STATE_DETAILS]->(OutletStateDetails)
CREATE (out3State)-[:HAS_STATE_DETAILS]->(OutletStateDetails)
CREATE (out4State)-[:HAS_STATE_DETAILS]->(OutletStateDetails)
CREATE (out5State)-[:HAS_STATE_DETAILS]->(OutletStateDetails)
CREATE (out6State)-[:HAS_STATE_DETAILS]->(OutletStateDetails)
CREATE (out7State)-[:HAS_STATE_DETAILS]->(OutletStateDetails)
CREATE (out8State)-[:HAS_STATE_DETAILS]->(OutletStateDetails)


CREATE (pdu)-[:HAS_SNMP_COMPONENT]->(out1)
CREATE (pdu)-[:HAS_SNMP_COMPONENT]->(out2)
CREATE (pdu)-[:HAS_SNMP_COMPONENT]->(out3)
CREATE (pdu)-[:HAS_SNMP_COMPONENT]->(out4)
CREATE (pdu)-[:HAS_SNMP_COMPONENT]->(out5)
CREATE (pdu)-[:HAS_SNMP_COMPONENT]->(out6)
CREATE (pdu)-[:HAS_SNMP_COMPONENT]->(out7)
CREATE (pdu)-[:HAS_SNMP_COMPONENT]->(out8)

CREATE (out1)-[:POWERED_BY]->(out1State)
CREATE (out2)-[:POWERED_BY]->(out2State)
CREATE (out3)-[:POWERED_BY]->(out3State)
CREATE (out4)-[:POWERED_BY]->(out4State)
CREATE (out5)-[:POWERED_BY]->(out5State)
CREATE (out6)-[:POWERED_BY]->(out6State)
CREATE (out7)-[:POWERED_BY]->(out7State)
CREATE (out8)-[:POWERED_BY]->(out8State)


CREATE (out1)-[:POWERED_BY]->(pdu)
CREATE (out2)-[:POWERED_BY]->(pdu)
CREATE (out3)-[:POWERED_BY]->(pdu)
CREATE (out4)-[:POWERED_BY]->(pdu)
CREATE (out5)-[:POWERED_BY]->(pdu)
CREATE (out6)-[:POWERED_BY]->(pdu)
CREATE (out7)-[:POWERED_BY]->(pdu)
CREATE (out8)-[:POWERED_BY]->(pdu)
;
