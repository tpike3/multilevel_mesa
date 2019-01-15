# Multi-Level Mesa

Multi-Level (ML) Mesa is a library which supports Python's Agent Based Modelling Library Mesa. ML Mesa's views complex systems as adaptive networks and uses a network graph structure to allow dynamic management of agent modules (groups) and model schedules.

ML Mesa has three main components. First, a collection of managers which tracks the agents, the modules of agents (meta-agents), the network of agents, and agents who belong to an existing meta-agent, and the schedule. Second, a series of functions which provides the user different options to form meta-agents or dissolve them. Third, a meta-agent class which allows for the inclusion of different meta-agent policies, manages the behavior and status of the meta_agent, and implcitily produces hierarchies within the complex system. (Figure 1)

!(ML Mesa Schematic)[https://github.com/tpike3/ml_mesa/blob/master/ml_mesa/picture/ML-Mesa%20Schematic.png]
**Figure 1**

### Creating an ML Mesa Instance and the ML Mesa Managers

Creating an instance of ML Mesa requires one parameter, and initiates one attribute and six managers. The one parameter is min_for_meta, which tells ML_Mesa the minimum number of agents which must be in a meta-agent. The min_for_meta parameter has a default setting of 2. The one attribute of ML Mesa is id_counter, which allows for unique_ids to be generated for meta-agents if the user does not supply any. The six managers are (1) ML_Mesa.\_agents which is an ordered dictionary (a hashtable consisting of a key:value pair) that holds every agent added to the instance. This manager is critical to ensure the most granualar possible of agents. (2) ML_Mesa.net is a instance of a NewtorkX graph. This feature provides the critical strcuture for tracking and managing agent and metaagents. (3) ML_Mesa.agents_by_type uses a dictionary of dictionaries to also track agents by type. This feature allows for faster reference of specific types of agents when manipulating meta-agents or schedules. (4) ML_Mesa.schedule replaces the typical Mesa schedule and is an ordered dictionary which manages the agents and when they execute a step function. (5) ML_Mesa.metas is an ordered dictionary and tracks the meta-agents within the model performing the same function of tracking meta-agents as the agents ordered dictionary. (6) ML_Mesa.reverse_meta is a dictionary of sets. The key is agent identification and the set is meta-agents to which the agent belongs. This structre is necessary to ensure duplicate meta-agents are not created or that an agent should be added to an exisitng meta-agent instead of creating a new one. The use of sets also helps expedite computation by using set operations to evaluate if a meta-agent agent should be formed or agents added to an existing meta-agent. 

### The ML Mesa Functions

As shown in figure 1, ML Mesa has two approaches for producing a multi-level ABM, an explcit approach and a network approach. Underneath these two approaches, ML Mesa turns the desired agents into a bilateral link list which form the meta-agents. Each input of agents if transformed into a network edge which forms the meta_agent or adds agents to the meta-agent. The bilateral link list prevents each meta-agent from being fully connected so a diversity network strcutures can exist both within the whole model and within the meta-agents. 

The explicit approach takes a user defined process which generates a list of agents. As not every network is a fully connected network the user defined function looks at the list from a single agent perspective. The user identifies an agent or group of agents (the default is all agents in the ML_Mesa.\_agents dictionary) and then stipulates an evaluation process. From this process, a list of agents who meet the criteria is generated, which ML Mesa then links to the initial agent. As dictionaries are typically unordered and cannot be manipulated during iteration a *yield* versus the more common *return* function is necessary to pass the list of agents to the function. The function then creates a bilateral link list which in turn forms a meta-agent. 

The network approach uses the network graph    

## Uses

 

## Requirements

 

## Installation 

## Implementation

 

## Required Parameters 


## Default Parameters 



## Example Implementation



## Detailed Description of Module




            
## Weaknesses and Choices


## Happy Modeling!





    
