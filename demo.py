# Copyright Jade Vinson 2016

import random

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

    waiting = 0     # begin, transitions to unblocked
    unblocked = 1   # transitions to moving
    moving = 2      # transitions to waiting or packing
    packing = 3     # transitions to seated
    seated = 4      # end
    all_states = [waiting, unblocked, moving, packing, seated]
    names = ['waiting','unblocked','moving','packing','seated']
    obstructing_states = [waiting, unblocked, packing]
    nonobstructing_states = [moving, seated]


class AirplaneAndPassengers:
    def people_and_seats():
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


class BoardingProcess:
    "Data and state of time,people,positions,plane,seats,etc, and methods for simulating."

    def __init__(self, people, people_to_seats, queue):
        "Starting lineup of people, positions and timers, based on their seats and boarding order."

        self.people = people[:]
        self.people_to_seats = people_to_seats[:]

        self.state = [State.waiting for i in self.people]

        self.position = [0 for i in self.people]
        for j in range(len(self.people)):
            self.position[queue[j]]  = -PhysicalConstants.waiting_space*j

        self.goal = [PhysicalConstants.seat_space*s[0] for s in self.people_to_seats]  # Position of goal seat

        self.ahead = [-1 for i in self.people]
        self.behind = [-1 for i in self.people]
        for i in range(1,len(self.people)):
            self.ahead[queue[i]] = queue[i-1]
            self.behind[queue[i-1]] = queue[i]

        self.stime = [0 for i in self.people] # snap time when person was last updated
        self.time = 0 # Global time
        self.ntime = {} # ntime; time at which this person is scheduled to next do something


    def unblock_person_at_front(self):
        person_at_front = max([p for p in self.people], key = lambda x: self.position[x])
        assert self.state[person_at_front] == State.waiting
        self.state[person_at_front] = State.unblocked
        self.ntime[person_at_front] = self.time + PhysicalConstants.reflex_time


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


    def time_to_seat(self,p):
        return (self.goal[p]-self.position[p])/PhysicalConstants.walking_speed


    def is_obstruction_ahead(self,p):
        return (self.ahead[p]>=0) & (self.state[self.ahead[p]] in State.obstructing_states)


    def time_to_obstruction(self,p):
        dist_to_obstruction = (self.position[self.ahead[p]]-PhysicalConstants.waiting_space-self.position[p])
        return dist_to_obstruction/PhysicalConstants.walking_speed


    def time_to_reach_seat_or_obstruction(self,p):
        "Calculate time to next action for person p, due to either block ahead, or reaching seat."

        time_to_seat = self.time_to_seat(p)
        time_to_event = time_to_seat
        if self.is_obstruction_ahead(p):
            time_to_obstruction = self.time_to_obstruction(p)
            if time_to_obstruction < time_to_seat:
                time_to_event = time_to_obstruction

        return self.time + time_to_event


    def whats_next_seat_or_obstruction(self,p):
        time_to_seat = self.time_to_seat(p)
        if self.is_obstruction_ahead(p):
            if self.time_to_obstruction(p) < time_to_seat:
                return State.waiting
        return State.packing


    def step_person_forward_to_global_time(self,i):
        assert self.state[i] in State.all_states
        assert self.time >= self.stime[i]  # Only step forward in time, never backward
        if i in self.ntime:
            assert self.time <= self.ntime[i] # Not stepping forward beyond an upcoming event
        if self.state[i] == State.moving:
            self.position[i] += PhysicalConstants.walking_speed * (self.time-self.stime[i])
            assert self.position[i] <= self.goal[i] + util.epsilon
        self.stime[i] = self.time


    def is_boarding_process_complete(self):
        return all([s==State.seated for s in self.state])


    def remove_person_from_lineup(self,p):
            person_behind = self.behind[p]
            person_ahead = self.ahead[p]
            if person_ahead>=0:
                self.behind[person_ahead] = person_behind
            if person_behind>=0:
                self.ahead[person_behind] = person_ahead
            self.ahead[p] = -1
            self.behind[p] = -1


    def process_event_for(self,p):
        # First assert that there is an event to be processed right now,
        # and time is caught up, and remove event from queue
        assert util.nearzero(self.time - self.stime[p])
        assert util.nearzero(self.time - self.ntime[p])
        del self.ntime[p]

        state_before = self.state[p]
        if state_before == State.unblocked:
            self.state[p] = State.moving
            self.ntime[p] = self.time_to_reach_seat_or_obstruction(p)
        elif state_before == State.moving:
            next_state = self.whats_next_seat_or_obstruction(p)
            if next_state == State.packing:
                assert util.nearzero(self.position[p]-self.goal[p])
                self.state[p] = State.packing
                self.ntime[p] = self.time + PhysicalConstants.packing_time
            elif next_state == State.waiting:
                self.state[p] = State.waiting
            else:
                assert False
        elif state_before == State.packing:
            self.state[p] = State.seated
            self.remove_person_from_lineup(p)
        else:
            assert False


    def update_person_based_on_events_ahead(self,p):
        self.step_person_forward_to_global_time(p)
        state_before = self.state[p]
        if state_before == State.waiting:
            a = self.ahead[p]
            if ((a<0) | (self.state[a] in State.nonobstructing_states)
                | (self.position[p] < self.position[a]-PhysicalConstants.waiting_space)):
                self.state[p] = State.unblocked
                self.ntime[p] = self.time + PhysicalConstants.reflex_time
        elif state_before == State.moving:
            self.ntime[p] = self.time_to_reach_seat_or_obstruction(p)
        elif state_before in [State.packing,State.seated,State.unblocked]:
            pass
        else:
            assert False


    def advance_by_one_event(self):
        (next_time,actor) = min([(v,k) for (k,v) in  self.ntime.items()],key=lambda x:x[0])
        person_behind_actor = self.behind[actor]

        print ('time,steptime,actor = ',self.time,next_time - self.time, actor)
        assert next_time >= self.time
        self.time = next_time

        self.step_person_forward_to_global_time(actor)
        self.process_event_for(actor)

        if person_behind_actor >= 0:
            self.update_person_based_on_events_ahead(person_behind_actor)


if (__name__ == '__main__'):

    random.seed(131)

    people, people_to_seats = AirplaneAndPassengers.people_and_seats()
    queue = people[:]
    random.shuffle(queue)

    bp = BoardingProcess(people, people_to_seats, queue)

    print('THE INITIAL STATE:')
    bp.printstate()

    bp.unblock_person_at_front()

    print('STATE AFTER UNBLOCKING FIRST PERSON')
    bp.printstate()

    while not bp.is_boarding_process_complete():
        bp.advance_by_one_event()
        #bp.printstate()

    print('FINAL TIME: ', bp.time)
