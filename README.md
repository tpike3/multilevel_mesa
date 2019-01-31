# Multi-Level Mesa

Multi-Level (ML) Mesa is a library which supports Python's Agent Based Modeling Library Mesa. ML Mesa's views complex systems as adaptive networks and uses a network graph structure to allow dynamic management of agent modules (groups) and model schedules.

ML Mesa has three main components. First, a collection of managers which tracks the agents, the modules of agents (groups), the network of agents, and agents who belong to an existing group, and the schedule. Second, a series of functions which provides the user different options to form groups or dissolve them. Third, a group class which allows for the inclusion of different policies, manages the behavior and status of the group, and implicitly produces hierarchies within the complex system. (Figure 1)

![ML Mesa Schematic](https://github.com/tpike3/ml_mesa/blob/master/ml_mesa/picture/ML-Mesa%20Schematic.png)
**Figure 1**

## Requirements

ML Mesa requires

    Mesa>=0.8.4
    NetworkX>=2.2  

## Installation 

    pip install ml_mesa

### Creating an ML Mesa Instance and the ML Mesa Managers

Creating an instance of ML Mesa requires no parameters, and initiates one attribute and six managers. 

Attribute: 
1. ML_Mesa.id_counter, provides a unique_id for each group

Keyword parameters:
1. ML_Mesa.min_for_group tells the instance the minimum number of agents which must be in a group. The min_for_group parameter has a default setting of 2. 
2. ML_Mesa.group_net takes a Boolean and is defaulted to False. This parameter tells the instance whether or not a group agent can form a larger group agent with other group agents. 

Six Managers: 

1. ML_Mesa.\_agents which is an ordered dictionary (a hash-table consisting of a key:value pair) that holds every agent added to the instance
2. ML_Mesa.net is an instance of a NewtorkX graph. This feature provides the critical structure for tracking and managing agents and groups.
3. ML_Mesa.agents_by_type uses a dictionary of dictionaries to track agents by type. This feature allows for faster reference of specific types of agents when manipulating groups or schedules.
4. ML_Mesa.schedule replaces the Mesa schedule and is an ordered dictionary which manages the agents and when they execute a step function. 
5. ML_Mesa.groups is an ordered dictionary and tracks the groups within the model performing the same function of tracking groups as the agents ordered dictionary.
6. ML_Mesa.reverse_groups is a dictionary of dictionaries of sets. The first dictionary key is the agent id, while the second is group types (link and link values) and the set is the group ids to which the agent belongs in those group types.  

### The ML Mesa Functions

As shown in figure 1, ML Mesa has two primary approaches for facilitating a multi-level ABM, an explicit approach and a network approach. Within these two approaches, ML Mesa turns the desired agents into a bilateral link list which form the groups. Each input of agents is transformed into a network edge which forms the groups or adds agents to an existing group. The use of links is also used to disband groups or remove agents from the group. These functions then create a more dynamic schedule with modules of agent within hierarchies. 

#### Forming and Dissolving Meta-Agents

##### User Defined Formation Process ML_Mesa.form_meta

The formation function of the explicit approach is ML_Mesa.form_group and takes a user defined process which must generate a list of bilaterally connected agents (Box 3-2). This approach can be computationally expensive, but is necessary to allow for the accurate recreation of the network. As dictionaries (e.g. the schedule) cannot be manipulated during iteration users must use a yield versus the more common return operator to pass the list of agents to the ML_Mesa.form_group function. 

##### User-Defined Formation Function: ML_Mesa.form_group

    ```
    def form_group(self, process, *args, determine_id = 'default', double = False,\
        policy = None, group_type = None,  **kwargs):
    ```

The ML_Mesa.form_group function requires one parameter which is the user specified process which determines whether or not an agent should be in a group with other agents. The \*args and \*\*kwargs allows the user to pass in the parameters for this process. The determine_id parameters ensures each group gets a unique id. If default it will simply append a number based on the id_counter attribute to the string 'group'. For the user to pass in an id he or she must yield the id as the first element of a tuple generated from the yield operator from the user defined process. Users must choose this id carefully as the id is used in the set operations to merge groups. The double parameter takes a Boolean value and is defaulted to False. If True the agent will remain in the schedule as an independent entity and be added as part of the group, while if False the agent is removed. This feature is to provide users maximum flexibility for agent scheduling and group processes. The policy parameter passes in the step processes for the group, which can consist of only internal processes or can consist of group processes and then execute the individual agent processes.  The group_type parameter takes a string and allows the user to specify different types of groups so an agent can belong to different types of group such as ‘family’ and ‘firm’.     

##### User Defined Dissolution Process: ML_Mesa.reassess_group

The dissolution function for the explicit approach (although it can be used interchangeably with the network approach) is ML_Mesa.reassess_group. This function iterates through each group and then uses the user defined process to assess whether or not an agent should still belong to the group. Similar to the ML_Mesa.form_group this function requires a yield to provide the list of agents which should be removed and then proceeds to remove those agents while updating the appropriate managers. This function also ensures if the group fails to have a certain number of agents within the group that the group will be removed. This minimum number of agents is the min_for_group attribute of the ML Mesa instance and has a default setting of two

##### User-Defined Dissolution Function

    ```
    def reassess_group(self, process, *args, reintroduce = True, group_type = None, **kwargs):
    ```

The ML_Mesa.reassess_meta function requires one parameter, which is the process defined by the user for assessing whether or not the agent should remain within the group. The function also has a reintroduce parameter which takes a Boolean value and is defaulted to True. This parameter tells the function whether or not to reintroduce the removed agents back into the schedule.  


##### Network Defined Formation: ML_Mesa.net_group

The formation function of the network approach is ML_Mesa.net_group and uses an undirected NetworkX graph object to assess what agents should form groups. With an undirected graph and as indicated in the above figure, there are three possibilities for assessing whether or not linked agents should be in the same group. First, by whether or not a link exists between the agents. Second, if a specific type of link exists (e.g. friend, enemy). Third, if a link exists which has reached a certain value. 

##### Network Formation Function

    ``` 
    def net_group(self, link_type = None, link_value = None, double = False, policy = None, group_to_net = False):
    ```

The ML_Mesa.net_group function requires no parameters and will default to whether or not a link exists or not between agents. As the net_group function has no process passed in there is no way to specify a group id, the function uses the default "group" if groups are forming based on the presence of a link, the link_type is not the default None or the link_type_link_value, plus a number from the ML_Mesa.id_counter attribute. If users decided they would like to pass in processes to provide a unique id for groups this could be added in future versions, but was not included in this version as it did not add anything substantive to the ML Mesa dynamics. The link_type function allows the user to pass in what link key value should link agents together. The link_type can then be further specified with the link_value criteria. These values are also used as the dictionary keys in the ML_Mesa.reverse_groups manager. The link_value can either be a string to further classify the type of link, for example family: friendly or family: angry_teenager or it can be a value such as trades: 10 (number of trades between agents), which in this case tracks a type of interaction between agents. As net_group is an additive process the value is assumed to be a threshold of greater than or equal to a value. The network can then be updated and evaluated through the other processes in the ABM using NetworkX object manipulation functions. For convenience, ML_Mesa also has ML_Mesa.add_links and ML_Mesa.remove_links functions. These functions take a list of agents, combines them in to a list of fully connected tuples and then adds or removes the links.    

#### Network Defined Dissolution: ML_Mesa.reassess_net_group

The ML_Mesa.reassess_net_group (Box 3-5) uses the same taxonomy of options as ML_Mesa.net_group. First, an agent can be removed based on the presence of a link, the presence of a specific link type and finally the presence of a specific link value. The function will also check to ensure the meta-agent still has the minimum number of agents to remain a group which is defaulted to two with the ML_Mesa.min_for_group attribute. 

##### Network Dissolution Function

    ```
    def reassess_net_group(self, link_type = None, link_value = None)
    ```

The dissolution function similar to the formation function requires no parameters and will default to determining if there is a link or not. The user can also specify link types which cause agents to be removed or link values, which can again be either strings or numbers. However, as this function is not additive, if the value is a number it must be less than or equal to the given value. 

#### Schedule Functions

As ML_Mesa replaces the normal schedule function of Mesa, it must also have the basic scheduling functions. These are the add and remove functions, which remain at the individual agent level but have a higher degree of complexity as agents must be kept in multiple managers to ensure agents are being properly 'stepped' in the schedule or removed if the agent 'dies'. ML Mesa also replaces Mesa's step function. Its primary schedule is random activation, but this can be turned off for an ordered activation and a staged activation can be executed through the agent_type manager. A future extension of ML_Mesa would be to store different schedules based on different network configurations. This would save computation time so specific agent schedules would be created less often. For example, if one was recreating daily life of a population and the night and morning hours used one configuration, while the daytime hours would use a different configuration, each calling different behavior routines for the agents. 

##### Schedule Functions

    ```
    def add(self, agent, schedule = True, net = True)
    def remove(self, agent):
    def step(self, shuffled = True, by_type = False, const_update = False)
    ```

Similar to Mesa, the ML_Mesa.add function requires an agent object. It also has two keyword parameters which take Boolean parameters each with a default value of True. Keyword parameter schedule adds the agent to the schedule. This is an option in case the user begins with a complex network and the agent is already part of a group. The net parameter similarly adds the agent to the NetworkX object. This is done in case the user has an agent he or she does not want to be part of the network. The ML.Mesa.remove function requires an agent object. If invoked this will remove the agent from all managers as applicable. The ML_Mesa.step function works in a similar way to the Mesa step function, where it iterates through each agent in schedule and executes their step function. Random activation is the default as identified by the keyword parameter shuffled. If shuffled is False it will follow the order in the ordered dictionary (the order the agents were added). The keyword parameter by_type is set to False but can take a list of agent types to simulate staged activation. Constant update provides the ability to have specific agent types activated after the more dynamic schedule. For example, an environmental variable which changes at a steady rate for each time step.  

### The MetaAgent Class

The Group class introduces hierarchy into the ABM. The Group class performs similar functions to ML Mesa or Mesa's time module. The Group class has three managers, which includes a dictionary of the agents which belong to the Group, a dictionary of dictionaries with the agents in the Group by type and a NetworkX graph object of the sub_agents. The Group then has three attributes to make it easier for users to employ the Group. The first attribute is Group.active which is a Boolean value to help users activate and deactivate Groups as necessary. The next two attributes are Group.type and Group.__str__ which both equal "group" and allow the user greater ease in identifying and performing functions on the groups. The final attribute of the Group is its policy object, this object is passed in by the user and provides the Group behavior. The behavior of the Groups and its internal agents is done with two step functions the Group.group_step which calls the policy function and the individual agent step functions, again using a random order, but with the same options of the ML_Mesa.step function to dictate schedule ordering processes. 

Attributes: 
1. Group.sub_agents = dictionary
2. Group.agents_by_type = dictionary   
3. Group.net = NetworkX graph 
4. Group.policy = object of group policies
5. Group.active = status of Group

Main Functions:
1. Group.meta_step() = policies to dictate sub_agent behavior
2. Group.step() = sub_agent behaviors 

The interaction of the schedule, formation and dissolution of modules of agents, and the ability for hierarchies to exist allows for the easier introduction of these key features of complex systems. The functions can be employed as part of the normal step function, at specific events or at specific intervals. By using a network data structure as the main management structure, ML Mesa is able to integrate the interdependencies and changing dynamics of those interdependencies into ABM management structure providing a new dynamic which goes beyond the current multi-level approaches.     

## Happy Modeling!





    
