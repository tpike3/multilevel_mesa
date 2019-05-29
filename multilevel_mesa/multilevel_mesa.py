# -*- coding: utf-8 -*-
"""
Created on Thu Nov 15 13:48:44 2018

ML Mesa Module

Purpose: To provide the management overhead for agent based models which 
consists of several modules and heirarchies of agents

Concept: 
    ML_Mesa provides two options for ML Mesa. First, an explicit approach. 
In this approach the user defines what process should occur and when agents 
group together and reassess if the should stay together. Second, a network
which defines what entwork attirbutes should cause and agent to group together. 

Each function has a description of what is does as well as embedded comments. 
The main areas for the ML_Mesa Class are: 
    
    --Granular agent functions (line 70)
        -- add
        -- remove
    --Explicit approach (line 422 )
        -- form_group
        --reassess_group
    --Core functions- steps and buffers (line 278)
        --const_buffer
        --group_buffer
        --step
    --Network based approach (line 671)
        --net schedule with 3 options
            1- link
            2- link type
            3- link attribute
        --add_link
        --remove_link
"""

from collections import OrderedDict, defaultdict
import networkx as nx
from mesa.time import RandomActivation
import itertools

class MultiLevel_Mesa(RandomActivation):
    
    def __init__(self, model, min_for_group = 2, group_to_net = False):
        super().__init__(model)
        #Maintains master dictionary of all agents in model
        self._agents = OrderedDict()
        #Maintains master network of all agents in model
        self.net = nx.Graph()
        #Provides view of agents by type
        self.agents_by_type = defaultdict(dict)
        #Dictionary of agents who are active for each time step
        self.schedule = OrderedDict()
        #Minimum number of agent to eleminate a group agent
        self.min = min_for_group
        #Counter for Group Agent tracking
        self.id_counter = 0
        #Attribute for making hierarchies
        self.group_net = group_to_net
        #Ordered dictionary of group agents
        self.groups = OrderedDict()
        #Reverse dictionary of Agents to Groups by linktype to which they belong
        self.reverse_groups = defaultdict(lambda: defaultdict(set))
        
    @property
    def agent_count(self):
        '''
        Acts as an attribute of ML_Mesa Class
        Provides number of agents by agent type
        '''
        agents =[]
        for k,v in self.agents_by_type.items(): 
            agents.append((k, len(v)))
        return agents
    
    @property
    def active_agent_count(self):
        '''
        Acts as an attribute of ML_Mesa Class
        Provides number of group agents in the schedule
        '''
        return len(self.schedule.keys())
    
    def get_agent_group(self, agent, link_type):
        '''
        Function to make easier for users to get agent group
        
        '''
        
        group = None        
        
        for item in self.reverse_groups[agent.unique_id][link_type]:
            group = self.groups[item]
            break
                        
        return group
    
    ##########################################
    #
    #  Granular Agent Functions
    #
    #########################################
       
    
    def add(self, agent, schedule = True, net = True): 
        '''
        Params: 
            agent - single granular agent object
            Schedule - if True will add the agent to the schedule
        
        Adds agents to: 
            - Master agent OrderedDict (self._agents)
            - Master agent network (self.net)
            - Master agents by type Dict (self.agents_by_type)        
        '''
        
        self._agents[agent.unique_id] = agent
        agent_type = type(agent)
        self.agents_by_type[agent_type][agent.unique_id] = agent
        
        if net: 
            self.net.add_node(agent) 
        ##Will change initial test
        
        if schedule: 
            self.schedule[agent.unique_id] = agent

    ###########################################################
    #
    #       Remove Functions with helper with and without
    #       recursion
    #
    ##########################################################
            
    def _remove_groups_recursion(self, m, group_type):
        '''
        Params: 
            Group Agent and Group Type, identify where in the reverse group 
            dictionary the Group agents are
            
        Purpose: Provides a recursive function to remove hierarchies of group
        agents
        
        Helper Function for _cache_remove
        
        Removes agent from: 
            - Master agent list (self._agents)
            - Master agent network (self.net)
            - Master agents by type Dict (self.agents_by_type)
            - Schedule
            - Reverse Groups
        '''
        
        if m in self.schedule.keys():
            #remove from schedule
            del self.schedule[m]
        
        #remove group agent from all reverse_groups
        for group_dicts in self.reverse_groups.values():
            group_dicts[group_type].discard(m)
        
        #is group part of larger group
        if m in self.reverse_groups.keys():
            #identify super group
            super_group = self.reverse_groups[m]
            for group_agents in super_group.values():
                #produces a lists of sets of groups
                for group in self.set_buffer(group_agents): 
                    super_status, group_remove = self.groups[group].remove(m, self.min) 
                    if super_status != None: 
                        #remove super_group
                        self._remove_groups_recursion(group,group_remove)
                    
        #remove from master groups
        del self.groups[m]
        #remove node is exists
        if m in self.net:
            self.net.remove_node(m)
    
    
    def _cache_remove(self, agent): 
        
        '''
        Params:
            agent - single granular agent object
        
        Supported by _remove_groups_recursion
        
        Removes agent from: 
            - Master agent list (self._agents)
            - Master agent network (self.net)
            - Master agents by type Dict (self.agents_by_type)
            - Schedule
            - Reverse Groups
        '''
        del self._agents[agent.unique_id]
        agent_class = type(agent)
        del self.agents_by_type[agent_class][agent.unique_id]
        self.net.remove_node(agent)
        
        if agent.unique_id in self.reverse_groups.keys():
            _groups = []
            #convert groups to which agent belongs to list
            for group_type in self.reverse_groups[agent.unique_id].keys():
                _groups += list(self.reverse_groups[agent.unique_id][group_type])
                
            #delete agent from reverse_group
            del self.reverse_groups[agent.unique_id]
            for m in _groups: 
                if m in self.groups.keys():
                    if agent.unique_id in self.groups[m].sub_agents.keys():
                        #remove agent from group_agent
                        group_status, group_type = self.groups[m].remove(agent.unique_id, self.min)
                        #if agent dies
                        if group_status != None:
                            #Helper function to deal with groups within groups
                            self._remove_groups_recursion(m, group_type)
             
        if agent.unique_id in self.schedule.keys(): 
            del self.schedule[agent.unique_id] 
        #self._remove_groups_recursion.cache_clear()
        
    
    def _remove(self, agent):
        '''
        Non recursive verion of remove, allows for faster processing,
        if group can't become agent
        
        Parameter: Agent object
        
        Removes agent from: 
            - Master agent list (self._agents)
            - Master agent network (self.net)
            - Master agents by type Dict (self.agents_by_type)
            - Schedule
            - Reverse Groups        
        
        '''
        
        del self._agents[agent.unique_id]
        agent_class = type(agent)
        del self.agents_by_type[agent_class][agent.unique_id]
        self.net.remove_node(agent)
        
        if agent.unique_id in self.reverse_groups.keys():
            _groups = []
            
            #convert groups to which agent belongs to list
            for group_type in self.reverse_groups[agent.unique_id].keys():
               _groups += list(self.reverse_groups[agent.unique_id][group_type])
                        
            #delete agent form reverse_groups
            del self.reverse_groups[agent.unique_id]
            for m in _groups: 
                if m in self.groups.keys():
                    if agent.unique_id in self.groups[m].sub_agents.keys():
                        #remove agent form group_agent
                        group_status, group_type = self.groups[m].remove(agent.unique_id, self.min)
                        #if agent dies
                        if group_status != None:
                            if m in self.schedule.keys():
                                #remove fsom schedule
                                del self.schedule[m]
                            #remove group agent from all reverse_groups
                            #get list of sub_agents in mets
                            subs = list(self.groups[m].sub_agents.values())
                            #iterate through subs
                            for a in subs: 
                                #get all associated links
                                 self.reverse_groups[a][group_type].discard(m)
                            #remove from master group
                            del self.groups[m]
                            #remove node is exists
                            if m in self.net:
                                self.net.remove_node(m)
        
        if agent.unique_id in self.schedule.keys(): 
            del self.schedule[agent.unique_id] 
  
    
    def remove(self, agent):
        
        '''
        User removable function select between recursive or non recursive 
        versions
        
        Parameters: Agent or GroupAgent object
        
        Removes agent from: 
            - Master agent list (self._agents)
            - Master agent network (self.net)
            - Master agents by type Dict (self.agents_by_type)
            - Schedule
            - Reverse Groups        
        
        '''
        #calls non-recusursive function
        if self.group_net == False: 
            self._remove(agent)
        
        #call recursive function    
        else: 
            self._cache_remove(agent)
                
    ########################################################################
    #
    #                  Group Helper Function
    #
    ########################################################################
    
    def group_iterate(self, groups, determine_id, double, policy, group_net, \
                     link_type):
        '''
        Main Function of ML Mesa
        
        Parameters: 
            groups = list of bilateral links to for Group
            determine_id: parameter to pass in unique_id for group agent
            double: True of False- remove agent from schedule
            policy: object of group policies toward agents
            group_net: whether group can form more hierarchies
            link_type: type of link category to which group belongs
            
        Purpose: Form group agent, biased to first come first serve. Granular
        agents join existing groups
                
        '''
        
        for edge in groups:
            #create empty dictionary for sub_agents of specific link
            group2_dict = {}
            #identify if the agents are part of common group
            group_intersect = \
            self.reverse_groups[edge[0].unique_id][link_type].intersection\
            (self.reverse_groups[edge[1].unique_id][link_type])
            #identify if the agents are part of the specified common group type
            if group_intersect == set(): #no intersection
               #neither are part of a group and will create their own
               if  self.reverse_groups[edge[0].unique_id][link_type] == set() and \
               self.reverse_groups[edge[1].unique_id][link_type] == set(): #not part of group_agent
                   # create new Id
                   if determine_id == 'default': 
                       unique_id =  "group"+str(self.id_counter)
                       self.id_counter += 1
                   #determine_id converted to string in net_group function
                   elif str(link_type) in determine_id:
                       unique_id =  determine_id +"_"+str(self.id_counter)
                       self.id_counter += 1
                   else: 
                       unique_id = determine_id
                   #create new group agent        
                   group2_dict = {unique_id: dict((x.unique_id, x) for x in edge)}
                   
                   ma = GroupAgent(unique_id, self.model, self._agents,\
                          group2_dict[unique_id], self.reverse_groups, self.min, \
                          policy, link_type)
                   ma.form_graph(edge)
                   # add to schedule
                   self.schedule[ma.unique_id] = ma
                   #add to management structures
                   #Groups ordereddict
                   self.groups[ma.unique_id] = ma
                   #reverse_groups references
                   self.reverse_groups[edge[0].unique_id][link_type].add(ma.unique_id)
                   self.reverse_groups[edge[1].unique_id][link_type].add(ma.unique_id)
                   #network if not there
                   if self.net.has_edge(edge[0], edge[1]) == False:
                       self.add_link([edge])
                   #remove from schedule
                   if double == False: 
                       if edge[0].unique_id in self.schedule.keys():
                               del self.schedule[edge[0].unique_id]
                       if edge[1].unique_id in self.schedule.keys(): 
                               del self.schedule[edge[1].unique_id]
                   if group_net == True: 
                       self.net.add_node(ma)
               #one is part of a group_agent so the other will join
               elif self.reverse_groups[edge[0].unique_id][link_type] == set() or \
               self.reverse_groups[edge[1].unique_id][link_type] == set():  
                  if self.reverse_groups[edge[0].unique_id][link_type] == set():
                      #get the group_agent
                      for agent in self.reverse_groups[edge[1].unique_id][link_type]:
                          group_a = agent
                          break
                
                      self.groups[group_a].add([edge[0]]) #GroupAgent add function
                     
                      #add to reverse
                      self.reverse_groups[edge[0].unique_id][link_type].add(group_a) #set add function
                      #add to network
                      self.add_link([edge])
                      #delete from schedule
                      if double == False: 
                        if edge[0].unique_id in self.schedule.keys():
                                del self.schedule[edge[0].unique_id]
                  else: 
                      for agent in self.reverse_groups[edge[0].unique_id][link_type]:
                          group_a = agent
                          break
                      
                      self.groups[group_a].add([edge[1]]) #GroupAgent add function
                      
                      #add to reverse
                      self.reverse_groups[edge[1].unique_id][link_type].add(group_a) #set add function 
                      #add to network
                      self.add_link([edge])
                      #delete from schedule
                      if double == False: 
                        if edge[1].unique_id in self.schedule.keys(): 
                                del self.schedule[edge[1].unique_id]
               #both are part of a group_agent and so will maintain a link
               else: 
                  #make sure there is a link between agents
                  self.add_link([edge])
            #both are part of the same groupagent
            else: 
                pass

    
    #########################################################################
    #
    #         Explicit Approach - User Directed GroupAgent Creation
    #
    ########################################################################    
    
    def group_remove(self, agents):
        '''
        Helper function for form_group
        
        Concept:
            Groups agents who should form a group together in a list os tuples
            Checks to ensure agent is still alive   
        '''
        for agent in agents[:]:
           if agent not in self._agents.values():
                agents.remove(agent)
        
        if len(agents) <2:
            return None
        #make tuples
        #1st agents
        main = [agents[0]]
        agents = agents[1:]
        main = main*len(agents)
        edges = list(zip(main, agents))
    
        return edges
    
    def form_group(self, process, *args, determine_id = 'default', \
                      double = False, policy = None, group_type = None,\
                      **kwargs):
        '''
        Concept: Function works with a user defined process to take in lists of 
        agents who should be grouped together and runs them through the group_agent 
        process making sure they are still alive and not duplicating group_agents
        
        Helper function: group_remove(self) checks to see if agent is still 
        alive
        
        Params: 
            process (required) -- YIELDs list of agents who should be grouped
            together and if ID not default and ID
            args = arguments for user defined process
            determine_id = default means the package will give an id
            double = True or False if agents should be stepped twice during 
            process
            policy = pass in group_agent policy
            
        Critical Dynamics: 
            process must YIELD agent group
            process must return list of agent objects, with first agent being
            the linked to all others
        
        '''

       
        for result in process(*args, **kwargs): 
            if type(result) != tuple:
                #remove dead agents if any    
                edges = self.group_remove(result)
                if edges != None: 
                    #create group_agents
                    self.group_iterate(edges, determine_id, double, policy, 
                                      self.group_net, link_type = group_type)
            else: 
                edges= self.group_remove(result[1])
                #create group_agents
                if edges != None: 
                    #create group_agents
                    self.group_iterate(edges, result[0], double, policy, \
                                      self.group_net, link_type = group_type)
         
            
                   
   
    def reassess_group(self, process, reintroduce = True, group_type = None, **kwargs):
        
        '''
        Purpose: Examine a group agent to remove or add agents and delete if 
        empty
        
        Params: 
            processs - function to assess whether agents should be in same 
                       module
            args - arguments for process function
            shuffled - True or False; do agents need to be in random order
            min_for_group - one more than the smallest number of subagents 
            before a groupagent is deleted
            
        Critical Dynamics: 
            - process must return 2 agents who are no longer linked
            - group-agents then receives list of agents to remove
            - if group-agent has no subagents it is removed from schedule
        
        '''
                
        for group_agent in self.reassess_buffer(): 
            
            #master list of agents to remove
            subs_to_remove = []
             
            #must receive list of tuples of connected agents
            peel_list = process(group_agent, **kwargs)
            if peel_list != None: 
                 #allows process output to be two agents or 
                 #tuple of two agents
                 if len(peel_list) == 2: 
                     edges = tuple(peel_list)
                     
                     self.net.remove_edge(self._agents[edges[0].unique_id],\
                                             self._agents[edges[1].unique_id])
                     #Remove from reverse_group, uses set remove function
                     
                     
                     self.reverse_groups[edges[0].unique_id][group_type].remove(group_agent.unique_id)
                     self.reverse_groups[edges[1].unique_id][group_type].remove(group_agent.unique_id)
                 elif len(peel_list) > 2: 
                     #Be Default all agents in a group_agent should be
                     #connected
                     edges = list(itertools.combinations(peel_list, 2))
                     self.net.remove_edges_from(edges)
                     for edge in edges: 
                         self.reverse_groups[edges[0].unique_id].remove(group_agent.unique_id)
                         self.reverse_groups[edges[1].unique_id].remove(group_agent.unique_id)       
                 else: 
                     raise Exception("Removing subagents from a group", \
                                     "requires either 2 agents ", 
                                     "or a list of agents. ",)
                    
                 #remove buffer is based on agent id, convert agent list
                 # to agent ID
                 for each in peel_list: 
                     subs_to_remove.append(each.unique_id)

            #function to add independent agent back in 
            if reintroduce == True and peel_list != None: 
                for agent in peel_list: 
                    self.add(agent, schedule = True)
            
            # call function to remove groupagents if necessary
            group_status, group_type = group_agent.remove(subs_to_remove, self.min)
            #Remove group-agents with no sub_agents
            if group_status != None: 
                #remove from schedule
                if group_agent.unique_id in self.schedule.keys(): 
                    del self.schedule[group_agent.unique_id]
                del self.groups[group_agent.unique_id]
                #iterate through subs
                for a in subs_to_remove: 
                   self.reverse_groups[a][group_type].discard(group_agent.unique_id)
            
        
    #########################################################
    #
    #    Core Functions - Step and Buffer
    #
    #########################################################    
    
    def set_buffer(self, groups):
        '''
        Helper buffer for _cache_remove_recursion
        
        Allows it to iterate over the set of reverse_group to remove
        agents
        '''       
        
        set_groups = list(groups)
        
        for g in set_groups: 
            yield g
    
    def reassess_buffer(self):
        '''
        Helper function for reassess functions to manipulate groups dictionary
        '''
                
        group_keys = list(self.groups.keys())
    
        for key in group_keys: 
            yield self.groups[key]
    
    def const_buffer(self, agent_type):
        '''
        Purpose: Buffer to update agents who are updated each step
        occurs after the step function of all the other agents
        
        Params: agent_type identfies which agent should be updated
        
        '''
        const_ids = list(self.agents_by_type[agent_type].keys())

        for agent in const_ids: 
            if agent in self._agents.keys():
                  yield self._agents[agent]    
                
    
    def group_buffer(self, shuffled):
        '''
        Purpose: Buffer for main agents to prevent issues of data structure
        changing during execution
        
        Params: Shuffled - changes order of execution to mitigate mover 
        advantages
        '''
                
        group_keys = list(self.schedule.keys())
              
        if shuffled: 
            self.model.random.shuffle(group_keys)
        
        for key in group_keys: 
            if key in self.schedule.keys(): 
                yield self.schedule[key]
    
    def step(self, shuffled = True, by_type = False, const_update = False):
        '''
        Purpose: Step function which executes agent step functions
        
        Params: 
            Shuffled: To randomize agent order
            by_type: whether or not agents should be executed in a type order
            const_update: whether agents are updated once per step regardless
        '''                
        
        for agent in self.group_buffer(shuffled):
            #currently a random activation nested within a random activation 
            if agent.type != 'group' and type(agent) != const_update: 
                agent.step()
            else: 
                if by_type == False: 
                    agent.group_step()
                else: 
                    #type is list of agents order
                    if const_update == False: 
                        agent.group_step(by_type)
                    else: 
                        agent.group_step(by_type, const_update)
                
        if const_update != False: 
            for agent in self.const_buffer(const_update):
                agent.step()
        
        
    ######################################################################
    #
    #         Networked Based Group-Agent Creation
    #
    ######################################################################
    
    def net_group(self, link_type = None,link_value = None, \
                     double = False, policy = None):
        '''
        Concept: Updates schedule specified by link data either type of 
        connection or value
        
        Params: 
          - link_type - activates network with a link that has a specific
                       attribute
          - link_value - activates network with a value of a specific attribute 
          
        '''
        
        if link_type != None: 
            if link_value == None: 
                _groups = []
                for edge in self.net.edges.data(link_type): 
                    _groups.append((edge[0], edge[1]))
                determine_id = str(link_type)

            else: 
                _groups = []
                for edge in self.net.edges.data(link_type): 
                    if type(link_value) == str:
                        if edge[2] == link_value:
                            _groups.append((edge[0], edge[1]))
                    elif edge[2] >= link_value: 
                        _groups.append((edge[0], edge[1]))
                determine_id = str(link_type)+"_"+str(link_value)        
                    
           
            self.group_iterate(_groups, determine_id, double= double,\
                              policy = policy, group_net = self.group_net,\
                              link_type = link_type)
            
        
        else: 
            # Add all linked nodes to schedule
            _groups = list(self.net.edges())
            self.group_iterate(_groups, determine_id = "default", double= double,\
                              policy = policy, group_net = self.group_net, \
                              link_type = link_type)
            #active_list = []
            #for group in groups: 
                
        
    def reassess_net_group(self, link_type = None,\
                 link_value = None,):
        '''
        Concept: Updates group specified by link data either type of 
        connection or value
        
        Params: 
          - link_type - activates network with a link that has a specific
                       attribute
          - link_value - activates network with a value of a specific attribute 
          
        '''
        
        #remove groups who are no longer linked
        if link_type != None: 
            if link_value == None: 
                group_type = str(link_type)
            else: 
                group_type = str(link_type)+"_"+str(link_value)
        else:
            group_type = link_type
        
        for group_agent in self.reassess_buffer(): 
            for link in group_agent.edge_buffer(link_type, link_value):
                if self.net.has_edge(link[0], link[1])== False:
                    #remove from reverse group dictionary
                    self.reverse_groups[link[0].unique_id][group_type].remove(group_agent.unique_id)
                    self.reverse_groups[link[1].unique_id][group_type].remove(group_agent.unique_id)
                    #see if group agent should still exist
                    group_status, group_type2 = group_agent.remove([link[0].unique_id, link[1].unique_id], self.min)
                                        
                    #Remove group-agents with no sub_agents
                    if group_status != None: 
                        #add individual agent back in schedule
                        for agent in link:
                            if agent in self._agents.values():
                                self.add(agent, schedule = True)
                        #remove from schedule
                        if group_agent.unique_id in self.schedule.keys():
                            del self.schedule[group_agent.unique_id]
                        #remove from group dictionary
                        del self.groups[group_agent.unique_id]
                        #iterate through subs and remove from reverse group
                        for a in link: 
                           self.reverse_groups[a][group_type].discard(group_agent.unique_id)
                        
                 
    #TODO make easier to remove based on key, add buffer?
    def add_link(self, agents):     
        '''
        Add links to master networks based on agent initiation
        
        Params: 
            agents - list of agent objects
        
        '''
        
        if len(agents) > 2: 
           agents = list(itertools.combinations(agents, 2))
        self.net.add_edges_from(agents)
        
    def remove_link(self, agents):
        '''      
        Remove links to master network based on agent initiatiation
        
        Params: 
            agents - list of agent objects
        '''
        
        if len(agents) > 2: 
            agents = list(itertools.combinations(agents, 2))
        self.net.remove_edges_from(agents)
        
            
###############################################################
#
#         GROUPAGENT CLASS
#
###################################################################
from mesa import Agent

class GroupAgent(Agent, MultiLevel_Mesa):
    '''
    GroupAgent
    
    Class which provides GroupAgents functions.
    This porvides the ability to manage the GroupAgents which form and bring in 
    group_agent functions
    
    There are two main area of functions
     Helper functions:
         -- make_types
         -- form_graph
         -- add
         -- remove
     Core functions: 
         -- agent_buffer
         -- remove_buffer
         -- agent_by_type_buffer
         -- group_step
         -- step
         --step_by_type
    '''
    
    def __init__(self, unique_id, model, agents, sub_agents, reverse_groups, \
                 min_for_group, policy = None, link_type = None, active = True):
        super().__init__(unique_id, model)
        self._agents = agents 
        self.reverse_groups = reverse_groups
        #sub_agents is dictionary {unique_id:agent_object}
        self.sub_agents =sub_agents
        self.subs_by_type = self.make_types(sub_agents)
        self.sub_net = nx.Graph()
        self.min_for_group = min_for_group
        self.policy = self.get_policy(policy)
        self.active = active
        self.group_type = link_type
        self.type = 'group'
        self.__str__ = 'group'
    
   
    def get_policy(self, policy):
       
       if policy == None: 
           return None
       else: 
           return policy()
    
   #######################################################################
   #
   #                   Helper Functions
   #
   ######################################################################
    
    def make_types(self, sub_agents):
        '''
        Purpose: Create a dictionary of agents by type
        
        Params: dictionary of sub_agents
        '''        
        
        by_type = defaultdict(dict)
        for k,v in sub_agents.items(): 
            by_type[type(v)][v.unique_id] = v
            
        return by_type
            
    
    def form_graph(self, links):
        '''
        Concept: Forms internal agent graph
        
        params: 
            links - list of pairwise agents for links
            
        '''
        
        nodes = list(self.sub_agents.values())
        self.sub_net.add_nodes_from(nodes)
        if type(links) == list:
            self.sub_net.add_edges_from(links)
        else: 
            self.sub_net.add_edge(links[0], links[1])
           
    def add(self, agents):
        '''
        Concept - Allows agent(s) to be added to existing group_agent
        
        Params: 
            agents - list of agent objects
        '''        
        for agent in agents: 
            if agent.unique_id not in self.sub_agents.keys(): 
                self.sub_agents[agent.unique_id] = agent
                self.sub_net.add_node(agent)
                self.subs_by_type[type(agent)][agent.unique_id] = agent
                self.reverse_groups[agent.unique_id][self.group_type].add(self.unique_id)
                for agents in self.sub_agents.values(): 
                    self.sub_net.add_edge(agent, agents)
                    
    
    def remove(self,subs_to_remove, min_for_group, reintroduce = True):
        '''
        Concept - Allows agents to be removed form existing group-agent
        
        Params: 
            - subs_to_remove list of agent objects
            - min_for_group -attribute of ML_Mesa class which determines
            how many agents for a minum agent default is 2
        '''       
        
        
        if type(subs_to_remove) != list: 
            subs_to_remove = [subs_to_remove]
        
        for key, agent in self.remove_buffer(subs_to_remove):
            
            del self.sub_agents[key]
            self.sub_net.remove_node(agent)
            del self.subs_by_type[type(agent)][agent.unique_id]
        
        if len(self.sub_agents.keys()) < min_for_group:
            #Place agent back in schedule
            if reintroduce == True: 
                for agent in self.sub_agents.values():
                    #Mkae sure agents are still alive
                    if agent.unique_id in self._agents.keys():
                        self.model.ml.schedule[agent.unique_id] = agent
                        self.reverse_groups[agent.unique_id][self.group_type].discard(self.unique_id)
            #must return group_type to get right dictionary in reverse_groups
            return "died", self.group_type
        else:         
            return None, None
    
       
    
    
    
    ######################################################################
    #
    #              Core Step functions and buffers of Sub_Agents
    #
    #######################################################################    
    
    def edge_buffer(self, link_type, link_value):
        '''
        Concept: Buffer to prevent error from network object manipulation
        
        Params: 
            shuffled - True or False
        '''      
        
        
        if link_type != None: 
            if link_value == None: 
                _groups = []
                for edge in self.sub_net.edges.data(link_type): 
                    _groups.append((edge[0], edge[1]))
            else: 
                _groups = []
                for edge in self.sub_net.edges.data(link_type): 
                    #for string qualifier
                    if edge[2] != link_value:
                            _groups.append((edge[0], edge[1]))
                    #for value qualifier
                    elif edge[2] <= link_value: 
                            _groups.append((edge[0], edge[1]))
        else: 
            _groups = list(self.sub_net.edges())               
        
        for edge in _groups: 
            yield edge
    
    
    def agent_buffer(self, shuffled=True):
        '''
        Concept: Buffer to prevent error from object manipulation
        
        Params: 
            shuffled - True or False
        '''        
        
        agent_keys = list(self.sub_agents.keys())   
        
        if shuffled: 
            self.model.random.shuffle(agent_keys)
        
        for key in agent_keys: 
            if key in self.sub_agents.keys(): 
                yield self.sub_agents[key]
        
    
    def remove_buffer(self, subs_to_remove):
        '''
        Concept - Buffer to prevent error from object manipulation
        
        Params: 
            subs_to_remove - lists of agent objects
        '''
                
        agent_keys = list(self.sub_agents.keys())
        
        
        for key in agent_keys:
            if key in self.sub_agents.keys() and key in subs_to_remove: 
                yield key, self.sub_agents[key] 
    
    
    def agent_by_type_buffer(self, agent_type, shuffled):
        '''
        Purpose: Buffer for sub agent execution by type
        
        params:
            agent_type: identifies agent_type to step
            shuffled: True = randomize order of agents
        '''
        
        
        agent_keys = list(self.subs_by_type[agent_type].keys())
                
        for key in agent_keys:
            yield self.sub_agents[key]
      
    
    def group_step(self, by_type = False, const_update = False):
        '''
        Purpose: Exectue step function of group-agent and subagents
        
        Params: 
            by_type: either False or [list] indicating type of agents to execute
            const_update: either False or agent type indicating agent 
            which is updated constantly
        '''
        
        if self.policy != None: 
             
            self.policy_step(self.policy)
            
        else: 
            if  by_type  == False: 
                self.step()
            else: 
                if const_update == False: 
                    for agent_type in by_type: 
                        self.step_by_type(agent_type)
                else: 
                    for agent_type in by_type: 
                        if agent_type == const_update: 
                            pass
                        else: 
                            self.step_by_type(agent_type)
     
    
    
    def policy_step(self, policy, shuffled = True):
        
         
        for agent in self.agent_buffer(shuffled):
            if hasattr(agent, "type") and agent.type == 'group':   
                agent.group_step()
            else:
                #necessary for agent ghost who have not yet been removed from
                #group_agent but still allive
                if len(self.sub_agents.values()) < self.min_for_group:
                    agent.step()
                else:                    
                    policy.step(agent)
            
        
    
    def step(self, shuffled=True):
        '''
        Concept: Step process for sub agents within active group agent
        '''
        
        for agent in self.agent_buffer(shuffled):
            if hasattr(agent, "type") and agent.type == 'group':
                self.group_step()
            else:
                if agent.unique_id in self._agents.keys(): 
                    agent.step()
            
        
    def step_by_type(self, agent_type, shuffled = True):
        
        '''
        Concept: Step process for sub agents within active group agent by 
        type
        '''
        
        for agent in self.agent_by_type_buffer(agent_type, shuffled):
            if hasattr(agent, "type") and agent.type == 'group':
                self.group_step()
            else:
                if agent.unique_id in self._agents.keys(): 
                    agent.step()
                
        
                
              

        
        
        
           
        

            