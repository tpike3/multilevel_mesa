# Multi-Level Mesa

Multi-Level (ML) Mesa is a library which supports Python's Agent Based Modeling Library Mesa. ML Mesa's views complex systems as adaptive networks and uses a network graph structure to allow dynamic management of agent modules (groups) and model schedules.

ML Mesa has three main components. First, a collection of managers which tracks the agents, the modules of agents (meta-agents), the network of agents, and agents who belong to an existing meta-agent, and the schedule. Second, a series of functions which provides the user different options to form meta-agents or dissolve them. Third, a meta-agent class which allows for the inclusion of different meta-agent policies, manages the behavior and status of the meta_agent, and implicitly produces hierarchies within the complex system. (Figure 1)

![ML Mesa Schematic](https://github.com/tpike3/ml_mesa/blob/master/ml_mesa/picture/ML-Mesa%20Schematic.png)
**Figure 1**

## Requirements

ML Mesa requires

    Mesa>=0.8.4
    NetworkX>=2.2  

## Installation 

    pip install ml_mesa

### Creating an ML Mesa Instance and the ML Mesa Managers

Creating an instance of ML Mesa requires no parameters, and initiates one attribute and six managers. The class has one keyword parameter, ML_Mesa.min_for_meta, which tells ML_Mesa the minimum number of agents which must be in a meta-agent. The min_for_meta parameter has a default setting of 2. The one attribute of ML Mesa is id_counter, which allows for unique_ids to be generated for meta-agents. The six managers are:
1. ML_Mesa.\_agents which is an ordered dictionary (a hash-table consisting of a key:value pair) that holds every agent added to the instance. This manager is critical to maintain the most granular dictionary possible of all agents.
2. ML_Mesa.net is a instance of a NewtorkX graph. This feature provides the critical structure for tracking and managing agent and meta-agents.
3. ML_Mesa.agents_by_type uses a dictionary of dictionaries to also track agents by type. This feature allows for faster reference of specific types of agents when manipulating meta-agents or schedules. 
4. ML_Mesa.schedule replaces the typical Mesa schedule and is an ordered dictionary which manages the agents and when they execute a step function. 
5. ML_Mesa.metas is an ordered dictionary and tracks the meta-agents within the model performing the same function of tracking meta-agents as the agents ordered dictionary. 
6. ML_Mesa.reverse_meta is a dictionary of sets. The key is agent identification and the set is meta-agents to which the agent belongs. This structure is necessary to ensure duplicate meta-agents are not created or that an agent should be added to an existing meta-agent instead of creating a new one. The use of sets also helps expedite computation by using set operations to evaluate if a meta-agent should be formed or agents added to an existing meta-agent. 

### The ML Mesa Functions

As shown in figure 1, ML Mesa has two primary approaches for facilitating a multi-level ABM, an explicit approach and a network approach. Underneath these two approaches, ML Mesa turns the desired agents into a bilateral link list which form the meta-agents. Each input of agents is transformed into a network edge which forms the meta_agent or adds agents to an existing meta-agent. The use of links is also used to disband meta-agents or remove agents from the meta-agent. These functions then create a more dynamic schedule based on the criteria of the meta-agent and its associated policies. 

#### Forming and Dissolving Meta-Agents

##### User Defined Formation Process ML_Mesa.form_meta

The formation function of the explicit approach is ML_Mesa.form_meta and takes a user defined process which generates a list of agents. The user defined process provides the criteria for ML_Mesa.form_meta to iterate through the list of agents from the first agent in the list's perspective. This approach can be computationally expensive, but is necessary to allow for the accurate recreation of the network. The user identifies an agent or group of agents (the default is all agents in the ML_Mesa.\_agents dictionary) and then stipulates an evaluation process. From this process, a list of agents who meet the criteria is generated, which ML Mesa then links to the initial agent. As dictionaries cannot be manipulated during iteration users must use a *yield* versus the more common *return* function to pass the list of agents to the form_meta function. The function then creates a bilateral link list which in turn forms a meta-agent. 

**User-Defined Formation Function**
    ```
    def form_meta(self, process, *args, determine_id = 'default', \
                  double = False, policy = None,  **kwargs):
    ```

The ML_Mesa.form_meta function requires one parameter which is the user specified process(es) which determine whether or not an agent should be in a meta-agent with other agents. This passes in the function(s) which determines what agents should be part of a meta_agent. The \*args and \*\*kwargs allows the user to pass in the parameters for these processes. The determine_id arguments ensure each meta-agent gets a unique_id. If default it will simply append a number based on the id_counter attribute to the string 'meta'. For the user to pass in an id he or she must *yield* the id as the first element of a tuple from the user defined process. The double parameter takes a boolean value. If *True* the agent will remain in the schedule as an independent entity, while if *False* the agent is removed. This is to provide users maximum flexibility for agent scheduling and meta-agent processes. The policy parameter passes in the step processes for the meta-agent, which can consist of only internal processes or can consist of meta-agent processes and then execute the individual agent processes.   

##### User Defined Dissolution Process: ML_Mesa.reassess_meta

The dissolution function for the explicit approach (although it can be used interchangeably with the network approach) is ML_Mesa.reassess_meta. This function iterates through each meta-agent and then uses the user defined process to assess on whether or not an agent should still belong to the meta-agent. Similar to the ML_Mesa.form_meta this function requires a *yield* to provide the list of agents which should be removed and then proceeds to remove those agents while updating the appropriate managers. This function also ensures if the meta-agent fails to have a certain number of agents within the meta_agent that the meta-agent will also be removed. This minimum number of agents is the min_for_meta attribute of the ML Mesa instance and has a default setting of two. 

**User-Defined Dissolution Function**
    ```
    def reassess_meta(self, process, *args, reintroduce = True, **kwargs):
    ```

The ML_Mesa.reassess_meta function requires one parameter, which is the process defined by the user for assessing whether or not the agent should remain within the meta_agent. The function also has a reintroduce parameter which takes a boolean value and is default to *True*. This parameter tells the function whether or not to reintroduce the removed agents back into the schedule.  


##### Network Defined Formation: ML_Mesa.net_schedule

The formation function of the network approach is ML_Mesa.net_schedule and uses an undirected NetworkX graph object to assess what agents should form meta-agents. With an undirected graph and as indicated in figure one, there are three possibilities for assessing whether or not linked agents should be in the same meta-agents. First, simply by whether or not a link exists between the agents. Second, if a specific type of link exists. Third, if a link exists which has reached a certain value. For example in the SugarScape verification and validation discussed in the next section, one version forms a meta_agent if an agent and landscape cell are linked, in another version, the agents form a meta-agent if they have 10 or more trades between them. Although, NetworkX also offers the possibility of directed graphs and multi-graphs these options were not used for simplicity sake and because the dynamics of ABMs can account for the main aspects of these features. As NetworkX uses a dictionary structure to capture nodes and links, a multi-graph can be easily simulated by adding more link types along the edge, so a link may have the dictionary keys {family, tribe, job...} allowing for a link with multiple types similar to a multi-graph. The directed graph dynamic can also by achieved through agent interactions as the link attributes can dictate the direction of resources based on agent attributes. The one cost is users can not use the network evaluation functions in NetowrkX associated with multi-graphs and directed graphs. Using an undirected graph provides a leaner, more easily understood approach without loss of network dynamics. 

**Network Formation Function**
    ``` 
    def net_schedule(self, link_type = None, link_value = None, double = False, policy = None):
    ```

The ML_Mesa.net_schedule function requires no parameters and will default to simply if a link exists or not between agents. As the meta-agent is formed purely based on the links between agents, no \*args or \*\*kwargs arguments are required. As the net schedule has no process passed in the id of the meta_agents uses the default "meta" plus a number from the id-counter attribute. If users decided they would like to pass in processes to provide a unique id for meta-agents this could be added in future versions, but was not included in this version as it did not add anything substantive to the ML Mesa dynamics. The link_type function allows the user to pass in what link key value should link agents together. The link_type can then be further specified with the link_value criteria. The link_value can either be a string to further classify the type of link, for example *family: friendly* or *family: angry_teenager* or it can be a value such as will be seen in the SugarScape model *trades: 4* (number of trade between agents). As net_schedule is an additive process the value is assumed to be a threshold of greater than or equal to a value. The network can then be updated and evaluated through the other processes in the ABM using NeworkX object manipulation functions. For convenience, ML_Mesa also has ML_Mesa.add_links and ML_Mesa.remove_links functions. These functions take a list of agents, combines them in to a list of fully connected tuples and then adds the edges to graph.    

#### Network Defined Dissolution: ML_Mesa.reassess_net_schedule

The ML_Mesa.reassess_net_schedule uses the same taxonomy of options as ML_Mesa.net_schedule. First, an agent can be removed based on the presence of a link, the presence of a specific link type and finally the presence of a specific link value. The function will also check to ensure the meta-agent still has the minimum number of agents to remain a meta-agent which is defaulted to two with ML_Mesa.min_for_meta attribute. 

**Network Dissolution Function**
    ```
    def reassess_net_schedule(self, link_type = None, link_value = None)
    ```

The dissolution function similar to the formation function requires no parameters and will default to determining if there is a link or not. The user can also specify link types which cause agents to be removed or link values, which can again be either strings or numbers. However, as this function is not additive, if the value is a number it must be less than or equal to the given value. 

#### Schedule Functions

As ML_Mesa replaces the normal schedule function of Mesa, it must also have the basic scheduling functions. These are the add and remove functions, which remain at the individual agent level but have a higher degree of complexity as agents must be kept in multiple managers to ensure agents they are being properly 'stepped' in the schedule or removed if the agent 'dies'. ML_ Mesa also replaces Mesa's step function. Its primary schedule is random activation, but this can be turned off for an ordered activation and a staged activation can be executed through the agent_type manager. A future extension of ML_Mesa would be to store different schedules based on different network configurations. This would save computation time so specific agent schedules would be created less often. For example, if one was recreating daily life of a population and the night and morning hours used one configuration, while the daytime hours would use a different configuration, each calling different behavior routines for the agents. 

**Schedule Functions**
    ```
    def add(self, agent, schedule = True, net = True)

    def remove(self, agent):

    def step(self, shuffled = True, by_type = False, const_update = False)
    ```

Similar to Mesa, the add function requires an agent object. It also has two keyword parameters which take boolean parameters each with a default value of *True*. Keyword parameter *schedule* adds the agent to the schedule. This is an option in case the user begins with a complex network and the agent is already part of a meta-agent. The *net* parameter similarly adds the agent to the network. This is done in case the user has agent he or she does not want to be part of the network. For instance, in a SugarScape model, the grid cells may not need to be a part of the network as what is of concern is the agents network. The remove function requires an agent object. If invoked this will remove the agent from all managers as applicable. The step function works in a similar way to the Mesa step function, where it iterates through each agent in schedule and executes their step function. Random activation is the default as identified by the keyword parameter *shuffled.* If shuffled is false it will follow the order in the ordered dictionary. The keyword parameter *by_type* is set to False but can take a list of agent types to simulate staged activation. Constant update provides the ability to have a group of agent types be activated after the more dynamic schedule. For example, an environmental variable which changes at a steady rate for each time step, such as sugar or spice growth in the SugarScape model. 

### The MetaAgent Class

The MetaAgent class introduces hierarchy into the ABM. The MetaAgent class performs similar functions to ML Mesa or Mesa's time module. MetaAgents has three managers, which includes a dictionary of the agents which belong to the MetaAgent, a dictionary of dictionaries with the agents in the meta-agent by type and a NetworkX graph object of the sub_agents. The MetaAgent then has three attributes to make it easy for users to employ the MetaAgent. The first attribute is MetAgent.active which is a boolean value to help users activate and deactivate MetaAgents as necessary. The next two attributes are MetaAgent.type and MetaAgent.__str__ which both equal "meta" and allow the user greater ease in identifying and performing functions on the meta-agents. The final attribute of the MetaAgent class is its policy object, this object is passed in by the user and provides the meta-agents behavior. The behavior of the meta-agents and its internal agents is done with two step functions the MetaAgent.meta_step which calls the policy function and the individual agent step functions, again using a random order, but with the same options of the ML_Mesa.step function to dictate schedule ordering processes.   

The interaction of the schedule, formation and dissolution of modules of agents, and the ability for hierarchies to exist within allows ML Mesa to introduce modules and hierarchies of agents and a key dynamic of complex systems. The functions can be employed as part of the normal step function, at specific events or at specific intervals. By using a network data structure as the main management structure, ML Mesa is able to integrate the interdependencies and changing dynamics of those interdependencies into ABM management structure providing a new dynamic which goes beyond the current multi-level approaches.     

## Happy Modeling!





    
