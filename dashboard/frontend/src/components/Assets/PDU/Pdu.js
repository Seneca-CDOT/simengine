
import React from 'react';
import pdu from '../../../images/pdu-empty.svg';
import pdu2 from '../../../images/pdu-selected.svg';
import { Text, Image, Group, Line } from 'react-konva';
import Socket from '../common/Socket';


export default class Pdu extends React.Component {


  constructor() {
    super();
    this.state = {
      image: null,
      color: 'grey',
      selectedSocket: -1,
    };

    this.pduRef = React.createRef();
    this.selectSocket = this.selectSocket.bind(this)
  }

  componentDidMount() {
    const image = new window.Image();
    image.src = pdu;
    image.onload = () => {
      // setState will redraw layer
      // because "image" property is changed
      this.setState({
        image: image
      });
    };
  }


  handlePduSelection = () => {

    const selected = !this.state.selected;
    let image = this.state.image;
    image.src = selected ? pdu2: pdu;

    this.setState({
      selected: selected
    });

    if(selected) {
      this.props.onElementSelection(this.props.elementId);
    }
  };

  selectSocket = (i) => {

    // deselect PDU
    let image = this.state.image;
    image.src = pdu;
    this.setState({
      selected: false,
      selectedSocket: ""+this.props.elementId+(i+1)
    });

    this.props.onElementSelection(String(this.props.elementId) + (i + 1));
  }

  render() {
    let sockets = [];
    let inputSocket = <Socket x={30} socketName={"input socket"} selectable={false}/>

    let x=160;
    let pduName = this.props.name?this.props.name:'pdu';
    const pduElement = this.props.elementInfo[this.props.elementId];

    for (let i=0; i< pduElement.children.length; i++) {
      sockets.push(
        <Socket
          x={x}
          key={i}
          socketName={"output [" + (i+1) + "]"}
          onElementSelection={() => {this.selectSocket(i)}}
          selectable={true}
          elementInfo={this.props.elementInfo}
          elementId={pduElement.children[i]}
          selectedSocket={this.state.selectedSocket}
          parentSelected={this.state.selected}
        />
      );
      x += 90;
    }


    return (
      <Group
        draggable="true"
        onDragEnd={this.props.onPosChange}
      >
        <Text text={pduName} />
        <Image
          image={this.state.image}
          onClick={this.handlePduSelection}
          fill={null}
        />
        <Line />
        {inputSocket}
        {sockets}
      </Group>
    )
  }
}
