

class simengineSocketClient {

  constructor ({onTopologyReceived, onAmbientReceived, onAssetReceived, onMainsReceived}) {

    // set up endpoint URL
    let new_uri = '';
    const loc = window.location;

    if (loc.protocol === "https:") {
      new_uri = "wss:";
    } else {
      new_uri = "ws:";
    }
    
    new_uri += "//" + loc.hostname + ':8000/simengine';

    this.ws = new WebSocket(new_uri);

    this.ws.onmessage = ((evt) =>
    {
      const data = JSON.parse(evt.data);
      
      console.log("Server sent data: ");
      console.log(data);

      if (data.request === 'topology') {
        onTopologyReceived(data.data);
      } else if (data.request === 'ambient') {
        onAmbientReceived(data.data);
      } else if (data.request === 'asset') {
        onAssetReceived(data.data);
      } else if (data.request === 'mains') {
        onMainsReceived(data.data);
      }
    });
  }

  onOpen(cb) {
    this.ws.onopen = cb;
  }

  onClose(cb) {
    this.ws.onclose = cb;
  }

  socketOnline() {
    return this.ws.readyState == this.ws.OPEN;
  }

  sendData(data) {
    this.ws.send(JSON.stringify(data));
  }
}

export default simengineSocketClient;