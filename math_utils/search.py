import heapq

#performs a uniform cost search (dijkstra's algorithm)
#start states is an iterable of states where the search should be gin
#goal_func takes a state and returns True if this is a goal state, false otherwise
#neighbor_func takes a state and returns an iterable of tuples containing a state and a cost to move to that state
def uniform_cost_search(start_states, goal_func, neighbor_func):
	
	open_set = list((0, s, None) for s in start_states)
	heapq.heapify(open_set)
	
	closed_set = dict()
	
	final_state = None
	
	while(len(open_set) > 0):
		cost, state, parent = heapq.heappop(open_set)
		
		if(state not in closed_set):
			closed_set[state] = parent
			
			if(goal_func(state)):
				final_state = state
				break
				
			for neighbor, neighbor_cost in neighbor_func(state):
				if(neighbor not in closed_set):
					heapq.heappush(open_set,(cost + neighbor_cost, neighbor, state))
					
	#if the final state is not none, we have found a path
	result = list()
	if(final_state is not None):
		current_state = final_state
		
		while(current_state is not None):
			result.append(current_state)
			current_state = closed_set[current_state]
			
		result.reverse()
		
	return result