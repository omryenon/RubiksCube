
import sys
import time


# ============================================================================
# get_arg() returns command line arguments.
# ============================================================================
def get_arg(index, default=None):
    '''Returns the command-line argument, or the default if not provided'''
    return sys.argv[index] if len(sys.argv) > index else default


# ============================================================================
# List of possible moves
# https://ruwix.com/online-puzzle-simulators/2x2x2-pocket-cube-simulator.php
#
# Each move permutes the tiles in the current state to produce the new state
# ============================================================================

# Global variables:

# Backtrack:

depthBound=1
verbose = False
failCounter=0
backtrackCalls=0
finalStateList=[]


# Graph search:

generatedNodes = 0
expandedNodes = 0
RULES = {
    "U": [2, 0, 3, 1, 20, 21, 6, 7, 4, 5, 10, 11,
          12, 13, 14, 15, 8, 9, 18, 19, 16, 17, 22, 23],
    "U'": [1, 3, 0, 2, 8, 9, 6, 7, 16, 17, 10, 11,
           12, 13, 14, 15, 20, 21, 18, 19, 4, 5, 22, 23],
    "R": [0, 9, 2, 11, 6, 4, 7, 5, 8, 13, 10, 15,
          12, 22, 14, 20, 16, 17, 18, 19, 3, 21, 1, 23],
    "R'": [0, 22, 2, 20, 5, 7, 4, 6, 8, 1, 10, 3,
           12, 9, 14, 11, 16, 17, 18, 19, 15, 21, 13, 23],
    "F": [0, 1, 19, 17, 2, 5, 3, 7, 10, 8, 11, 9,
          6, 4, 14, 15, 16, 12, 18, 13, 20, 21, 22, 23],
    "F'": [0, 1, 4, 6, 13, 5, 12, 7, 9, 11, 8, 10,
           17, 19, 14, 15, 16, 3, 18, 2, 20, 21, 22, 23],
    "D": [0, 1, 2, 3, 4, 5, 10, 11, 8, 9, 18, 19,
          14, 12, 15, 13, 16, 17, 22, 23, 20, 21, 6, 7],
    "D'": [0, 1, 2, 3, 4, 5, 22, 23, 8, 9, 6, 7,
           13, 15, 12, 14, 16, 17, 10, 11, 20, 21, 18, 19],
    "L": [23, 1, 21, 3, 4, 5, 6, 7, 0, 9, 2, 11,
          8, 13, 10, 15, 18, 16, 19, 17, 20, 14, 22, 12],
    "L'": [8, 1, 10, 3, 4, 5, 6, 7, 12, 9, 14, 11,
           23, 13, 21, 15, 17, 19, 16, 18, 20, 2, 22, 0],
    "B": [5, 7, 2, 3, 4, 15, 6, 14, 8, 9, 10, 11,
          12, 13, 16, 18, 1, 17, 0, 19, 22, 20, 23, 21],
    "B'": [18, 16, 2, 3, 4, 0, 6, 1, 8, 9, 10, 11,
           12, 13, 7, 5, 14, 17, 15, 19, 21, 23, 20, 22]
}

'''
sticker indices:

        0  1
        2  3
16 17   8  9   4  5  20 21                    
18 19  10 11   6  7  22 23
       12 13
       14 15
F:       
        0  1
       19 17
16 12  10  8   2  5  20 21                    
18 13  11  9   3  7  22 23
        6  4
       14 15

       [0, 1, 19, 17, 2, 5, 3, 7, 10, 8, 11, 9,
          6, 4, 14, 15, 16, 12, 18, 13, 20, 21, 22, 23],

face colors:

    0
  4 2 1 5
    3

rules:
[ U , U', R , R', F , F', D , D', L , L', B , B']
'''


class Cube:

    def __init__(self, config="WWWW RRRR GGGG YYYY OOOO BBBB"):

        # ============================================================================
        # tiles is a string without spaces in it that corresponds to config
        # ============================================================================

        self.config = config
        self.tiles = config.replace(" ", "")

        self.depth = 0
        self.rule = ""
        self.parent = None

    def __str__(self):
        # ============================================================================
        # separates tiles into chunks of size 4 and inserts a space between them
        # for readability
        # ============================================================================
        chunks = [self.tiles[i:i + 4] + " " for i in range(0, len(self.tiles), 4)]
        return "".join(chunks)

    def __eq__(self, state):
        return (self.tiles == state.tiles) or (self.config == state.config)

    def toGrid(self):
        # ============================================================================
        # produces a string portraying the cube in flattened display form, i.e.,
        #
        #	   RW
        #	   GG
        #	BR WO YO GY
        #	WW OO YG RR
        #	   BB
        #	   BY
        # ============================================================================

        def part(face, portion):
            # ============================================================================
            # This routine converts the string corresponding to a single face to a
            # 2x2 grid
            #    face is in [0..5] if it exists, -1 if not
            #    portion is either TOP (=0) or BOTTOM (=1)
            # Example:
            # If state.config is "RWGG YOYG WOOO BBBY BRWW GYRR".
            #   part(0,TOP) is GW , part(0,BOTTOM) is WR, ...
            #   part(5,TOP) is BR , part(5,BOTTOM) is BB
            # ============================================================================

            result = "   "
            if face >= 0:
                offset = 4 * face + 2 * portion
                result = self.tiles[offset] + self.tiles[offset + 1] + " "
            return result

        TOP = 0
        BOTTOM = 1

        str = ""
        for row in [TOP, BOTTOM]:
            str += part(-1, row) + part(0, row) + \
                   part(-1, row) + part(-1, row) + "\n"

        for row in [TOP, BOTTOM]:
            str += part(4, row) + part(2, row) + \
                   part(1, row) + part(5, row) + "\n"

        for row in [TOP, BOTTOM]:
            str += part(-1, row) + part(3, row) + \
                   part(-1, row) + part(-1, row) + "\n"

        return str

    def applicableRules(self):
        return list(RULES.keys())

    def applyRule(self, rule):
        # ============================================================================
        # apply a rule to a state
        # ============================================================================
        newtiles = ""
        for i in range(24):
            newtiles += self.tiles[RULES.get(rule)[i]]
        cubix = Cube(newtiles)
        cubix.rule = rule
        return cubix

    def goal(self):
        if len(set(self.tiles[0:4])) == 1 & len(set(self.tiles[4:8])) == 1 & len(set(self.tiles[8:12])) == 1 & len(
                set(self.tiles[12:16])) == 1 & len(set(self.tiles[16:20])) == 1 & len(set(self.tiles[20:24])) == 1:
            return True
        return False

    def countNode(self):
        count=0
        if len(set(self.tiles[0:4])) != 1:
            count +=1
        if len(set(self.tiles[4:8])) != 1:
            count += 1
        if len(set(self.tiles[8:12])) != 1:
            count += 1
        if len(set(self.tiles[12:16])) != 1:
            count += 1
        if len(set(self.tiles[16:20])) != 1:
            count += 1
        if len(set(self.tiles[20:24])) != 1:
            count += 1
        # return self.depth + (10 * count)
        # other heuristic but not really good: average of unique colors on each square
        average=0
        average += len(set(self.tiles[0:4]))
        average += len(set(self.tiles[4:8]))
        average += len(set(self.tiles[8:12]))
        average += len(set(self.tiles[12:16]))
        average += len(set(self.tiles[16:20]))
        average += len(set(self.tiles[20:24]))
        average = average/6
        return self.depth + average + count*10

def h(list):

    min = 0
    for i in range(len(list)):
        if list[i].countNode() < list[min].countNode():
            temp = list[i]
            list[i] = list[min]
            list[min]= temp
            min=i
    return list

def graphSearch(state=Cube()):
    global expandedNodes
    global generatedNodes
    goalnode = state
    open = [state]
    generatedNodes += 1
    close = []
    while len(open) != 0:
        s = open[0]
        open = open[1:]
        close = close + [s]
        expandedNodes += 1
        if s.goal():
            goalnode = s
            break
        for r in s.applicableRules():
            si = s.applyRule(r)
            if si not in open + close:
                si.parent = s
                si.depth = s.depth + 1
                open = open + [si]
                generatedNodes += 1
                open = h(open)
            elif si in open:
                if si.depth > s.depth + 1:
                    si.parent = s
                    si.depth = s.depth + 1
            elif si in close:
                if si.depth > s.depth + 1:
                    si.parent = s
                    si.depth = s.depth + 1
                    for r in si.applicableRules():
                        si.applyRule(r).depth += 1
    if goalnode.goal():
        path = []
        while goalnode is not None:
            path = [goalnode] + path
            goalnode = goalnode.parent
        print("SOLVED!")
        return path
    else:
        return "No solution"

def BFS(state=Cube()):
    global expandedNodes
    global generatedNodes
    goalnode = state
    open = [state]
    generatedNodes += 1
    close = []
    while len(open) != 0:
        s = open[0]
        open = open[1:]
        close = close + [s]
        expandedNodes += 1
        if s.goal():
            goalnode = s
            break
        for r in s.applicableRules():
            si = s.applyRule(r)
            if si not in open + close:
                si.parent = s
                si.depth = s.depth + 1
                open = open + [si]
                generatedNodes += 1
            elif si in open:
                if si.depth > s.depth + 1:
                    si.parent = s
                    si.depth = s.depth + 1
            elif si in close:
                if si.depth > s.depth + 1:
                    si.parent = s
                    si.depth = s.depth + 1
                    for r in si.applicableRules():
                        si.applyRule(r).depth += 1
    if goalnode.goal():
        path = []
        while goalnode is not None:
            path = [goalnode] + path
            goalnode = goalnode.parent
        print("SOLVED!")
        return path
    else:
        return "No solution"

def DFS(state=Cube()):
    global expandedNodes
    global generatedNodes
    goalnode = state
    open = [state]
    generatedNodes += 1
    close = []
    while len(open) != 0:
        s = open[0]
        open = open[1:]
        close = close + [s]
        expandedNodes += 1
        if s.goal():
            goalnode = s
            break
        for r in s.applicableRules():
            si = s.applyRule(r)
            if si not in open + close:
                si.parent = s
                si.depth = s.depth + 1
                open = [si] + open
                generatedNodes += 1
            elif si in open:
                if si.depth > s.depth + 1:
                    si.parent = s
                    si.depth = s.depth + 1
            elif si in close:
                if si.depth > s.depth + 1:
                    si.parent = s
                    si.depth = s.depth + 1
                    for r in si.applicableRules():
                        si.applyRule(r).depth += 1
    if goalnode.goal():
        path = []
        while goalnode is not None:
            path = [goalnode] + path
            goalnode = goalnode.parent
        print("SOLVED!")
        return path
    else:
        return "No solution"



def backtrack(stateList =  [Cube()]):
    global backtrackCalls
    global failCounter
    global finalStateList
    currState = stateList[0]
    restList = stateList[1:]
    if currState.goal():
        return None
    ruleSet = RULES.keys()
    if (currState in restList):
        if verbose:
            print("FAILED-1")
            print("a cycle has occurred")
        failCounter+=1
        return "FAILED-1"
    elif len(ruleSet)==0:
        if verbose:
            print("FAILED-2")
            print("dead end - No solution possible from here")
        failCounter += 1
        return "FAILED-2"
    elif len(stateList) > depthBound:
        if verbose:
            print("FAILED-3")
            print("Passed the depth bound")
        failCounter += 1
        return "FAILED-3"
    elif ruleSet == None:
        if verbose:
            print("FAILED-4")
            print("There are not any possible moves")
        failCounter += 1
        return "FAILED-4"
    else:
        for r in ruleSet:
            # if r.precondition(currState):
            if verbose:
                print("Rule:")
                print(r.__str__())
            newState= currState.applyRule(r)
            if verbose:
                print("State:")
                print(newState.__str__())
            newStateList = [newState] + stateList
            backtrackCalls +=1
            path = backtrack(newStateList)
            if path and len(path) >0 and path[0] != "F" and path!=None :
                return path + [newState.rule]
            elif path==None :
                finalStateList = newStateList
                print("Goal achieved")
                path=[newState.rule]
                return path
        if verbose:
            print("FAILED-5")
            print("Nothing worked")
        failCounter += 1
        return "FAILED-5"

def generateinit():
    state = Cube("GRGR YYYY OGOG BOBO WWWW BRBR")
    state2 = state.applyRule("D")
    state3 = state2.applyRule("F")
    state4 = state3.applyRule("B")
    return state4

def addSpaces(str):
    str1 = str[0:4]
    str2 = str[4:8]
    str3 = str[8:12]
    str4 = str[12:16]
    str5 = str[16:20]
    str6 = str[20:24]
    return Cube(str1 + " " + str2 + " " + str3 + " " + str4 + " " + str5 + " " + str6)

# --------------------------------------------------------------------------------
#  MAIN PROGRAM
# --------------------------------------------------------------------------------

if __name__ == '__main__':

    # ============================================================================
    # Read input from command line:
    #   python3 <this program>.py STATE VERBOSE
    # where
    # STATE is a string prescribing an initial state
    # VERBOSE specifies to enter VERBOSE mode for detailed algorithm tracing.
    # ============================================================================
    CONFIG = get_arg(1)

    VERBOSE = get_arg(2)
    VERBOSE = (VERBOSE == "verbose" or VERBOSE == "v")
    if VERBOSE:
        print("Verbose mode:")
        verbose = True

    # ============================================================================
    # Print list of all rules.
    # ============================================================================
    print("All Rules:\n_________")
    for m in RULES.keys():
        print("  " + str(m) + ": " + str(RULES[m]))

    if (CONFIG != None ):
        if (CONFIG != "-"):
            print("init state is: " + CONFIG)
        else:
            print("init state will be a random value")
    else:
        print("init state will be a random value")
    # ============================================================================
    # Test case: default state is a goal state
    # ============================================================================
    # state = Cube()
    # print(state)
    # if state.goal():
    #     print("SOLVED!")
    # else:
    #     print("NOT SOLVED.")

    # ============================================================================
    # Test case: This state is one move from a goal.
    # Applying the "R" rule should solve the puzzle.

    if (CONFIG != None ):
        if (CONFIG != "-"):
            init = addSpaces(CONFIG)
        else:
            init = generateinit()
    else:
        init = generateinit()

##########################################################################################
    print("Backtrack Function:")
    start2 = time.process_time()
    while 1:
        initstate = init
        # making the initial statelist and calls
        stateList = [initstate]
        backtrackCalls += 1
        finalPath = backtrack(stateList)
        if finalPath[0] == "F":
            print("Depth " + str(depthBound) + " Failed")
        else:
            print("---------Rules-----------------")
            finalPath.reverse()
            for r in finalPath:
                print(r.__str__())

            print("---------States-----------------")
            finalStateList.reverse()
            for s in finalStateList:
                print(s.__str__())

            print("Number of Failures:")
            print(failCounter)
            print("Number of backtrack calls:")
            print(backtrackCalls)
            print("Time of Backtrack Function:")
            print("Depth " + str(depthBound) + " is OK!")
            break
        depthBound += 1
    end2 = time.process_time() - start2
    print(end2)
    # ============================================================================
    print("GraphSearch Function:")
    start = time.process_time()
    list = graphSearch(init)
    end = time.process_time() - start
    print("States:")
    for e in list:
        print(e.__str__())
    print("Rules:")
    for e in list:
        print(e.rule.__str__())
    print("number of nodes that were generated:")
    print(generatedNodes)
    print("number of nodes that were expanded:")
    print(expandedNodes)
    print("Time of GraphSearch Function:")
    print(end)
