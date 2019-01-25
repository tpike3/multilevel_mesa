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
    --Explicit approach (line )
        -- form_meta
        --reassess_meta
    --Core functions- steps and buffers (line 278)
        --const_buffer
        --meta_buffer
        --step
    --Network based approach (line)
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


class ML_Mesa(RandomActivation):
    
    def __init__(self, model, min_for_meta = 2):
        super().__init__(model)
        #Maintains master dictionary of all agents in model
        self._agents = OrderedDict()
        #Maintains master network of all agents in model
        self.net = nx.Graph()
        #Provides view of agents by type
        self.agents_by_type = defaultdict(dict)
        #Dictionary of agents who are active for each time step
        self.schedule = OrderedDict()
        #Minimum number of agent to eleminate a meta agent
        self.min = min_for_meta
        #TODO Create Meta_agent Orderdict; figure out how to make nested
        #levels
        self.id_counter = 0
        self.metas = OrderedDict()
        self.reverse_meta = defaultdict(set)
        
        
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
        Provides number of meta agents in the schedule
        '''
        return len(self.schedule.keys())
    
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
            
            
    def remove(self, agent): 
        
        '''
        Params:
            agent - single granular agent object
        
        Removes agent from: 
            - Master agent list (self._agents)
            - Master agent network (self.net)
            - Master agents by type Dict (self.agents_by_type)
            - Schedule
            - Reverse Metas
        '''
        del self._agents[agent.unique_id]
        agent_class = type(agent)
        del self.agents_by_type[agent_class][agent.unique_id]
        self.net.remove_node(agent)
        
        if agent.unique_id in self.reverse_meta.keys():
            meta = self.reverse_meta[agent.unique_id]
            #delete agent form reverse_meta
            del self.reverse_meta[agent.unique_id]
            for m in meta: 
                if m in self.metas.keys():
                    if agent.unique_id in self.metas[m].sub_agents.keys():
                        #remove agent form meta_agent
                        meta_status = self.metas[m].remove(agent.unique_id, self.min)
                        #if agent dies
                        if meta_status != None:
                            if m in self.schedule.keys():
                                #remove fsom schedule
                                del self.schedule[m]
                                #remove meta agent form all reverse_metas
                                for meta_sets in self.reverse_meta.values():
                                    meta_sets.discard(m)
                            #remove form master meta
                            del self.metas[m]
                            #remove node is exists
                            if m in self.net:
                                self.net.remove_node(m)
                                
            
        
        if agent.unique_id in self.schedule.keys(): 
            del self.schedule[agent.unique_id] 
            
                
    ########################################################################
    #
    #                  Meta Helper Function
    #
    ########################################################################
    
    def meta_iterate(self, metas, determine_id, double, policy, group_net):
        
        
        for edge in metas:
                #create empty dictionary for sub_agents of specific link
                meta2_dict = {}
                #identify if the agents have are part of common metaagent
                intersect = \
                self.reverse_meta[edge[0].unique_id].intersection(self.reverse_meta[edge[1].unique_id])
                if intersect == set(): #no intersection
                   #neither are part of a metaagent and will create their own
                   if  self.reverse_meta[edge[0].unique_id] == set() and \
                   self.reverse_meta[edge[1].unique_id] == set(): #not part of meta_agent
                       # create new Id
                       if determine_id == 'default': 
                           unique_id =  "meta"+str(self.id_counter)
                           self.id_counter += 1
                       else: 
                           unique_id = determine_id
                       #create new meta agent        
                       meta2_dict = {unique_id: dict((x.unique_id, x) for x in edge)}
                       #Create conditional for policy
                       if policy == None: 
                           ma = MetaAgent(unique_id, self.model, self._agents,\
                                      meta2_dict[unique_id], self.reverse_meta)
                       else:
                           ma = MetaAgent(unique_id, self.model, self._agents,\
                                      meta2_dict[unique_id], self.reverse_meta, \
                                      policy)
                       ma.form_graph(edge)
                       # add to schedule
                       self.schedule[ma.unique_id] = ma
                       #add to management structures
                       #Metas ordereddict
                       self.metas[ma.unique_id] = ma
                       #reverse_meta references
                       self.reverse_meta[edge[0].unique_id].add(ma.unique_id)
                       self.reverse_meta[edge[1].unique_id].add(ma.unique_id)
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
                   #one is part of a meta_agent so the other will join
                   elif self.reverse_meta[edge[0].unique_id] == set() or \
                   self.reverse_meta[edge[1].unique_id] == set():  
                      if self.reverse_meta[edge[0].unique_id] == set():
                          #get the meta_agent
                          for agent in self.reverse_meta[edge[1].unique_id]:
                              meta_a = agent
                              break
                         
                          self.metas[meta_a].add([edge[0]])
                          #self.schedule[meta_a].add([edge[0]]) #MetaAgent add function
                          #add to reverse
                          self.reverse_meta[edge[0].unique_id].add(meta_a) #set add function
                          #add to network
                          self.add_link([edge])
                          #delete from schedule
                          if double == False: 
                            if edge[0].unique_id in self.schedule.keys():
                                    del self.schedule[edge[0].unique_id]
                      else: 
                          for agent in self.reverse_meta[edge[0].unique_id]:
                              meta_a = agent
                              break
                          
                          self.metas[meta_a].add([edge[1]])
                          #self.schedule[meta_a].add([edge[1]]) #metaagent add functoin
                          #add to reverse
                          self.reverse_meta[edge[1].unique_id].add(meta_a) #set add function 
                          #add to network
                          self.add_link([edge])
                          #delete from schedule
                          if double == False: 
                            if edge[1].unique_id in self.schedule.keys(): 
                                    del self.schedule[edge[1].unique_id]
                   #both are part of a meta_agent and so will maintain a link
                   else: 
                      #make sure there is a link between agents
                      self.add_link([edge])
                #both are part of the same metaagent
                else: 
                    pass
    
    
    #########################################################################
    #
    #         Explicit Approach - User Directed MetaAgent Creation
    #
    ########################################################################    
    
    def group_remove(self, agents):
        '''
        Helper function for form_meta
        
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
    
    def form_meta(self, process, *args, determine_id = 'default', \
                      double = False, policy = None,  **kwargs):
        '''
        Concept: Function works with a user defined process to take in lists of 
        agents who should be gorup together and runs them through the meta_agent 
        process making sure they are still alive and not duplicating meta_agents
        
        Helper function: group_remove(self) checks to see if agent is still 
        alive
        
        Params: 
            process (required) -- YIELDs list of agents who should be grouped
            together and if ID not default and ID
            args = arguments for user defined process
            TODO improve for multiple arguments
            determine_id = default means the package will give an id
            TODO test non default id
            double = True or False if agents should be stepped twice during 
            process
            policy = pass in meta_agent policy
            
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
                    #create meta_agents
                    self.meta_iterate(edges, determine_id, double, policy)
            else: 
                edges= self.group_remove(result[1])
                #create meta_agents
                if edges != None: 
                    #create meta_agents
                    self.meta_iterate(edges, result[0], double, policy)
         
            
                   
   
    def reassess_meta(self, process, *args, reintroduce = True, **kwargs):
        
        '''
        Purpose: Examine a meta agent to remove or add agents and delete if 
        empty
        
        Params: 
            processs - function to assess whether agents should be in same 
                       module
            args - arguments for process function
            shuffled - True or False; do agents need to be in random order
            min_for_meta - one more than the smallest number of subagents 
            before a metaagent is deleted
            
        Critical Dynamics: 
            - process must return 2 agents who are no longer linked
            - meta-agents then receives list of agents to remove
            - if meta-agent has no subagents it is removed from schedule
        
        '''
                
        for meta_agent in self.reassess_buffer(): 
            
            #master list of agents to remove
            subs_to_remove = []
            if args == None: 
                #must receive list of tuples of connected agents
                peel_list = process(meta_agent, *args, **kwargs)
                if peel_list != None: 
                     #allows process output to be two agents or 
                     #tuple of two agents
                     if len(peel_list) == 2: 
                         edges = tuple(peel_list)
                         self.net.remove_edge(self._agents[edges[0].unique_id],\
                                                 self._agents[edges[1].unique_id])
                         #Remove form reverse_meta, uses set remove function
                         self.reverse_meta[edges[0].unique_id].remove(meta_agent.unique_id)
                         self.reverse_meta[edges[1].unique_id].remove(meta_agent.unique_id)
                     elif len(peel_list) > 2: 
                         #Be Default all agents in a meta_agent should be
                         #connected
                         edges = list(itertools.combinations(peel_list, 2))
                         self.net.remove_edges_from(edges)
                         for edge in edges: 
                             self.reverse_meta[edges[0].unique_id].remove(meta_agent.unique_id)
                             self.reverse_meta[edges[1].unique_id].remove(meta_agent.unique_id)       
                     else: 
                         raise Exception("Removing subagents from a ", \
                                         "requires either 2 agents ", 
                                         "or a list of agents. ",)
                        
                     #remove buffer is based on agent id, convert agent list
                     # to agent ID
                     for each in peel_list: 
                         subs_to_remove.append(each.unique_id)
                        
                
            else: 
                peel_list = process(meta_agent, args)
                if peel_list != None: 
                    subs_to_remove += peel_list
                 
            
            
            #function to add independent agent back in 
            if reintroduce == True and peel_list != None: 
                for agent in peel_list: 
                    self.add(agent, schedule = True)
            
            # call function to remove metaagents if necessary
            meta_status = meta_agent.remove(subs_to_remove, self.min)
            #Remove meta-agents with no sub_agents
            if meta_status != None: 
                del self.schedule[meta_agent.unique_id]
                del self.metas[meta_agent.unique_id]
            
        
    #########################################################
    #
    #    Core Functions - Step and Buffer
    #
    #########################################################    
    
    def reassess_buffer(self):
        
        meta_keys = list(self.metas.keys())
    
        for key in meta_keys: 
            yield self.metas[key]
    
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
                
    def meta_buffer(self, shuffled):
        '''
        Purpose: Buffer for main agents to prevent issues of data structure
        changing during execution
        
        Params: Shuffled - changes order of execution to mitigate mover 
        advantages
        '''
                
        meta_keys = list(self.schedule.keys())
                
        if shuffled: 
            self.model.random.shuffle(meta_keys)
        
        for key in meta_keys: 
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
        
        for agent in self.meta_buffer(shuffled):
            #currently a random activation nested within a random activation 
            if type(agent) != MetaAgent and type(agent) != const_update: 
                agent.step()
            else: 
                if by_type == False: 
                    agent.meta_step()
                else: 
                    #type is list of agents order
                    if const_update == False: 
                        agent.meta_step(by_type)
                    else: 
                        agent.meta_step(by_type, const_update)
                
        if const_update != False: 
            for agent in self.const_buffer(const_update):
                agent.step()
                    
        
        
        
        
    ######################################################################
    #
    #         Networked Based Meta-Agent Creation
    #
    ######################################################################
    
    def net_schedule(self, link_type = None,link_value = None, \
                     double = False, policy = None, group_net = False):
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
                metas = []
                for edge in self.net.edges.data(link_type): 
                    metas.append((edge[0], edge[1]))

            else: 
                metas = []
                for edge in self.net.edges.data(link_type): 
                    if type(link_value) == str:
                        if edge[2] == link_value:
                            metas.append((edge[0], edge[1]))
                    elif edge[2] >= link_value: 
                        metas.append((edge[0], edge[1]))
                    
           
            self.meta_iterate(metas, determine_id = "default", double= double,\
                              policy = policy, group_net = group_net)
            
        
        else: 
            # Add all linked nodes to schedule
            metas = list(self.net.edges())
            self.meta_iterate(metas, determine_id = "default", double= double,\
                              policy = policy, group_net = group_net)
            #active_list = []
            #for meta in metas: 
                
        
    def reassess_net_schedule(self, link_type = None,\
                 link_value = None,):
    #remove metas who are no longer linked
             
        for meta_agent in self.reassess_buffer(): 
            for link in meta_agent.edge_buffer(link_type, link_value):
                
                if self.net.has_edge(link[0], link[1])== False:
                    self.reverse_meta[link[0].unique_id].remove(meta_agent.unique_id)
                    self.reverse_meta[link[1].unique_id].remove(meta_agent.unique_id)
                    meta_status = meta_agent.remove([link[0].unique_id, link[1].unique_id], self.min)
                    #add back into schedule
                    for agent in link: 
                        self.add(agent, schedule = True)
                    #Remove meta-agents with no sub_agents
                    if meta_status != None: 
                        del self.schedule[meta_agent.unique_id]
                        del self.metas[meta_agent.unique_id]
                        
            '''
                print (meta)
                #get unique_name, must be a common attribute of both agents
                if determine_id == "default":
                              unique_id = "meta"+str(self.id_counter)
                              self.id_counter += 1
                else:
                    unique_id = getattr(meta[0], determine_id)
                    
                if unique_id in self.schedule.keys(): #Assessess meta_agents in schedule
                    active_list.append(unique_id)
                    #Maintains list of agents to be updated
                    self.schedule[unique_id].add(meta)
                    #TODO can this be made more efficient?
                else: 
                    meta2_dict = {unique_id: dict((x.unique_id, x) for x in meta)}
                    ma = MetaAgent(unique_id, self.model, self._agents, \
                                   meta2_dict[unique_id],\
                                   self.reverse_meta)
                    self.schedule[ma.unique_id] = ma
                    ma.form_graph(meta)
                    #Ensures meta_agents in schedule
                    active_list.append(unique_id)
                                        
            #print ("active_list ", active_list)
            #print ("lag_list ", [(v.unique_id, v.value_sug, v.value_spice) for v in lag_list])
            for agent in self.meta_buffer(False):
                if agent.unique_id not in active_list: 
                    del self.schedule[agent.unique_id]
            '''
                 
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
        Remove links to master materowks based on agent intiatiation
        
        Params: 
            agents - list of agent objects
        '''
        
        if len(agents) > 2: 
            agents = list(itertools.combinations(agents, 2))
        self.net.remove_edges_from(agents)
        
            

'''
MetaAgent

Class which provides MetaAgents functions.
This porvides the ability to manage the MetaAgents which form and bring in 
meta_agent functions

There atre two main area of functions
 Helper functions:
     -- make_types
     -- form_graph
     -- add
     -- remove
 Core functions: 
     -- agent_buffer
     -- remove_buffer
     -- agent_by_type_buffer
     -- meta_step
     -- step
     --step_by_type
'''



from mesa import Agent

class MetaAgent(Agent, ML_Mesa):

    def __init__(self, unique_id, model, agents, sub_agents, reverse_meta, \
                 policy = None, active = True):
        super().__init__(unique_id, model)
        self._agents = agents 
        self.reverse_meta = reverse_meta
        #sub_agents is dictionary {unique_id:agent_object}
        self.sub_agents =sub_agents
        self.subs_by_type = self.make_types(sub_agents)
        self.sub_net = nx.Graph()
        self.policy = self.get_policy(policy)
        self.active = active
        self.type = 'meta'
        self.__str__ = 'meta'
    
   
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
        Concept - Allows agent(s) to be added to existing meta_agent
        
        Params: 
            agents - list of agent objects
        '''        
        for agent in agents: 
            if agent.unique_id not in self.sub_agents.keys(): 
                self.sub_agents[agent.unique_id] = agent
                self.sub_net.add_node(agent)
                self.subs_by_type[type(agent)][agent.unique_id] = agent
                self.reverse_meta[agent.unique_id].add(self.unique_id)
                for agents in self.sub_agents.values(): 
                    self.sub_net.add_edge(agent, agents)
                    
    
    def remove(self,subs_to_remove, min_for_meta, reintroduce = True):
        '''
        Concept - Allows agents to be removed form existing meta-agent
        
        Params: 
            - subs_to_remove list of agent objects
            - min_for_meta -attribute of ML_Mesa class which determines
            how many agents for a minum agent default is 2
        '''       
        
        if type(subs_to_remove) != list: 
            subs_to_remove = [subs_to_remove]
        
        for key, agent in self.remove_buffer(subs_to_remove):
            del self.sub_agents[key]
            self.sub_net.remove_node(agent)
            del self.subs_by_type[type(agent)][agent.unique_id]
        
        if len(self.sub_agents.keys()) < min_for_meta:
            #Place agent back in schedule
            if reintroduce == True: 
                for agent in self.sub_agents.values():
                    self.model.ml.schedule[agent.unique_id] = agent
            return "died"
        else:         
            return None
    
       
    
    
    
    ######################################################################
    #
    #              Core Step functions and buffers of Sub_Agents
    #
    #######################################################################    
    
    def edge_buffer(self, link_type, link_value):
        
        if link_type != None: 
            if link_value == None: 
                metas = []
                for edge in self.sub_net.edges.data(link_type): 
                    metas.append((edge[0], edge[1]))
            else: 
                metas = []
                for edge in self.sub_net.edges.data(link_type): 
                    if edge[2] != link_value:
                            metas.append((edge[0], edge[1]))
                    elif edge[2] <= link_value: 
                            metas.append((edge[0], edge[1]))
        else: 
            metas = list(self.sub_net.edges())               
        
        for edge in metas: 
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
      
    
    def meta_step(self, by_type = False, const_update = False):
        '''
        Purpose: Exectue step function of meta-agent and subagents
        
        Params: 
            by_type: either False or [list] indicating type of agents to execute
            const_update: either False or agent type indicating agent 
            which is updated constantly
        '''
        
        if self.policy != None: 
             
            self.policy.step(self)
            
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
     
    def step(self, shuffled=True):
        '''
        Concept: Step process for sub agents within active meta agent
        '''
        
        for agent in self.agent_buffer(shuffled):
            if agent.unique_id in self._agents.keys(): 
                    agent.step()
                        
    def step_by_type(self, agent_type, shuffled = True):
        
        '''
        Concept: Step process for sub agents within active meta agent by 
        type
        '''
        
        for agent in self.agent_by_type_buffer(agent_type, shuffled):
            if agent.unique_id in self._agents.keys(): 
                agent.step()
                
              

        
        
        
           
        

            