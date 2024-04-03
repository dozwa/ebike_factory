# Based on Guitar factory by juanhorgan
# see https://github.com/juanhorgan/guitar_factory/
# also https://towardsdatascience.com/manufacturing-simulation-using-simpy-5b432ba05d98


# Noch zu tun:
# - individuelle Maschinenfehler einbauen
# - Maschinenwartung einbauen
# - Log für Container erstellen
# - Auswertung der Simulation


import simpy
import random
import os

ebikes_made = 0

print(f'STARTING SIMULATION')
print(f'----------------------------------')

#-------------------------------------------------

#Parameters

# random seed
random.seed(42)

#working hours
hours = 8

#business days
days = 200

#total working time (hours)
total_time = hours * days

# containers

    #drive system
drive_system_capacity = 100
initial_drive_system = 50

    #body
body_capacity = 100
initial_body = 50

    #wheels
wheels_capacity = 100
initial_wheels = 50

    #ebike
ebike_capacity = 100

    #dispatch
dispatch_capacity = 500

# Machine capacities
num_paint_shop = 1
num_body_assembler = 2
num_drive_system_assembler = 2
num_ebike_assembler = 2
num_quality_control = 1

# Machine times
mean_paint = 1
std_paint = 0.5

mean_body_assembler = 2
std_body_assembler = 0.3

mean_drive_system_assembler = 2
std_drive_system_assembler = 0.4

mean_ebike_assembler = 2
std_ebike_assembler = 0.4

mean_quality_control = 1
std_quality_control = 0.1



#critical levels
    #critical stock should be 1 business day greater than supplier take to come
drive_system_critical_stock = 10
body_critical_stock = 10
wheels_critical_stock = 10

#-------------------------------------------------

# Logging

log_path = "ebike_factory/Logs/"

# Log function
def log_machine(machine, message):
    global log_path
    filepath = log_path + machine.name + '.txt'
    # Create log file if it doesn't exist
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    file = open(filepath, 'a')
    file.write(f'{machine.name} {message} at day {int(env.now/8)}, hour {round(env.now % 8,2)}\n')
    file.close()

def log_stock(message):
    global log_path
    filepath = log_path + 'stock_control.txt'
    # Create log file if it doesn't exist
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    file = open(filepath, 'a')
    file.write(f'{message} at day {int(env.now/8)}, hour {round(env.now % 8,2)}\n')
    file.close()


#-------------------------------------------------

# Named container class, to give names to containers which is not possible in simpy
class NamedContainer(simpy.resources.container.Container):
    def __init__(self, *args, name="container", **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name

# Stock controller class
        
class StockController:
    def __init__(self, env, resource, critical_stock, name):
        self.env = env
        self.resource = resource
        self.critical_stock = critical_stock
        self.name = name
        self.process = env.process(self.run())

    def run(self):
        yield self.env.timeout(0)
        while True:
            if self.resource.level <= self.critical_stock:
                log_stock(f'{self.name} stock below critical level ({self.resource.level})')
                log_stock(f'calling {self.name} supplier')
                yield self.env.timeout(16)
                log_stock(f'{self.name} supplier arrives')
                yield self.resource.put(30)
                log_stock(f'new {self.name} stock is {self.resource.level}')
                yield self.env.timeout(8)
            else:
                yield self.env.timeout(1)

# Factory class
class EBike_Factory:
    def __init__(self, env):
        # Containers
            # Containers for initial compontens from suppliers
        self.drive_system_a = NamedContainer(env, capacity = drive_system_capacity, init = initial_drive_system, name = 'drive_system_a')
        self.body_a = NamedContainer(env, capacity = body_capacity, init = initial_body, name = 'body_a')
        self.wheels_a = NamedContainer(env, capacity = wheels_capacity, init = initial_wheels, name = 'wheels_a')
            # Containers for production
        self.drive_system_b = NamedContainer(env, capacity = drive_system_capacity, init = 0, name = 'drive_system_b')
        self.drive_system_c = NamedContainer(env, capacity = drive_system_capacity, init = 0, name = 'drive_system_c')
        self.body_b = NamedContainer(env, capacity = body_capacity, init = 0, name = 'body_b')
        self.body_c = NamedContainer(env, capacity = body_capacity, init = 0, name = 'body_c')
        self.ebike_a = NamedContainer(env, capacity = ebike_capacity, init = 0, name = 'ebike_a')
            # Container for dispatch
        self.ebike_b = NamedContainer(env, capacity = ebike_capacity, init = 0, name = 'ebike_b')

        # Stock control processes
        self.drive_system_control = StockController(env, self.drive_system_a, drive_system_critical_stock, 'drive_system')
        self.body_control = StockController(env, self.body_a, body_critical_stock, 'body')
        self.wheels_control = StockController(env, self.wheels_a, wheels_critical_stock, 'wheels')
        self.dispatch_control = env.process(self.dispatch_ebikes_control(env))

    def dispatch_ebikes_control(self, env):
        global ebikes_made
        yield env.timeout(0)
        while True:
            if self.ebike_b.level >= 50:
                log_stock(f'dispach stock is {self.ebike_b.level} calling store to pick ebikes')
                yield env.timeout(4)
                log_stock(f'store picking {self.ebike_b.level} ebikes')
                ebikes_made += self.ebike_b.level
                yield self.ebike_b.get(self.ebike_b.level)
                yield env.timeout(8)
            else:
                yield env.timeout(1)

#-------------------------------------------------

# Machines

class Machine:
    def __init__(self, env, name, parts_list, mean_time, std_time, parts_required=1):
        global input_storages
        global output_storages
        self.env = env
        self.name = name
        self.input_storage = input_storages if isinstance(input_storages, dict) else [input_storages]
        self.input_storage = input_storages if isinstance(input_storages, dict) else [input_storages]
        self.output_storages = output_storages if isinstance(output_storages, dict) else [output_storages]
        self.mean_time = mean_time
        self.std_time = std_time
        self.parts_required = parts_required  # Anzahl der gleichzeitig zu bearbeitenden Teile
        self.parts_in_machine = 0  # Anzahl der Teile, die sich gerade in der Maschine befinden
        self.parts_produced = -1  # Anzahl der Teile, die die Maschine produziert hat
        self.process = env.process(self.run())
        self.defect = False
        self.parts_list = parts_list
        self.parts_stock = {key: 0 for key in parts_list}
    
    def defect_function(self):
        log_machine(self, f'error not fixed, parts discarded')
        yield env.timeout(2)
        log_machine(self, f'calling maintenance')
        yield env.timeout(8)
        log_machine(self, f'maintenance done')
        self.defect = True

    def error(self):
        log_machine(self, f'got an error')
        yield env.timeout(2)
        
    def output(self):
        for output_storage in self.output_storages[self.name]:
            yield self.env.timeout(1/30)  # 1/30 hour is the time to put a part in the storage to simulate transportation
            yield output_storage.put(1)
            self.parts_produced += 1
            log_machine(self, f'put 1 part {output_storage.name} in {output_storage.name}-storage')

    def run(self):
        # parts_produced with -1 to avoid pulling parts from the input_storages without producing parts while initializing machine
        if self.parts_produced == -1:
            self.parts_produced = 0
        else:
            while True:
                # Prüfen ob die anzahl der teile in parts_stock dirctionary, den benötigten teilen in parts_list dictionary entspricht, wenn nicht, dann teil anfordern
                for key in self.parts_list:
                    if self.parts_stock[key] < self.parts_list[key]:
                        yield self.input_storage[key].get(1)
                        yield self.env.timeout(1/30)  # 1/30 hour is the time to get a part from the storage to simulate transportation
                        self.parts_stock[key] += 1
                        self.parts_in_machine += 1  # Teile in der Maschine erhöhen
                        log_machine(self, f'got part 1 part {self.input_storage[key].name} from {self.input_storage[key].name}-storage, current stock {self.parts_in_machine}')
                log_machine(self, f'has {self.parts_in_machine} parts in machine i.e. {self.parts_stock}')

                # Wenn alle notwendigen Teile in der Maschine sind, dann Maschine starten
                process_time = max(random.gauss(self.mean_time, self.std_time), 1)
                yield self.env.timeout(process_time)

                # Randomly generate errors
                if random.randint(0, 10) < 1:
                    yield from self.error()
                    # Randomly generate defects
                    if random.randint(0, 10) < 3:
                        yield from self.defect_function()

                # Generate output
                if self.defect == False:
                    yield from self.output()
                else:
                    self.defect = False

                self.parts_in_machine -= sum(self.parts_stock.values())
                for key in self.parts_stock:
                    if key in self.parts_list:
                        self.parts_stock[key] -= self.parts_list[key]
                log_machine(self, f'has {self.parts_in_machine} parts in machine i.e. {self.parts_stock}')

#-------------------------------------------------
        
#Generators

        
def paint_shop_gen(env, ebike_factory):
    for i in range(num_paint_shop):
        paint_shop = Machine(env, "paint_shop", paint_shop_parts, mean_paint, std_paint, parts_required=2)
        env.process(paint_shop.run())
        yield env.timeout(0)

def body_assembler_gen(env, ebike_factory):
    for i in range(num_body_assembler):
        body_assembler = Machine(env, "body_assembler" , body_assembler_parts, mean_body_assembler, std_body_assembler)
        env.process(body_assembler.run())
        yield env.timeout(0)

def drive_system_assembler_gen(env, ebike_factory):
    for i in range(num_drive_system_assembler):
        drive_system_assembler = Machine(env, "drive_system_assembler", drive_system_assembler_parts, mean_drive_system_assembler, std_drive_system_assembler)
        env.process(drive_system_assembler.run())
        yield env.timeout(0)

def ebike_assembler_gen(env, ebike_factory):
    for i in range(num_ebike_assembler):
        ebike_assembler = Machine(env, "ebike_assembler", ebike_assembler_parts, mean_ebike_assembler, std_ebike_assembler, parts_required=4)
        env.process(ebike_assembler.run())
        yield env.timeout(0)

def quality_control_gen(env, ebike_factory):
    for i in range(num_quality_control):
        quality_control = Machine(env, "quality_control", quality_control_parts, mean_quality_control, std_quality_control)
        env.process(quality_control.run())
        yield env.timeout(0)

#-------------------------------------------------

env = simpy.Environment()
ebike_factory = EBike_Factory(env)

#-------------------------------------------------

# Parts dictionary
                    
paint_shop_parts = {'body_b': 1, 'drive_system_a': 1}
body_assembler_parts = {'body_a': 1}
drive_system_assembler_parts = {'drive_system_b': 1}
ebike_assembler_parts = {'body_c': 1, 'drive_system_c': 1, 'wheels_a': 1}
quality_control_parts = {'ebike_a': 1}

# Storage dictionary

input_storages = {'drive_system_a': ebike_factory.drive_system_a, 
                    'body_a': ebike_factory.body_a, 
                    'wheels_a': ebike_factory.wheels_a, 
                    'drive_system_b': ebike_factory.drive_system_b, 
                    'drive_system_c': ebike_factory.drive_system_c, 
                    'body_b': ebike_factory.body_b, 
                    'body_c': ebike_factory.body_c, 
                    'ebike_a': ebike_factory.ebike_a, 
                    'ebike_b': ebike_factory.ebike_b}

output_storages = {"paint_shop": [ebike_factory.drive_system_b, ebike_factory.body_c],
                    "body_assembler": [ebike_factory.body_b],
                    "drive_system_assembler": [ebike_factory.drive_system_c],
                    "ebike_assembler": [ebike_factory.ebike_a],
                    "quality_control": [ebike_factory.ebike_b]}

paint_shop_gen = env.process(paint_shop_gen(env, ebike_factory))
body_assembler_gen = env.process(body_assembler_gen(env, ebike_factory))
drive_system_assembler_gen = env.process(drive_system_assembler_gen(env, ebike_factory))
ebike_assembler_gen = env.process(ebike_assembler_gen(env, ebike_factory))
quality_control_gen = env.process(quality_control_gen(env, ebike_factory))

env.run(until = total_time)

print(f'----------------------------------')
print('total ebikes dispatched: {0}'.format(ebikes_made))
print(f'----------------------------------')
print(f'SIMULATION COMPLETED')


#-------------------------------------------------



