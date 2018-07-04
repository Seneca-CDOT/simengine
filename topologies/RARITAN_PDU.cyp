///////////////////////////////////////////
// Cypher Script for PDU component
///////////////////////////////////////////

// ----------------------------------------
///// Outlet (Instance of the Simulator) /////
// ----------------------------------------
CREATE (out:Asset:Outlet { name: 'out',  key: 1112 })

// ----------------------------------------
///// PDU (Instance of the Simulator) /////
// ----------------------------------------
CREATE (pdu:Asset:PDU:SNMPSim { 
  name: 'Rariton PDU',
  key: 1111,
  staticOidFile: 'pdu/raritan-pdu.snmprec'
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
CREATE (out1:Asset:Outlet:Component { 
  name: 'out1',
  key: 11111
})

CREATE (out2:Asset:Outlet:Component { 
  name: 'out2',  
  key: 11112
})

CREATE (out3:Asset:Outlet:Component { 
  name: 'out3',
  key: 11113
})

CREATE (out4:Asset:Outlet:Component { 
  name: 'out4',
  key: 11114
})

CREATE (out5:Asset:Outlet:Component { 
  name: 'out5',
  key: 11115
})

CREATE (out6:Asset:Outlet:Component { 
  name: 'out6',
  key: 11116
})

CREATE (out7:Asset:Outlet:Component { 
  name: 'out7',
  key: 11117
})

CREATE (out8:Asset:Outlet:Component { 
  name: 'out8',
  key: 11118
})


// OIDs that belong to the PDU //
// - - - - - - - - - - - - - - - 

///////// Socket States - on/off ////////////

CREATE (OutletStateDetails:OIDDesc {
  `1`: "switchOn",
  `0`: "switchOff"
}) 

CREATE (out1State:OID {
  name: "OutletState",
  OID: "1.3.6.1.4.1.13742.4.1.2.2.1.3.1",
  OIDName: "OutletState", 
  defaultValue: 1, // on by default
  dataType: 2
})

CREATE (out2State:OID {
  name: "OutletState2",
  OID: "1.3.6.1.4.1.13742.4.1.2.2.1.3.2",
  OIDName: "OutletState", 
  defaultValue: 1,
  dataType: 2
})

CREATE (out3State:OID {
  name: "OutletState3",
  OID: "1.3.6.1.4.1.13742.4.1.2.2.1.3.3",
  OIDName: "OutletState", 
  defaultValue: 1,
  dataType: 2
})

CREATE (out4State:OID {
  name: "OutletState4",
  OID: "1.3.6.1.4.1.13742.4.1.2.2.1.3.4",
  OIDName: "OutletState", 
  defaultValue: 1,
  dataType: 2
})

CREATE (out5State:OID {
  name: "OutletState5",
  OID: "1.3.6.1.4.1.13742.4.1.2.2.1.3.5",
  OIDName: "OutletState", 
  defaultValue: 1,
  dataType: 2
})

CREATE (out6State:OID {
  name: "OutletState6",
  OID: "1.3.6.1.4.1.13742.4.1.2.2.1.3.6",
  OIDName: "OutletState", 
  defaultValue: 1,
  dataType: 2
})

CREATE (out7State:OID {
  name: "OutletState7",
  OID: "1.3.6.1.4.1.13742.4.1.2.2.1.3.7",
  OIDName: "OutletState", 
  defaultValue: 1,
  dataType: 2
})

CREATE (out8State:OID {
  name: "OutletState8",
  OID: "1.3.6.1.4.1.13742.4.1.2.2.1.3.8",
  OIDName: "OutletState", 
  defaultValue: 1,
  dataType: 2
})

///////// Outlet Current ////////////

CREATE (out1Current:OID {
  name: "OutletCurrent",
  OIDName: "OutletCurrent",
  OID: "1.3.6.1.4.1.13742.4.1.2.2.1.4.1",
  defaultValue: 0, 
  dataType: 66
})

CREATE (out2Current:OID {
  name: "OutletCurrent2",
  OIDName: "OutletCurrent",
  OID: "1.3.6.1.4.1.13742.4.1.2.2.1.4.1.2",
  defaultValue: 0,
  dataType: 66
})

CREATE (out3Current:OID {
  name: "OutletCurrent3",
  OIDName: "OutletCurrent",
  OID: "1.3.6.1.4.1.13742.4.1.2.2.1.4.1.3",
  defaultValue: 0,
  dataType: 66
})

CREATE (out4Current:OID {
  name: "OutletCurrent4",
  OIDName: "OutletCurrent",
  OID: "1.3.6.1.4.1.13742.4.1.2.2.1.4.1.4",
  defaultValue: 0,
  dataType: 66
})

CREATE (out5Current:OID {
  name: "OutletCurrent5",
  OIDName: "OutletCurrent",
  OID: "1.3.6.1.4.1.13742.4.1.2.2.1.4.1.5",
  defaultValue: 0,
  dataType: 66
})

CREATE (out6Current:OID {
  name: "OutletCurrent6",
  OIDName: "OutletCurrent",
  OID: "1.3.6.1.4.1.13742.4.1.2.2.1.4.1.6",
  defaultValue: 0,
  dataType: 66
})

CREATE (out7Current:OID {
  name: "OutletCurrent7",
  OIDName: "OutletCurrent",
  OID: "1.3.6.1.4.1.13742.4.1.2.2.1.4.1.7",
  defaultValue: 0,
  dataType: 66
})

CREATE (out8Current:OID {
  name: "OutletCurrent8",
  OIDName: "OutletCurrent",
  OID: "1.3.6.1.4.1.13742.4.1.2.2.1.4.1.8",
  defaultValue: 0,
  dataType: 66
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

CREATE (pdu)-[:HAS_OID]->(out1Current)
CREATE (pdu)-[:HAS_OID]->(out2Current)
CREATE (pdu)-[:HAS_OID]->(out3Current)
CREATE (pdu)-[:HAS_OID]->(out4Current)
CREATE (pdu)-[:HAS_OID]->(out5Current)
CREATE (pdu)-[:HAS_OID]->(out6Current)
CREATE (pdu)-[:HAS_OID]->(out7Current)
CREATE (pdu)-[:HAS_OID]->(out8Current)


CREATE (out1State)-[:HAS_STATE_DETAILS]->(OutletStateDetails)
CREATE (out2State)-[:HAS_STATE_DETAILS]->(OutletStateDetails)
CREATE (out3State)-[:HAS_STATE_DETAILS]->(OutletStateDetails)
CREATE (out4State)-[:HAS_STATE_DETAILS]->(OutletStateDetails)
CREATE (out5State)-[:HAS_STATE_DETAILS]->(OutletStateDetails)
CREATE (out6State)-[:HAS_STATE_DETAILS]->(OutletStateDetails)
CREATE (out7State)-[:HAS_STATE_DETAILS]->(OutletStateDetails)
CREATE (out8State)-[:HAS_STATE_DETAILS]->(OutletStateDetails)


CREATE (pdu)-[:HAS_COMPONENT]->(out1)
CREATE (pdu)-[:HAS_COMPONENT]->(out2)
CREATE (pdu)-[:HAS_COMPONENT]->(out3)
CREATE (pdu)-[:HAS_COMPONENT]->(out4)
CREATE (pdu)-[:HAS_COMPONENT]->(out5)
CREATE (pdu)-[:HAS_COMPONENT]->(out6)
CREATE (pdu)-[:HAS_COMPONENT]->(out7)
CREATE (pdu)-[:HAS_COMPONENT]->(out8)

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
