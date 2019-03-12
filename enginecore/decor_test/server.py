

from recorder import recorder

class Server:


    @recorder
    def power_down(self):
        print('powering down')

    @recorder
    def power_up(self):
        print('powering up')

    @recorder
    def destroy_fan(self, fan_index):
        print('nuking fan #{}'.format(fan_index))


