import pycxsimulator
from pylab import *
import numpy as np

# Constants for model assumptions
degradation_rate = 0.98  # Represents 2% degradation of plastic size per time step
death_rate = 0.002  # Represents 0.2% chance of organism death per time step
attached_death_rate = 0.001 # Represents 0.1% chance of organism death per time step if colonizing
min_degradable_size = 0.05
agent_intro_rate = 0.07  # Probability of introducing a new agent each time step
microplastic_intro_rate = 0.05  # Probability of introducing a new microplastic each time step
max_agents = 110  # Maximum number of agents in the system
max_microplastics = 8  # Maximum number of microplastics in the system
eps_irreversible_threshold = 10
eps_dispersion_threshold = 20

#organism type to eps rate
organism_mapping = {
    "PioneerColonizer" : .5, 
    "SecondaryColonizer": 0, 
    "Degrader": 0}

#plastic type to hydrolysis capability
plastic_mapping = {
    "PUR": True, 
    "PLA": True, 
    "PET": True, 
    "PE": False, 
    "PP": False, 
    "PS": False, 
    "PVC": False
}

class Agent: #aka microorganism
    def __init__(self, organism_type, eps_production_rate):
        self.organism_type = organism_type
        self.eps_production_rate = eps_production_rate
        self.is_colonizing = False
        self.plastic_attached = None
        self.x = random()
        self.y = random()
    
    def adhere_to_plastic(self, microplastic):
        if microplastic.size <= min_degradable_size:
            return False
        
        #Creates order for which organisms can join the biofilm (pioneer -> secondary -> biodegrading organisms)
        if self.organism_type == "PioneerColonizer":
            return True
        elif self.organism_type == "SecondaryColonizer" and microplastic.eps_concentration >= eps_irreversible_threshold:
            for organism in microplastic.organisms:
                if organism.organism_type == "PioneerColonizer":
                    return True
        elif self.organism_type == "Degrader":
            for organism in microplastic.organisms:
                if organism.organism_type == "SecondaryColonizer":
                    return True
        return False
    
    def produce_eps(self):
        # Each organism produces EPS, which is deposited on the plastic it's attached to
        if self.is_colonizing and self.plastic_attached.eps_concentration < eps_dispersion_threshold:
            self.plastic_attached.eps_concentration += self.eps_production_rate


class Microplastic:
    def __init__(self, hydrolyzable, plastic_type):
        self.size = 1
        self.hydrolyzable = hydrolyzable
        self.plastic_type = plastic_type
        self.eps_concentration = 0
        self.is_colonized = False
        self.organisms = []
        self.x = random()
        self.y = random()

        
def initialize():
    global time, agents, microplastics, temperature, nutrient_availability, proximity_threshold, adj_death_rate, adj_degradation
    time = 0
    
    #environmental values (adjustable)
    temperature = 15 #Value between 0 and 30
    nutrient_availability = 2 #Value between 0 and 4
    
    proximity_threshold = adjusted_proximity_threshold(nutrient_availability)
    adj_death_rate = adjusted_death_rate(temperature)
    adj_degradation = adjusted_degrade_efficiency(temperature)
    
    #initialize agents
    agents = []
    for i in range(30):
        organism_type = np.random.choice(list(organism_mapping.keys()))
        eps_production_rate = organism_mapping[organism_type]
        agent = Agent(organism_type, eps_production_rate)
        agents.append(agent)
        
    #initialize MPs
    microplastics = []
    for i in range(3):
        plastic_type = np.random.choice(list(plastic_mapping.keys()))
        hydrolyzable = plastic_mapping[plastic_type]
        microplastic = Microplastic(hydrolyzable, plastic_type)
        microplastics.append(microplastic)
        

def observe():
    global agents, microplastics
    cla()
    
    organism_type_color = {'PioneerColonizer': 'b', 'SecondaryColonizer': 'r', 'Degrader': 'g'}
    for organism_type, color in organism_type_color.items():
        organism_type_agents = [ag for ag in agents if ag.organism_type == organism_type]
        x_agents = [ag.x for ag in organism_type_agents]
        y_agents = [ag.y for ag in organism_type_agents]
        plot(x_agents, y_agents, color + 'o', alpha=0.5, label=f'{organism_type} agents')  # 'o' for circles (agents)
    
    # Use a separate marker and color for microplastics
    x_plastics = [mp.x for mp in microplastics]
    y_plastics = [mp.y for mp in microplastics]
    plot(x_plastics, y_plastics, 'ks', markersize=20, alpha=0.15, label='Microplastics')  # 'ks' for squares (microplastics)
    
    for mp in microplastics:
        epsc = mp.eps_concentration
        types = mp.plastic_type
        num_orgs = len(mp.organisms)
        x_plastics = mp.x
        y_plastics = mp.y
        plt.text(x_plastics, y_plastics - 0.075, f'{epsc:.2f}',
                 ha='center', va='top', fontsize=8)
        plt.text(x_plastics, y_plastics - 0.05, types,
                 ha='center', va='top', fontsize=8)
        plt.text(x_plastics, y_plastics -0.1, num_orgs,
                 ha='center', va='top', fontsize=8)
    
    axis('image')
    axis([0, 1, 0, 1])
    title('t = ' + str(time))

def degrade_plastics():
    global microplastics
    
    # Degrade each piece of plastic
    for plastic in microplastics[:]:
        #plastics capable of hydrolysis are easier to degrade
        if plastic.hydrolyzable:
            for organism in plastic.organisms:
                if organism.organism_type == "Degrader":
                    plastic.size *= ((degradation_rate - adj_degradation) * .9)
        else:
            for organism in plastic.organisms:
                if organism.organism_type == "Degrader":
                    plastic.size *= (degradation_rate - adj_degradation)
            
        # Remove fully degraded plastics
        if plastic.size <= min_degradable_size:
            microplastics.remove(plastic)
            # Release any attached organisms
            if plastic.is_colonized:
                for agent in plastic.organisms:
                    agent.is_colonizing = False
                    agent.plastic_attached = None

def update_agent_position_with_plastic(agent):
    # If the agent is colonizing a piece of plastic, the agent's position should be updated to match the plastic's position
    jitter_amount = np.random.uniform(-0.008, 0.008)
    
    if agent.is_colonizing:
        agent.x, agent.y = agent.plastic_attached.x + jitter_amount, agent.plastic_attached.y + jitter_amount
        
def adjusted_death_rate(temperature):
    effect = temperature * 0.00008
    
    return effect

def adjusted_degrade_efficiency(temperature):
    effect = temperature / 30.0 * 0.15
    
    return effect

def adjusted_proximity_threshold(nutrient_availability):
    global proximity_threshold
    #changes proximity threshold based on nurtient availability
    proximity_threshold = 0.005
    adjustment_factor = 1 + nutrient_availability
    proximity_threshold *= adjustment_factor
    
    return proximity_threshold
        
def random_walk_and_adherence():
    global agents, microplastics, proximity_threshold
    
    for microplastic in microplastics:
        microplastic.x += uniform(-.03, .03)
        microplastic.y += uniform(-.03, .03)
        microplastic.x = 1 if microplastic.x > 1 else 0 if microplastic.x < 0 else microplastic.x
        microplastic.y = 1 if microplastic.y > 1 else 0 if microplastic.y < 0 else microplastic.y
    
    for agent in agents:
        if not agent.is_colonizing:
            agent.x += uniform(-.05, .05)
            agent.y += uniform(-.05, .05)
            agent.x = 1 if agent.x > 1 else 0 if agent.x < 0 else agent.x
            agent.y = 1 if agent.y > 1 else 0 if agent.y < 0 else agent.y
            # Check for nearby plastics to colonize
            for plastic in microplastics:
                if (agent.x - plastic.x)**2 + (agent.y - plastic.y)**2 < proximity_threshold:
                    agent.is_colonizing = agent.adhere_to_plastic(plastic)
                    if agent.is_colonizing:
                        plastic.is_colonized = True
                        plastic.organisms.append(agent)
                        agent.plastic_attached = plastic
                        break
        else:
            # Update the position of the colonizing agent to that of the plastic
            update_agent_position_with_plastic(agent)

def introduce_new_agents():
    global agents
    if len(agents) < max_agents and random() < agent_intro_rate:
        organism_type = np.random.choice(list(organism_mapping.keys()))
        eps_production_rate = organism_mapping[organism_type]
        new_agent = Agent(organism_type, eps_production_rate)
        agents.append(new_agent)

def introduce_new_microplastics():
    global microplastics
    if len(microplastics) < max_microplastics and random() < microplastic_intro_rate:
        plastic_type = np.random.choice(list(plastic_mapping.keys()))
        hydrolyzable = plastic_mapping[plastic_type]
        new_microplastic = Microplastic(hydrolyzable, plastic_type)
        microplastics.append(new_microplastic)        

def death_process():
    global agents
    for agent in agents:
        if not agent.is_colonizing:
            if random() < death_rate + adj_death_rate:
                agents.remove(agent)  # This agent dies
        else:
            if random() < attached_death_rate + adj_death_rate:
                agents.remove(agent)
    
def dispersion_based_on_eps():
    global microplastics
    for microplastic in microplastics:
        # Check if EPS concentration exceeds the threshold for dispersion
        if microplastic.eps_concentration >= eps_dispersion_threshold and microplastic.organisms:
            # Remove an agent from the microplastic and reset its colonization status
            dispersive_agent = microplastic.organisms.pop(-1)  # releases most recent biofilm member
            dispersive_agent.is_colonizing = False
            
            if not microplastic.organisms:
                microplastic.is_colonized = False
                microplastic.eps_concentration = 0
            
            # Only one agent leaves per step per microplastic, so stop checking after one agent has dispersed
            return  # Early return ensures only one agent per call; remove if multiple dispersions per step are allowed

def update():
    global time, agents, microplastics
    time += 1
   
    death_process()

    #introduction of new agents
    introduce_new_agents()
    introduce_new_microplastics()
    
    # Perform the random walk and check for adhesion of free agents to plastics
    random_walk_and_adherence()

    # Perform secretion of extracellular polymetric substances
    for microplastic in microplastics:
        for agent in microplastic.organisms:
            agent.produce_eps()
    
    dispersion_based_on_eps()
    
    # Apply the degradation to the plastics
    degrade_plastics()
    
pycxsimulator.GUI().start(func=[initialize, observe, update])