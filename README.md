*This project has been created as part of the 42 curriculum by adraji.*

# Fly-In: Drone Routing Simulation

## Description
The goal of this project is to design a system that efficiently routes a fleet of drones from a central base (start) to a target location (end) through a network of connected zones. It optimizes movement to minimize total simulation turns while strictly adhering to graph constraints, capacity rules, and path movement costs.

## Instructions
### Compilation & Installation
Ensure you have Python 3.12+ installed. This project uses `poetry` for dependency management.
To install all necessary dependencies, use the provided Makefile:
```bash
make install
```

### Execution
Run the simulation by providing a map file:
```bash
make run MAP=map.txt
```
To run the debug mode:
```bash
make debug MAP=map.txt
```
To run code linting and type checking (Flake8 and Mypy):
```bash
make lint
make lint-strict
```

## Example
### Input File
```
nb_drones: 5

start_hub: hub 0 0 [color=green]
hub: roof1 3 4 [zone=restricted color=red]
hub: roof2 6 2 [zone=normal color=blue]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
hub: tunnelB 7 4 [zone=normal color=red]
hub: obstacleX 5 5 [zone=blocked color=gray]
end_hub: goal 10 10 [color=yellow]

connection: hub-roof1
connection: hub-corridorA
connection: roof1-roof2
connection: roof2-goal
connection: corridorA-tunnelB [max_link_capacity=2]
connection: tunnelB-goal
```
### Expected Output
```
1: D1-corridorA D3-hub-roof1
2: D1-tunnelB D2-corridorA D3-roof1
3: D1-goal D2-tunnelB D3-roof2 D4-corridorA
4: D2-goal D3-goal D4-tunnelB D5-corridorA
5: D4-goal D5-tunnelB
6: D5-goal
```


## Algorithm & Implementation Strategy
The core routing strategy utilizes a graph pathfinding approach, avoiding third-party graph libraries (such as `networkx`). The implementation revolves around:
- **State Evaluation Turn-by-Turn**: Moving drones conditionally based on connection and zone capacities (`max_drones` and `max_link_capacity`).
- **Custom Parsing & Type Safety**: A robust parser constructs `Hub` and `Connection` objects. All custom logic errors (e.g., duplicate hubs, overlapping coordinates) are correctly caught. The project strictly uses `mypy` and `flake8` for type-safety and style validation.
- **Drone Scheduler**: Continuously calculates overlapping paths dynamically while prioritizing short travel times and avoiding blockages. Multi-turn delays (e.g., `restricted` zones taking 2 turns) are properly simulated.

## Visual Representation
The simulation outputs a standard turn-by-turn text-based history showing `D<ID>-<zone>` formats as required. In addition, the graph components encapsulate standard color metadata attributes that can integrate easily into terminal colors or a PyGame visual representation (as implemented in `pygame`). When outputting via console, ANSI escape codes translate hub colors directly into the user interface to enhance readability and user experience.

## Resources
- [Medium](https://medium.com/basecs/a-gentle-introduction-to-graph-theory-77969829ead8)
### AI Using
- I used AI to develop the idea of ​​the algorithm that came to me at the beginning of my work on this project, by giving it an initial idea of ​​the algorithm, then taking care of the problems that I had to solve or that I would face, and so on until I arrived at this algorithm.