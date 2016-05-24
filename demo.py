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
    all_states = [waiting, unblocked, moving, packing, seated]
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


    def unlock_person_at_front(self):
        person_at_front = max([p for p in self.people], key = lambda x: self.position[x])
        assert self.state[person_at_front] == State.waiting
        self.state[person_at_front] = State.unblocked
        self.ntime[person_at_front] = self.time + PhysicalConstants.reflex_time


    def time_to_reach_seat_or_obstruction(self,p):
        "Calculate time to next action for person p, due to either block ahead, or reaching seat."

        assert util.nearzero(self.stime[p] - self.time)
        time_to_seat = (self.goal[p]-self.position[p])/PhysicalConstants.walking_speed
        time_to_event = time_to_seat
        if (self.ahead[p]>=0) & (self.state[self.ahead[p]] in State.obstructing_states):
            dist_to_obstruction = (self.position[self.ahead[p]]-PhysicalConstants.waiting_space-self.position[p])
            time_to_obstruction = dist_to_obstruction/PhysicalConstants.walking_speed
            if time_to_obstruction < time_to_seat:
                time_to_event = time_to_obstruction
        return self.time + time_to_event


    def whats_next_seat_or_obstruction(self,p):
        assert util.nearzero(self.stime[p] - self.time)
        time_to_seat = (self.goal[p]-self.position[p])/PhysicalConstants.walking_speed
        next_state = State.packing
        if (self.ahead[p]>=0) & (self.state[self.ahead[p]] in State.obstructing_states):
            dist_to_obstruction = (self.position[self.ahead[p]]-PhysicalConstants.waiting_space-self.position[p])
            time_to_obstruction = dist_to_obstruction/PhysicalConstants.walking_speed
            if time_to_obstruction < time_to_seat:
                next_state = State.waiting
        return next_state


    def step_forward_to_time(self,i,t):
        assert self.state[i] in State.all_states
        assert t >= self.stime[i]  # Only step forward in time
        if self.state[i] == State.moving:
            self.position[i] += PhysicalConstants.walking_speed * (t-self.stime[i])
            assert self.position[i] <= self.goal[i] + util.epsilon
        self.stime[i] = t


    def is_boarding_process_complete(self):
        return all([s==State.seated for s in self.state])


    def advance_by_one_event_and_aftermath(self):
        (next_time,next_actor) = min([(v,k) for (k,v) in  self.ntime.items()],key=lambda x:x[0])
        print ('time,steptime,next_actor = ',self.time,next_time - self.time, next_actor)
        assert next_time >= self.time

        self.time = next_time

        self.step_forward_to_time(next_actor,self.time)

        # Update the state of next actor, and his effects on people behind
        SNA = self.state[next_actor]
        assert util.nearzero(self.time - self.ntime[next_actor])
        if SNA == State.unblocked:
            self.state[next_actor] = State.moving

            self.ntime[next_actor] = self.time_to_reach_seat_or_obstruction(next_actor)

            BNA = self.behind[next_actor]
            if (BNA >= 0):
                self.step_forward_to_time(BNA,self.time)
                if self.state[BNA]==State.waiting:
                    self.state[BNA] = State.unblocked
                    self.ntime[BNA] = self.time + PhysicalConstants.reflex_time
                elif self.state[BNA] == State.moving:
                    self.ntime[BNA] = self.time_to_reach_seat_or_obstruction(BNA)

        elif SNA == State.moving:
            # first determine if we will be transitioning to waiting_state or to packing_state
            time_next_event = self.time_to_reach_seat_or_obstruction(next_actor)
            next_state = self.whats_next_seat_or_obstruction(next_actor)
            assert util.nearzero(time_next_event - self.time)
            if next_state == State.packing:
                assert util.nearzero(self.position[next_actor]-self.goal[next_actor])
                self.state[next_actor] = State.packing
                self.ntime[next_actor] = self.time + PhysicalConstants.packing_time
            elif next_state == State.waiting:
                self.state[next_actor] = State.waiting
                del self.ntime[next_actor]
            else:
                assert False
            BNA = self.behind[next_actor]
            if (BNA >= 0) & (self.state[BNA] == State.moving):
                self.step_forward_to_time(BNA,self.time)
                self.ntime[BNA] = self.time_to_reach_seat_or_obstruction(BNA)

        elif SNA == State.packing:
            self.state[next_actor] = State.seated
            del self.ntime[next_actor]
            if self.ahead[next_actor]>=0:
                self.behind[self.ahead[next_actor]] = self.behind[next_actor]
            BNA = self.behind[next_actor]
            if BNA>=0:
                self.ahead[BNA] = self.ahead[next_actor]
                if self.state[BNA] == State.moving:
                    self.step_forward_to_time(BNA,self.time)
                    self.ntime[BNA] = self.time_to_reach_seat_or_obstruction(BNA)
                if self.state[BNA] == State.waiting:
                    self.state[BNA] = State.unblocked
                    self.ntime[BNA] = self.time + PhysicalConstants.reflex_time
            self.ahead[next_actor] = -1
            self.behind[next_actor] = -1
        else:
            print (SNA)
            assert False


bp = BoardingProcess()

print('THE INITIAL STATE:')
bp.printstate()

bp.unlock_person_at_front()

print('STATE AFTER UNBLOCKING FIRST PERSON')
bp.printstate()

while not bp.is_boarding_process_complete():
    bp.advance_by_one_event_and_aftermath()
    bp.printstate()

print('FINAL TIME: ', bp.time)
