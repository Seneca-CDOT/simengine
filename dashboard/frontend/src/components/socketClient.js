class simengineSocketClient {
  constructor(dataCallback) {
    // set up endpoint URL
    let newUri = '';
    const loc = window.location;

    if (loc.protocol === 'https:') {
      newUri = 'wss:';
    } else {
      newUri = 'ws:';
    }

    newUri += '//' + loc.hostname + ':8000/simengine';

    this.ws = new WebSocket(newUri);

    this.ws.onmessage = (evt) => {
      const data = JSON.parse(evt.data);

      console.log('Server sent data: ');
      console.log(data);

      switch (data.request) {
        case 'sys_layout':
          dataCallback.onTopologyReceived(data.payload);
          break;
        case 'ambient_upd':
          dataCallback.onAmbientReceived(data.payload);
          break;
        case 'asset_upd':
          dataCallback.onAssetReceived(data.payload);
          break;
        case 'mains_upd':
          dataCallback.onMainsReceived(data.payload);
          break;
        case 'play_list':
          dataCallback.onPlaylistReceived(data.payload);
          break;
      }
    };
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
