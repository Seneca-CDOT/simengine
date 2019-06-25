from enginecore.state.new_engine import Engine
import time

engine = Engine()
engine.start()

while True:
    engine.handle_voltage_update(0, 120)
    time.sleep(1)
