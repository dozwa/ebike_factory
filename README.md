# E-Bike Factory Simulation

## Introduction
This project provides a simple simulation environment for an e-bike production facility implemented using `simpy`. 
The simulation models the manufacturing process of e-bikes, including several production steps, stock management and quality control.

## Installation

To run this simulation, you need Python 3 and the installation of the `simpy` library. You can install `simpy` with pip:

```bash
pip install simpy
```

Make sure you also have random and os modules available in your Python environment, but these should already be included in most standard Python installations.

## Usage
To start the simulation, run the script with Python:

```bash
python ebike_factory_simulation.py
```

The script simulates the operation of an e-bike factory over a defined period of time and outputs the total number of e-bikes produced and shipped.

## Components

The simulation consists of the following components, the flow of goods is represented by the arrows.

![Representation of the components and goods flows](https://github.com/dozwa/ebike_factory/blob/main/eBike_Fabrik.drawio.png)

## License
This project is licensed under the MIT license - see the LICENSE.md file for details.

## Acknowledgment

This project is based on the article ["Manufacturing Simulation Using SimPy"](https://towardsdatascience.com/manufacturing-simulation-using-simpy-5b432ba05d98) and the GitHub repository [guitar_factory](https://github.com/juanhorgan/guitar_factory) by juanhorgan. Thank you @juanhorgan for providing it!
