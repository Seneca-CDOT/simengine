

class simengineSocketClient {

  constructor (dataCallback) {

    // set up endpoint URL
    let newUri = '';
    const loc = window.location;

    if (loc.protocol === "https:") {
      newUri = "wss:";
    } else {
      newUri = "ws:";
    }

    newUri += "//" + loc.hostname + ':8000/simengine';

    this.ws = new WebSocket(newUri);

    this.ws.onmessage = ((evt) =>
    {
      const data = JSON.parse(evt.data);

      console.log("Server sent data: ");
      console.log(data);

      switch(data.request) {
        case 'topology':
          dataCallback.onTopologyReceived(data.data);
          break;
        case 'ambient':
          dataCallback.onAmbientReceived(data.data);
          break;
        case 'asset':
          dataCallback.onAssetReceived(data.data);
          break;
        case 'mains':
          dataCallback.onMainsReceived(data.data);
          break;
        case 'plays':
          dataCallback.onPlaylistReceived(data.data);
          break;
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
