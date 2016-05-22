# Copyright Jade Vinson 2016

import random
random.seed(131)

import util


# Parameters describing time/space/physical properties:
waiting_space = 0.8  # amount of space taken by a person in line (meters)
seat_space    = 1.5  # amount of space between seat rows (meters)

reflex_time   = 0.3  # time from when a person unblocked to when they start walking
packing_time  = 12.0 # time it takes a person to store their luggage and get situated.
                     # Note we may refine model later so this depends on whether
                     # aisle seat has to stand up to let the window person get past them.

walking_speed = 0.8  # meters/second


def nearzero(x):
    assert(isinstance(x,float))
    return abs(x) < 0.000001


# Seats on the aircraft
seats = [(r,c) for r in range(1,11) for c in 'ABCD']
nseats = len(seats)
print('nseats,seats = ',nseats,seats)


# The people who will be passengers
npeople = nseats
people = list(range(npeople))
print('npeople,people = ',npeople,people)


# Correspondence between people and seats
assert npeople <= nseats
pts = seats[:]
random.shuffle(pts)
pts = pts[:npeople]  # people to seats function
print('People to seats: ',pts)



# Order in which people are lined up
queue = people[:]
random.shuffle(queue)
ptq = util.iperm(queue)
print('Queue = ',queue)
print('People = ',people)
print('Position of each person in queue = ',ptq)
print('Seat assigned to each person = ',pts)


# Possible states for a person:
waiting_state = 0
unblocked_state = 1
moving_state = 2
packing_state = 3
seated_state = 4




# Set the initial full state just before boarding starts
state = [waiting_state for i in people]    # waiting, unblocked, moving, packing, seated
position = [-waiting_space*ptq[i] for i in people] # current position
goal = [seat_space*s[0] for s in pts]  # Position of goal seat
rtime = [-1 for i in people] # Remaining Time until each person would initiate state change

# Person immediately ahead or behind in line, or -1 if none
ahead = [-1 for i in people]
behind = [-1 for i in people]
for i in range(1,npeople):
    ahead[queue[i]] = queue[i-1]
    behind[queue[i-1]] = queue[i]


def printstate():
    print('CURRENT STATE:')
    print('     time = ',time)
    print('    ','(person,seat,state,position,goal,rtime,ahead,behind)')
    for q in queue:
        if state[q] != seated_state:
            pass
            #print('    ',(q,pts[q],state[q],position[q],goal[q],rtime[q],ahead[q],behind[q]))


# Global time
time = 0


# Print the initial state
print('THE INITIAL STATE:')
printstate()


# To get things started, unblock the person at the very front of the line:
state[queue[0]] = unblocked_state
rtime[queue[0]] = reflex_time


print('STATE AFTER UNBLOCKIG FIRST PERSON')
printstate()


def time_until_seat_or_obstruction(p):
    "Calculate time to next action for person p, due to either block ahead, or reaching seat."

    time_to_seat = (goal[p]-position[p])/walking_speed
    time_to_event = time_to_seat
    next_state = packing_state
    if (ahead[p]>=0) & (state[ahead[p]] in [waiting_state,packing_state,unblocked_state]):
        time_to_obstruction = (position[ahead[p]]-waiting_space-position[p])/walking_speed
        if time_to_obstruction < time_to_seat:
            time_to_event = time_to_obstruction
            next_state = waiting_state
    return time_to_event,next_state


while not all([s==seated_state for s in state]):
    (step_time,next_actor) = min([(v,i) for (i,v) in enumerate(rtime) if v>=0])

    print ('time,steptime,next_actor = ',time,step_time, next_actor)


    # Now move every person, and global_time, forward by that amount of time:
    time += step_time
    for i in people:
        if state[i] == waiting_state:
            next
        elif state[i] == unblocked_state:
            rtime[i] -= step_time
            next
        elif state[i] == moving_state:
            rtime[i] -= step_time
            position[i] += walking_speed * step_time
            next
        elif state[i] == packing_state:
            rtime[i] -= step_time
            next
        elif state[i] == seated_state:
            next
        else:
            assert False


    # Update the state of next actor, and his effects on people behind
    SNA = state[next_actor]
    assert nearzero(rtime[next_actor])
    if SNA == unblocked_state:
        state[next_actor] = moving_state

        rtime[next_actor],_ = time_until_seat_or_obstruction(next_actor)

        if (behind[next_actor] >= 0):
            if state[behind[next_actor]]==waiting_state:
                state[behind[next_actor]] = unblocked_state
                rtime[behind[next_actor]] = reflex_time
            elif state[behind[next_actor]]==moving_state:
                rtime[behind[next_actor]],_ = time_until_seat_or_obstruction(behind[next_actor])
    elif SNA == moving_state:
        # first determine if we will be transitioning to waiting_state or to packing_state
        time_to_event,next_state = time_until_seat_or_obstruction(next_actor)
        assert nearzero(time_to_event)
        if next_state == packing_state:
            assert nearzero(position[next_actor]-goal[next_actor])
            state[next_actor] = packing_state
            rtime[next_actor] = packing_time
        elif next_state == waiting_state:
            state[next_actor] = waiting_state
            rtime[next_actor] = -1
        else:
            assert False
        if (behind[next_actor] >= 0) & (state[behind[next_actor]] == moving_state):
            rtime[behind[next_actor]],_ = time_until_seat_or_obstruction(behind[next_actor])

    elif SNA == packing_state:
        state[next_actor] = seated_state
        rtime[next_actor] = -1
        if ahead[next_actor]>=0:
            behind[ahead[next_actor]] = behind[next_actor]
        if behind[next_actor]>=0:
            ahead[behind[next_actor]] = ahead[next_actor]
            if state[behind[next_actor]] == moving_state:
                rtime[behind[next_actor]],_ = time_until_seat_or_obstruction(behind[next_actor])
            if state[behind[next_actor]] == waiting_state:
                state[behind[next_actor]] = unblocked_state
                rtime[behind[next_actor]] = reflex_time
        ahead[next_actor] = -1
        behind[next_actor] = -1
    else:
        print (SNA)
        assert False

    #printstate()

print('FINAL TIME: ', time)
