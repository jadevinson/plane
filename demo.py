# Copyright Jade Vinson 2016

import random
random.seed(131)

import util


class PhysicalConstants:
    "Parameters characterizing properties of airplane and passengers."

    waiting_space = 0.8  # amount of space taken by a person in line (meters)
    seat_space    = 1.5  # amount of space between seat rows (meters)
    reflex_time   = 0.3  # time from when a person unblocked to when they start walking
    packing_time  = 12.0 # time it takes a person to store their luggage and get situated.
                         # Note we may refine model later so this depends on whether
                         # aisle seat has to stand up to let the window person get past them.
    walking_speed = 0.8  # meters/second


class State:
    "Qualitative states for what a single person is doing."

    waiting = 0
    unblocked = 1
    moving = 2
    packing = 3
    seated = 4
    allowed = [waiting, unblocked, moving, packing, seated]
    names = ['waiting','unblocked','moving','packing','seated']
    obstructing_states = [waiting, unblocked, packing]


class BoardingProcess:
    "Data and state of time,people,positions,plane,seats,etc."

    def init_people_and_seats():
        "Create passenger list of people and assigned seats."

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
        people_to_seats = seats[:]
        random.shuffle(people_to_seats)
        people_to_seats = people_to_seats[:npeople]  # people to seats function
        print('People to seats: ',people_to_seats)

        # people and people_to_seats are the only things that will be used later:
        return people, people_to_seats


    def line_people_up_for_boarding(self,queue):
        "State of people, especially their positions, based on seats and boarding order."

        print('Queue = ',queue)
        print('People = ',self.people)
        print('Seat assigned to each person = ',self.people_to_seats)

        # Set the initial full state just before boarding starts
        self.state = [State.waiting for i in self.people]

        self.position = [0 for i in self.people]
        for j in range(len(self.people)):
            self.position[queue[j]]  = -PhysicalConstants.waiting_space*j

        self.goal = [PhysicalConstants.seat_space*s[0] for s in self.people_to_seats]  # Position of goal seat

        # Person immediately ahead or behind in line, or -1 if none
        self.ahead = [-1 for i in self.people]
        self.behind = [-1 for i in self.people]
        for i in range(1,len(self.people)):
            self.ahead[queue[i]] = queue[i-1]
            self.behind[queue[i-1]] = queue[i]


    def reset_all_timers(self):
        self.stime = [0 for i in self.people] #snap time; last time this person was looked at
        self.time = 0 # Global time
        self.ntime = {} # ntime; time at which this person is scheduled to next do something


    def __init__(self):
        self.people, self.people_to_seats = BoardingProcess.init_people_and_seats()

        self.state = self.ahead = self.behind = [0 for i in self.people] #ints
        self.position = self.goal = self.stime = [0.0 for i in self.people] #floats

        # Line everyone up physically acording to a random order
        queue = self.people[:]
        random.shuffle(queue)
        self.line_people_up_for_boarding(queue)

        self.reset_all_timers()


    def printstate(self):
        print('  CURRENT STATE:')
        print('     time = ',self.time)
        print('    ','(person,seat,state,position,goal,stime,ahead,behind)')

        for q in sorted([p for p in self.people], key = lambda x: -self.position[x]):
            if self.state[q] != State.seated:
                print('    ',(q,self.people_to_seats[q],State.names[self.state[q]],self.position[q],
                    self.goal[q],self.stime[q],self.ahead[q],self.behind[q]))
        print('  ','PRIORITY QUEUE OF NEXT ACTIONS:')
        for (v,k) in sorted([(v,k) for (k,v) in  self.ntime.items()],key=lambda x:x[0]):
            print ('    ',(v,k))


    def first_in_line(self):
        return max([p for p in self.people], key = lambda x: self.position[x])


    def unlock_person_at_front(self):
        self.state[self.first_in_line()] = State.unblocked
        self.ntime[self.first_in_line()] = self.time + PhysicalConstants.reflex_time


bp = BoardingProcess()

print('THE INITIAL STATE:')
bp.printstate()

bp.unlock_person_at_front()

print('STATE AFTER UNBLOCKIG FIRST PERSON')
bp.printstate()


def time_to_reach_seat_or_obstruction(p):
    "Calculate time to next action for person p, due to either block ahead, or reaching seat."

    assert util.nearzero(bp.stime[p] - bp.time)
    time_to_seat = (bp.goal[p]-bp.position[p])/PhysicalConstants.walking_speed
    time_to_event = time_to_seat
    if (bp.ahead[p]>=0) & (bp.state[bp.ahead[p]] in State.obstructing_states):
        dist_to_obstruction = (bp.position[bp.ahead[p]]-PhysicalConstants.waiting_space-bp.position[p])
        time_to_obstruction = dist_to_obstruction/PhysicalConstants.walking_speed
        if time_to_obstruction < time_to_seat:
            time_to_event = time_to_obstruction
    return bp.time + time_to_event


def whats_next_seat_or_obstruction(p):
    assert util.nearzero(bp.stime[p] - bp.time)
    time_to_seat = (bp.goal[p]-bp.position[p])/PhysicalConstants.walking_speed
    next_state = State.packing
    if (bp.ahead[p]>=0) & (bp.state[bp.ahead[p]] in State.obstructing_states):
        dist_to_obstruction = (bp.position[bp.ahead[p]]-PhysicalConstants.waiting_space-bp.position[p])
        time_to_obstruction = dist_to_obstruction/PhysicalConstants.walking_speed
        if time_to_obstruction < time_to_seat:
            next_state = State.waiting
    return next_state


def step_forward_to_time(i,t):
    assert bp.state[i] in State.allowed
    assert t >= bp.stime[i]  # Only step forward in time
    if bp.state[i] == State.moving:
        bp.position[i] += PhysicalConstants.walking_speed * (t-bp.stime[i])
        assert bp.position[i] <= bp.goal[i] + util.epsilon
    bp.stime[i] = t


while not all([s==State.seated for s in bp.state]):

    (next_time,next_actor) = min([(v,k) for (k,v) in  bp.ntime.items()],key=lambda x:x[0])
    print ('time,steptime,next_actor = ',bp.time,next_time - bp.time, next_actor)
    assert next_time >= bp.time

    bp.time = next_time

    step_forward_to_time(next_actor,bp.time)

    # Update the state of next actor, and his effects on people behind
    SNA = bp.state[next_actor]
    assert util.nearzero(bp.time - bp.ntime[next_actor])
    if SNA == State.unblocked:
        bp.state[next_actor] = State.moving

        bp.ntime[next_actor] = time_to_reach_seat_or_obstruction(next_actor)

        BNA = bp.behind[next_actor]
        if (BNA >= 0):
            step_forward_to_time(BNA,bp.time)
            if bp.state[BNA]==State.waiting:
                bp.state[BNA] = State.unblocked
                bp.ntime[BNA] = bp.time + PhysicalConstants.reflex_time
            elif bp.state[BNA] == State.moving:
                bp.ntime[BNA] = time_to_reach_seat_or_obstruction(BNA)

    elif SNA == State.moving:
        # first determine if we will be transitioning to waiting_state or to packing_state
        time_next_event = time_to_reach_seat_or_obstruction(next_actor)
        next_state = whats_next_seat_or_obstruction(next_actor)
        assert util.nearzero(time_next_event - bp.time)
        if next_state == State.packing:
            assert util.nearzero(bp.position[next_actor]-bp.goal[next_actor])
            bp.state[next_actor] = State.packing
            bp.ntime[next_actor] = bp.time + PhysicalConstants.packing_time
        elif next_state == State.waiting:
            bp.state[next_actor] = State.waiting
            del bp.ntime[next_actor]
        else:
            assert False
        BNA = bp.behind[next_actor]
        if (BNA >= 0) & (bp.state[BNA] == State.moving):
            step_forward_to_time(BNA,bp.time)
            bp.ntime[BNA] = time_to_reach_seat_or_obstruction(BNA)

    elif SNA == State.packing:
        bp.state[next_actor] = State.seated
        del bp.ntime[next_actor]
        if bp.ahead[next_actor]>=0:
            bp.behind[bp.ahead[next_actor]] = bp.behind[next_actor]
        BNA = bp.behind[next_actor]
        if BNA>=0:
            bp.ahead[BNA] = bp.ahead[next_actor]
            if bp.state[BNA] == State.moving:
                step_forward_to_time(BNA,bp.time)
                bp.ntime[BNA] = time_to_reach_seat_or_obstruction(BNA)
            if bp.state[BNA] == State.waiting:
                bp.state[BNA] = State.unblocked
                bp.ntime[BNA] = bp.time + PhysicalConstants.reflex_time
        bp.ahead[next_actor] = -1
        bp.behind[next_actor] = -1
    else:
        print (SNA)
        assert False

    bp.printstate()

print('FINAL TIME: ', bp.time)
