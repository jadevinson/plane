# Copyright Jade Vinson 2016

import random
random.seed(131)


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


def iperm(p):
    'Invert a permutation p'
    n = len(p)
    q = [-1 for i in list(range(n))]
    for i in list(range(n)):
        assert isinstance(p[i],int)
        assert p[i]>=0
        assert p[i]<n
        q[p[i]] = i
    for i in q:
        assert q[i]>=0
    return q


# Order in which people are lined up
queue = people[:]
random.shuffle(queue)
ptq = iperm(queue)
print('Queue = ',queue)
print('People = ',people)
print('Position of each person in queue = ',ptq)
print('Seat assigned to each person = ',pts)



# Set the initial full state just before boarding starts
state = ['waiting' for i in people]    # waiting, unblocked, moving, packing, seated
position = [-waiting_space*ptq[i] for i in people] # current position
goal = [seat_space*s[0] for s in pts]  # Position of goal seat
rtime = [-1 for i in people] # Remaining Time until each person would initiate state change

# Person immediately ahead or behind in line, or -1 if none
ahead = [-1 for i in people]
behind = [-1 for i in people]
for i in range(1,npeople):
    ahead[queue[i]] = queue[i-1]
    behind[queue[i-1]] = queue[i]


def nap(x):
    'name and print variable named x, useful for debugging.'
    assert(isinstance(x,str))
    print('    ',x + ' = ',eval(x))


def printstate():
    print('CURRENT STATE:')
    nap('time')
    print('    ','(person,seat,state,position,goal,rtime,ahead,behind)')
    for q in queue:
        if state[q] != 'seated':
            print('    ',(q,pts[q],state[q],position[q],goal[q],rtime[q],ahead[q],behind[q]))


# Global time
time = 0


# Print the initial state
print('THE INITIAL STATE:')
printstate()


# To get things started, unblock the person at the very front of the line:
state[queue[0]] = 'unblocked'
rtime[queue[0]] = reflex_time


print('STATE AFTER UNBLOCKIG FIRST PERSON')
printstate()


def time_until_seat_or_obstruction(next_actor):
    "Calculate time to next action for this person, due to either block ahead, or reaching seat."

    time_to_seat = (goal[next_actor]-position[next_actor])/walking_speed
    time_to_event = time_to_seat
    next_state = 'packing'
    if (ahead[next_actor]>=0) & (state[ahead[next_actor]] in ['waiting','packing','unblocked']):
        time_to_obstruction = (position[ahead[next_actor]]-waiting_space-position[next_actor])/walking_speed
        if time_to_obstruction < time_to_seat:
            time_to_event = time_to_obstruction
            next_state = 'waiting'
    return time_to_event,next_state


while not all([s=='seated' for s in state]):
    (step_time,next_actor) = min([(v,i) for (i,v) in enumerate(rtime) if v>=0])

    print ('time,steptime,next_actor = ',time,step_time, next_actor)


    # Now move every person, and global_time, forward by that amount of time:
    time += step_time
    for i in people:
        if state[i] == 'waiting':
            next
        elif state[i] == 'unblocked':
            rtime[i] -= step_time
            next
        elif state[i] == 'moving':
            rtime[i] -= step_time
            position[i] += walking_speed * step_time
            next
        elif state[i] == 'packing':
            rtime[i] -= step_time
            next
        elif state[i] == 'seated':
            next
        else:
            assert False


    # Update the state of next actor, and his effects on people behind
    SNA = state[next_actor]
    assert nearzero(rtime[next_actor])
    if SNA == 'unblocked':
        state[next_actor] = 'moving'

        rtime[next_actor],_ = time_until_seat_or_obstruction(next_actor)

        if (behind[next_actor] >= 0):
            if state[behind[next_actor]]=='waiting':
                state[behind[next_actor]] = 'unblocked'
                rtime[behind[next_actor]] = reflex_time
            elif state[behind[next_actor]]=='moving':
                rtime[behind[next_actor]],_ = time_until_seat_or_obstruction(behind[next_actor])
    elif SNA == 'moving':
        # first determine if we will be transitioning to 'waiting' or to 'packing'
        time_to_event,next_state = time_until_seat_or_obstruction(next_actor)
        assert nearzero(time_to_event)
        if next_state == 'packing':
            assert nearzero(position[next_actor]-goal[next_actor])
            state[next_actor] = 'packing'
            rtime[next_actor] = packing_time
            if (behind[next_actor] >= 0) & (state[behind[next_actor]]=='moving'):
                rtime[behind[next_actor]],_ = time_until_seat_or_obstruction(behind[next_actor])
        elif next_state == 'waiting':
            state[next_actor] = 'waiting'
            rtime[next_actor] = -1
            if (behind[next_actor] >= 0) & (state[behind[next_actor]] == 'moving'):
                rtime[behind[next_actor]],_ = time_until_seat_or_obstruction(behind[next_actor])
        else:
            assert False
    elif SNA == 'packing':
        state[next_actor] = 'seated'
        rtime[next_actor] = -1
        if ahead[next_actor]>=0:
            behind[ahead[next_actor]] = behind[next_actor]
        if behind[next_actor]>=0:
            ahead[behind[next_actor]] = ahead[next_actor]
            if state[behind[next_actor]] == 'moving':
                rtime[behind[next_actor]],_ = time_until_seat_or_obstruction(behind[next_actor])
            if state[behind[next_actor]] == 'waiting':
                state[behind[next_actor]] = 'unblocked'
                rtime[behind[next_actor]] = reflex_time
        ahead[next_actor] = -1
        behind[next_actor] = -1
    else:
        print (SNA)
        assert False

    printstate()

print('FINAL TIME: ', time)

# NOTES BELOW FOR TRYING TO THINK OUT A PLAN
#
# Big area for improvement: I think the simulation algorithm as I have it now is somewhere
#   between quadratic and cubic in the number of people, because the total time grows linearly,
#   the time increments grow smaller, and the amount of work for each time increment grows with
#   the number of people.
#   Is it possible to replace what I have with something like a priority queue of upcoming events?
#   That might be closer to more towards linear time in number of people (probably between
#   linear and quadratic, because the number of events per person will still increase)
#
# Big area for improvement: complexity and correctness, verifying its correct
#    * modularizing it and cleaning up the style will help
#    * Breaking it all up into smaller more manageable chunks
#    * adding functions and explicit tests will hekp
#    * refactoring towards priority queue will help; eg tests that old and new methods
#       get identical answers are valuable when old and new are very different
#
# PSEUDOCODE:
# all_seated = False
# while not all_seated:
#     (next_actor, step_time) = min( keys state, key = time to next action for that person ))
#     step everyone forward by step_time, updating their continuous state
#     time += step_time
#     the next actor takes his action, updating his full state as well as people behind that are affected
#     all_seated = all( s[0]=='seated' for s in state)
#
# print 'Total time requied for boarding if %f' % time
#
# Possible states for a person:
#   waiting - position
#   unblocked - position, time until moving
#   moving - position, time until obstacle
#   packing - time until completion
#   seated - [nothing more needed]
#
# ROUGH PLAN:
#
# Show visual pictures of one full boarding process, random order
#
# Simulate 1000 random boardings, and show historgram of boarding times
#
# Show visually and calculate boarding times,
#  for a handful of intersting orders such as WMI
#
# Visually show boarding process for an alpha=0.1 random
#   deviation from an ordered boarding such as WMI
#
# Simulate 1000 random deviations from ordered, and
#   calculate histogram of boarding times.
#
#
# Use the same plane throughout demo
#plane  = airplane.init()
#
# Use the same people throughout demo
#people = passengers.init(plane.get_seats())
#
# TODO: Set random seed for reproducibility
#
#order = shuffle(plane.get_seats())
#
#boarding = boarding_process.init(plane, people, order)
#
#time = boarding.simulate_visually()
#
#seats = airplane.get_seats()
#
#p = single_aisle_plane.init(rows=40, left='AB', right='CDE')
#
#
#setup single_aisle_plane
#
#Set up the geometry of the single_aisle_plane
#
#Set parameters such as walking speed, time to put luggage in bin, degree to which time to put luggage in bin changes with how ull they are
#
#Set up the individualities of teh passengers (maybe they are all the same, maybe some fast and some slow)
#
#Choose an order
#
#Simulate, with or without additruional variability
#
#
# Show a simulation of a single boarding with random order, in a visual way
#
#What is a way to internally represent the state?
#* Characteristics of the plane
#* Characteristics of the passengers
#* State of the boarding process: begins with a collection of queued people,
# during boarding the positions along aisle might be important concept,
# ends with everyone seated.
#
#HOw to step time forward?
#  * start from front of line, note how long it would take them to complete next action
#  * is each person waiting, walking, packing (takes more time if someone on row has to get up),
#      or seated?
#  * is each seat filled or not?
#
#Transitions:
#  * waiting -> walking : if the person ahead of you starts walking,
#     or the person ahead of you finishes packing
#  * walking -> packing: if you reach your seat
#  * walking -> waiting: if you reach an obstruction
#     * the walking person directly ahead of you starts packing or starts waiting
#       (by induction, they would only start waiting if someone farther ahead starts packing)
#     * you catch up to someone who is packing,
#     * you catch up to someone who is waiting.
#
#  * packing -> seated: takes an amount of time that depends on whether someone already seated
#     has to get up for you and configuration
#       Quick: (,A), (,B), (,C), (A,B), (A,C), (B,C), (AB,C)
#       Slow: (B,A), (C,A), (C,B), (AC,B)
#       Really Slow: (BC,A).
#
#Global state: time
#
#Details of state for each person:
#  waiting: position (a seat position, minus packing distance, minus a multiple of waiting dist)
#  walking: position
#  packing: time to completion
#
#Time until next discrete change:
#  * a walking person reaches obstruction (update column behind to waiting)
#  * a walking person starts packing (update column behind to waiting)
#  * a packing person is seated (update column behind to walking)
#
#take the minimum of all these above.  Then step everyone forward by that amount
#
#Keep stepping time forward until everyone is seated.
#
# Try 1000 random orders, what is variability in board time
#Set the random seed for reproducibility
#times = zeros(1000)
#
#for i=range(1000):
#    order = shuffle(seats)
#    s = boarding_simulation(order,p,parm)
#    times(i) = s.board_time()  # Runs the simulation in its full glory, but doesn't show anything visually and simply returns the final run time.
#
#show a histogram of times from random orders
#
# Now try particular orders:
# WMI window middle isle ordering
# back to front ordering
# staggered WMI (as recommended by Steffen)
#
# No one is perfect.  Start with a perect order, but assume that
# a proportion alpha totally disregard your instructions and board at random,
# while (1-alpha) follow instructions.
# How does board time increase as alpha increases?
#
# Selling status, priority boarding (this is important for airline revenue)
#
# Family blocks (members of a family will and should board together)
