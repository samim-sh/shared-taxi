from scipy.interpolate import interp1d
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas
import collections
import itertools
import time
import re
import sys
import os
import psutil
import plotly
import openpyxl

# Ask the user for number of taxis and passengers
No_Taxi = int(input('Enter No_Taxi= '))
No_passengers = int(input('Enter No_passengers= '))


def generator(beginning, ending):
    if beginning is None:
        num = 0
    while beginning < ending:
        yield beginning
        beginning += 1


# Disable Prints
def block_print():
    sys.stdout = open(os.devnull, 'w')


# Restore Prints
def enable_print():
    sys.stdout = sys.__stdout__


# Return 2 random integers within a range(start, end)
def random(start, end):
    first, second = np.random.randint(start, end), np.random.randint(start, end)
    return first, second


# Generate a random user at location (x_h, y_h) in a random home area
def sel_Home():
    random_home_area = np.random.choice(Home_list)
    x_h, y_h = random(0, 45)
    x_min_home_area, x_max_home_area = Home[random_home_area][0][0], Home[random_home_area][0][1]
    y_min_home_area, y_max_home_area = Home[random_home_area][1][0], Home[random_home_area][1][1]
    # Check until (x_h, y_h) stand within selected random home area
    while x_min_home_area > x_h or x_h > x_max_home_area or y_min_home_area > y_h or y_h > y_max_home_area:
        x_h, y_h = random(0, 45)
    return x_h, y_h, random_home_area


# Generate a random user at location (x_w, y_w) in a random work area
def sel_Work():
    random_work_area = np.random.choice(Work_list)
    x_w, y_w = random(0, 45)
    x_min_work_area, x_max_work_area = Work[random_work_area][0][0], Work[random_work_area][0][1]
    y_min_work_area, y_max_work_area = Work[random_work_area][1][0], Work[random_work_area][1][1]
    # Check until (x_w, y_w) stand within selected random work area
    while x_min_work_area > x_w or x_w > x_max_work_area or y_min_work_area > y_w or y_w > y_max_work_area:
        x_w, y_w = random(0, 45)
    return x_w, y_w, random_work_area


api = 0


# Calculate and return distance between 2 points (e.g. (x1, y1) and (x2, y2))
def distance(node1, node2):
    global api
    api += 1
    return abs(node1[0]-node2[0])+abs(node1[1]-node2[1])


# Removing selected taxi and passengers by it from taxi, origin and destination dictionaries
def del_dict_item(selected_taxi, comb_dic, index_dic):
    del Taxis[selected_taxi]
    for each_passenger in comb_dic[selected_taxi][index_dic[selected_taxi][0]]:
        del passengers_O[each_passenger]
        del passengers_D[re.sub(r'o', 'd', each_passenger)]


# Calculate and return -traveled distance- for each passenger respectively,
# from dropping on point to dropping off point in sharing mode
def finding_distance_sharing(origin_list, destination_list):
    temp_lst = []  # temp_lst store traveled distance for each passenger until dropping off taxi
    sequence_drop_on_off = origin_list + destination_list
    for passenger in origin_list:
        passenger_sequence = sequence_drop_on_off[origin_list.index(passenger):
                                                  sequence_drop_on_off.index(re.sub(r'o', 'd', passenger))+1]
        each_one_traveled_dist = 0
        for each in range(len(passenger_sequence) - 1):
            if re.findall(r'[a-zA-Z]+', passenger_sequence[each])[0] == 'pd':
                prior = passengers_D[passenger_sequence[each]]
            else:
                prior = passengers_O[passenger_sequence[each]]
            if re.findall(r'[a-zA-Z]+', passenger_sequence[each + 1])[0] == 'pd':
                following = passengers_D[passenger_sequence[each + 1]]
            else:
                following = passengers_O[passenger_sequence[each + 1]]
            each_one_traveled_dist += distance(prior, following)
        temp_lst.append(each_one_traveled_dist)
    return temp_lst


Start = time.time()
# ----------------------------------------------------------------------------------------------------------------------
#                                              Creating Home and Work Area
# ----------------------------------------------------------------------------------------------------------------------
Home = {}
Work = {}
counter = 0
for y in range(0, 31, 15):
    y1, y2 = y, y+15
    for x in range(0, 31, 15):
        x1, x2 = x, x+15
        if counter == 4 or counter == 8:
            Work["w{0}".format(counter+1)] = [(x1, x2), (y1, y2)]
        else:
            Home["h{0}".format(counter+1)] = [(x1, x2), (y1, y2)]
        counter += 1
Home_list = list(Home.keys())
Work_list = list(Work.keys())


# ----------------------------------------------------------------------------------------------------------------------
#                                                Generate Taxi Randomly
# ----------------------------------------------------------------------------------------------------------------------
Taxis = {}
for taxi in generator(1, No_Taxi+1):
    if taxi < (No_Taxi-No_Taxi/5):
        x, y, sel_home = sel_Home()
        Taxis["t{0}".format(taxi)] = (x, y)
    else:
        x, y, sel_work = sel_Work()
        Taxis["t{0}".format(taxi)] = (x, y)


# ----------------------------------------------------------------------------------------------------------------------
#                                                Generate User Randomly
# ----------------------------------------------------------------------------------------------------------------------
Passengers_O = {}
passengers_O = {}
passengers_D = {}
person = 1
while len(passengers_O) != No_passengers:
    # Generate /--one fifth--/ of No_passengers work to home
    if person > int(No_passengers * (1-1/5)):
        x, y, sel_work = sel_Work()
        xx, yy, sel_home = sel_Home()
        if distance((x, y), (xx, yy)) > 10:
            Passengers_O["p{0}_".format(person) + sel_work + '_to_' + sel_home] = (x, y)  # Origin_to_Destination
            passengers_O["po{0}".format(person)] = (x, y)  # Origin
            passengers_D["pd{0}".format(person)] = (xx, yy)  # Destination
            person += 1

    # Generate /--one fifth--/ of (No_passengers*(4 / 5) home to home
    elif person > int(No_passengers * (1-1/5)**2):
        x, y, sel_home = sel_Home()
        xx, yy, sel_home_sec = sel_Home()
        while sel_home_sec == sel_home:
            xx, yy, sel_home_sec = sel_Home()
        if distance((x, y), (xx, yy)) > 10:
            Passengers_O["p{0}_".format(person) + sel_home + '_to_' + sel_home_sec] = (x, y)  # Origin_to_Destination
            passengers_O["po{0}".format(person)] = (x, y)  # Origin
            passengers_D["pd{0}".format(person)] = (xx, yy)  # Destination
            person += 1

    # Generate /--No_passengers*(4 / 5)--/ of No_passengers home to work
    elif person > 0:
        x, y, sel_home = sel_Home()
        xx, yy, sel_work = sel_Work()
        if distance((x, y), (xx, yy)) > 10:
            Passengers_O["p{0}_".format(person) + sel_home + '_to_' + sel_work] = (x, y)  # Origin_to_Destination
            passengers_O["po{0}".format(person)] = (x, y)  # Origin
            passengers_D["pd{0}".format(person)] = (xx, yy)  # Destination
            person += 1

# Compute distance in individual mode(each passenger travel with own vehicle)
traveled_distance = {}
for each_person in passengers_O:
    traveled_distance[each_person] = distance(passengers_O[each_person], passengers_D[re.sub(r'o', 'd', each_person)])


# ----------------------------------------------------------------------------------------------------------------------
#                                                        Plotting
# ----------------------------------------------------------------------------------------------------------------------
fig, ax = plt.subplots()
alpha = [1.9, .6, .25, .15]
patterns = ['+', 'x', '-']
for each_area in generator(1, 10):
    if each_area == 5 or each_area == 9:
        x, y, w, h = Work["w{0}".format(each_area)][0][0], \
                     Work["w{0}".format(each_area)][1][0], \
                     Work["w{0}".format(each_area)][0][1] - Work["w{0}".format(each_area)][0][0], \
                     Work["w{0}".format(each_area)][1][1] - Work["w{0}".format(each_area)][1][0]
        rect = patches.Rectangle((x, y), w, h, facecolor='red', alpha=alpha[3], )
        ax.add_patch(rect)
    else:
        x, y, w, h = Home["h{0}".format(each_area)][0][0], \
                     Home["h{0}".format(each_area)][1][0], \
                     Home["h{0}".format(each_area)][0][1]-Home["h{0}".format(each_area)][0][0], \
                     Home["h{0}".format(each_area)][1][1]-Home["h{0}".format(each_area)][1][0]
        rect = patches.Rectangle((x, y), w, h, alpha=alpha[3], )
        ax.add_patch(rect)


# 1 scatter plot with different text at each data point
i = 0
numbers = np.arange(1, No_Taxi+1)
for x, y in list(Taxis.values()):
    ax.text(x, y, numbers[i])
    i += 1


ax.axis([0, 60, 0, 45])
ax.minorticks_on()

ax.grid(b=True, which="minor", linestyle="--", color='r', alpha=0.4)
ax.grid(b=True, which="major", linestyle="-", linewidth=1, color="b", alpha=0.4)

ax.set_axisbelow(True)
ax.set_xticks(np.arange(0, 46, 15))
ax.set_yticks(np.arange(0, 46, 15))
ax.set_xticks(np.arange(0, 46, 1), minor=True)
ax.set_yticks(np.arange(0, 46, 1), minor=True)

blue_patch = patches.Patch(color='blue', label="Home's Area")
red_patch = patches.Patch(color='red', label="Work's Area")
red_dot = ax.scatter(*zip(*list(Passengers_O.values())), marker='.', c='r', s=10, label="Passenger's Origin")
blue_dot = ax.scatter(*zip(*list(passengers_D.values())), marker='.', c='blue', s=10, label="Passenger's Destination")
green_star = ax.scatter(*zip(*list(Taxis.values())), marker='*', c='fuchsia', s=40, label="Taxi's Location")

# Hex = lambda:np.random.randint(250)
# color = lambda : '#{0:02X}{1:02X}{2:02X}'.format(Hex(), Hex(), Hex())
# for xyo, xyd in zip(list(passengers_O.values()), list(passengers_D.values())):
#     ax.annotate("", xytext=xyo, xy=xyd, arrowprops=dict(color=color(), arrowstyle="->"))
# plt.Circle((0,0),2,color='r',fill=False,clip_on=False)
# ax.add_artist(cc)
ax.legend(handles=[blue_patch, red_patch, red_dot, blue_dot, green_star], loc='best', title='Legend')

# Copy main dictionaries for using next for loops (SIF)
fix1, fix2, fix3 = Taxis.copy(), passengers_O.copy(), passengers_D.copy()

# Create file for writing print lines in a text file
file = open('/home/samim/PycharmProjects/SharedTaxi/log.txt', 'w')
# Writing in log.txt file
file.write('{0}\n\n{1}\n\n{2}\n\n{3}\n\n'.format(Passengers_O, fix2, fix3, fix1))

# y_Traveled_Distance == Sharing Mode
# y_Traveled_distance == Sharing Mode + Individual Mode
# y_traveled_distance == Individual Mode
No_riders_list, No_zero_list, No_one_list, No_two_list, No_three_list, No_four_list = [], [], [], [], [], []
y_Traveled_Distance, y_Traveled_distance, y_traveled_distance = [], [], []

# Create excel file for results (output.xlsx)
excel_writer = pandas.ExcelWriter('/home/samim/PycharmProjects/SharedTaxi/output.xlsx')

# # Create excel file for clustering (clustering.xlsx)
# excel_writer_clustering = pandas.ExcelWriter('/home/samim/PycharmProjects/SharedTaxi/clustering.xlsx')

# Data frame for active cars in system
df_active_cars = pandas.DataFrame(columns=['No_zero',
                                           'No_one',
                                           'No_two',
                                           'No_three',
                                           'No_four',
                                           'Sum_taxi',
                                           'Sum_passenger',
                                           'Nan',
                                           'Missing',
                                           'Total'])
# print(api)
api_list, api_fix, elapsed_time, rss = [], api, [], []
# For loop to find optimum SIF ======================================================== Sharing importance factor == SIF
for SIF in [round(i, 1) for i in np.linspace(1, 2.5, 16)]:

    start = time.time()
    api = api_fix

    # Writing in log.txt file
    file.write((('\n\n*\n*\n SIF = {0}\n*\n*\n'.format(SIF)).replace(' ', ' ' * 40, 1)).replace('*', '*' * 100, 4))

    # Data frame for results with headers
    df = pandas.DataFrame(columns=['Taxi',
                                   'Sequence at the origin', 'Sequence at the destination',
                                   'to first rider', 'origin', 'transfer', 'destination',
                                   '(sharing)', ' ', ' ', ' ',
                                   '(individual)', ' ', ' ', ' ',
                                   'Sharing/individual', ' ', ' ', ' '])
    df.loc[' '] = [' ',
                   ' ', ' ',
                   ' ', ' ', ' ', ' ',
                   'P1', 'P2', 'P3', 'P4',
                   'P1', 'P2', 'P3', 'P4',
                   'P1', 'P2', 'P3', 'P4']

    # # ========================================================================================================
    # # ========================================================================================================Clustering
    # # ========================================================================================================
    # df_clustering = pandas.DataFrame(columns=['Taxi',
    #                                           'Riders',
    #                                           'Origin',
    #                                           'CoM',
    #                                           'Destination',
    #                                           'CoM'])

    # For each SIF we should Retrieve Taxis, passengers_O and passengers_D dictionaries
    Taxis, passengers_O, passengers_D = fix1.copy(), fix2.copy(), fix3.copy()

    No_zero, No_one, No_two, No_three, No_four = 0, 0, 0, 0, 0  # Number of taxis with this riders
    Traveled_Distance = {}  # Distance each taxi travel in sharing mode

    nan_passenger = []
    # Check all taxis, each one of them
    for each_taxi in generator(0, len(Taxis)):
        check = False  # Check if there is at least one taxi in Defaultdict_comb_loc_com_cons_min dictionary
        check_3 = False  # Check if there is at least one taxi in Defaultdict_comb_loc_com_cons_min_3 dictionary
        # Writing in log.txt file
        # file.write((('\n\n*\n Taxi = {}\n'.format(each_taxi+1)).replace(' ', ' ' * 40, 1)).replace('*', '*' * 100, 2))

        # Putting possible riders in taxi's list
        # (i.e. if rider be in catchment area of taxi, it will be put in taxi's list)
        Defaultdict = collections.defaultdict(list)
        for j in Taxis:
            catchment_area = patches.Circle(Taxis[j], radius=3)
            for each_person in passengers_O:
                if catchment_area.contains_point(passengers_O[each_person]):
                    Defaultdict[j].append(each_person)
        # Writing in log.txt file
        # file.write('{0:41} ::= {1}\n'.format('Defaultdict', dict(Defaultdict)))
        # --------------------------------------------------------------------------------------------------------------
        #                                                   4
        # --------------------------------------------------------------------------------------------------------------
        # Find 4-combination of riders for each taxi
        Defaultdict_comb = collections.defaultdict(list)
        for i in Defaultdict:
            if len(Defaultdict[i]) >= 4:
                for j in itertools.combinations(Defaultdict[i], 4):
                    Defaultdict_comb[i].append(j)
        # Writing in log.txt file
        # file.write('{0:41} ::= {1}\n'.format('Defaultdict_comb', dict(Defaultdict_comb)))

        # Origin 4-coordinates (from passenger_O dictionary) for 4-combination of riders for each taxi
        Defaultdict_comb_loc = collections.defaultdict(list)
        for i in Defaultdict_comb:
            for j in range(len(Defaultdict_comb[i])):
                list_temporary = []
                for k in range(len(Defaultdict_comb[i][j])):
                    list_temporary.append(passengers_O[Defaultdict_comb[i][j][k]])
                Defaultdict_comb_loc[i].append(list_temporary)
        # Writing in log.txt file
        # file.write('{0:41} ::= {1}\n'.format('Defaultdict_comb_loc', dict(Defaultdict_comb_loc)))

        # Destination 4-coordinates (from passenger_D dictionary) for 4-combination of riders for each taxi
        Des_Defaultdict_comb_loc = collections.defaultdict(list)
        for i in Defaultdict_comb:
            for j in range(len(Defaultdict_comb[i])):
                list_temporary = []
                for k in range(len(Defaultdict_comb[i][j])):
                    list_temporary.append(passengers_D[re.sub(r'o', 'd', Defaultdict_comb[i][j][k])])
                Des_Defaultdict_comb_loc[i].append(list_temporary)
        # Writing in log.txt file
        # file.write('{0:41} ::= {1}\n'.format('Des_Defaultdict_comb_loc', dict(Des_Defaultdict_comb_loc)))

        # Calculating center of points for each group of riders for each taxi in origin
        Defaultdict_comb_loc_com = collections.defaultdict(list)
        for i in Defaultdict_comb_loc:
            Defaultdict_comb_loc_com[i].append((np.array(Defaultdict_comb_loc[i]).mean(axis=1)).tolist())
        # Writing in log.txt file
        # file.write('{0:41} ::= {1}\n'.format('Defaultdict_comb_loc_com', dict(Defaultdict_comb_loc_com)))

        # Calculating center of points for each group of riders for each taxi in destination
        Des_Defaultdict_comb_loc_com = collections.defaultdict(list)
        for i in Defaultdict_comb_loc:
            Des_Defaultdict_comb_loc_com[i].append((np.array(Des_Defaultdict_comb_loc[i]).mean(axis=1)).tolist())
        # Writing in log.txt file
        # file.write('{0:41} ::= {1}\n'.format('Des_Defaultdict_comb_loc_com', dict(Des_Defaultdict_comb_loc_com)))

        # --------------------------------------------------------------------------------------------------------------
        #                   Calculating constraints (const_origin + const_taxi + const_destination)
        # --------------------------------------------------------------------------------------------------------------
        Defaultdict_comb_loc_com_cons = collections.defaultdict(list)
        for i in Defaultdict_comb_loc_com:
            for j in range(len(Defaultdict_comb_loc[i])):
                Constraint = 0
                for k in range(len(Defaultdict_comb_loc[i][j])):
                    Constraint += distance(Defaultdict_comb_loc_com[i][0][j], Defaultdict_comb_loc[i][j][k]) + \
                                 distance(Des_Defaultdict_comb_loc_com[i][0][j], Des_Defaultdict_comb_loc[i][j][k])
                Defaultdict_comb_loc_com_cons[i].append(Constraint +
                                                        distance(Defaultdict_comb_loc_com[i][0][j], Taxis[i]))
        # Writing in log.txt file
        # file.write('{0:41} ::= {1}\n'.format('Defaultdict_comb_loc_com_cons', dict(Defaultdict_comb_loc_com_cons)))

        # Minimum values of Constraints
        Defaultdict_comb_loc_com_cons_min = collections.defaultdict(list)
        for i in Defaultdict_comb_loc_com_cons:
            Defaultdict_comb_loc_com_cons_min[i].append(min(Defaultdict_comb_loc_com_cons[i]))
        # If Defaultdict_comb_loc_com_cons dictionary be empty then Defaultdict_comb_loc_com_cons_min will be empty
        # i.e. minimum calculating get ValueError so we can't calculate four in line 445
        try:
            minimum = min(Defaultdict_comb_loc_com_cons_min, key=Defaultdict_comb_loc_com_cons_min.get)
            # Writing in log.txt file
            # file.write('{0:41} ::= {1}\n'.format('Defaultdict_comb_loc_com_cons_min',
            #                                      dict(Defaultdict_comb_loc_com_cons_min)))
            file.write('{0:41} ::= {1}\n'.format('4', minimum))
        except ValueError:
            check = True

        # Index of minimum values of Constraints
        Defaultdict_comb_loc_com_cons_min_index = collections.defaultdict(list)
        for i in Defaultdict_comb_loc_com_cons:
            index = Defaultdict_comb_loc_com_cons[i].index(min(Defaultdict_comb_loc_com_cons[i]))
            Defaultdict_comb_loc_com_cons_min_index[i].append(index)
        # Writing in log.txt file
        # file.write('{0:41} ::= {1}\n'.format('Defaultdict_comb_loc_com_cons_min_index',
        #                                      dict(Defaultdict_comb_loc_com_cons_min_index)))

        # --------------------------------------------------------------------------------------------------------------
        #                                                  3
        # --------------------------------------------------------------------------------------------------------------
        # Find 3-combination of riders for each taxi
        Defaultdict_comb_3 = collections.defaultdict(list)
        for i in Defaultdict:
            if len(Defaultdict[i]) >= 3:
                for j in itertools.combinations(Defaultdict[i], 3):
                    Defaultdict_comb_3[i].append(j)
        # Writing in log.txt file
        # file.write('{0:41} ::= {1}\n'.format('Defaultdict_comb_3', dict(Defaultdict_comb_3)))

        # Origin 3-coordinates (from passenger_O dictionary) for 3-combination of riders for each taxi
        Defaultdict_comb_loc_3 = collections.defaultdict(list)
        for i in Defaultdict_comb_3:
            for j in range(len(Defaultdict_comb_3[i])):
                list_temporary = []
                for k in range(len(Defaultdict_comb_3[i][j])):
                    list_temporary.append(passengers_O[Defaultdict_comb_3[i][j][k]])
                Defaultdict_comb_loc_3[i].append(list_temporary)
        # Writing in log.txt file
        # file.write('{0:41} ::= {1}\n'.format('Defaultdict_comb_loc_3', dicr(Defaultdict_comb_loc_3)))

        # Destination 3-coordinates (from passenger_D dictionary) for 3-combination of riders for each taxi
        Des_Defaultdict_comb_loc_3 = collections.defaultdict(list)
        for i in Defaultdict_comb_3:
            for j in range(len(Defaultdict_comb_3[i])):
                list_temporary = []
                for k in range(len(Defaultdict_comb_3[i][j])):
                    list_temporary.append(passengers_D[re.sub(r'o', 'd', Defaultdict_comb_3[i][j][k])])
                Des_Defaultdict_comb_loc_3[i].append(list_temporary)
        # Writing in log.txt file
        # file.write('{0:41} ::= {1}\n'.format('Des_Defaultdict_comb_loc_3', dict(Des_Defaultdict_comb_loc_3)))

        # Calculating center of points for each group of riders for each taxi in origin
        Defaultdict_comb_loc_com_3 = collections.defaultdict(list)
        for i in Defaultdict_comb_loc_3:
            Defaultdict_comb_loc_com_3[i].append((np.array(Defaultdict_comb_loc_3[i]).mean(axis=1)).tolist())
        # Writing in log.txt file
        # file.write('{0:41} ::= {1}\n'.format('Defaultdict_comb_loc_com_3', dict(Defaultdict_comb_loc_com_3)))

        # Calculating center of points for each group of riders for each taxi in destination
        Des_Defaultdict_comb_loc_com_3 = collections.defaultdict(list)
        for i in Defaultdict_comb_loc_3:
            Des_Defaultdict_comb_loc_com_3[i].append((np.array(Des_Defaultdict_comb_loc_3[i]).mean(axis=1)).tolist())
        # Writing in log.txt file
        # file.write('{0:41} ::= {1}\n'.format('Des_Defaultdict_comb_loc_com_3', dict(Des_Defaultdict_comb_loc_com_3)))

        # --------------------------------------------------------------------------------------------------------------
        #                   Calculating constraints_3 (const_origin + const_taxi + const_destination)
        # --------------------------------------------------------------------------------------------------------------
        Defaultdict_comb_loc_com_cons_3 = collections.defaultdict(list)
        for i in Defaultdict_comb_loc_com_3:
            for j in range(len(Defaultdict_comb_loc_3[i])):
                Constraint = 0
                for k in range(len(Defaultdict_comb_loc_3[i][j])):
                    Constraint += distance(Defaultdict_comb_loc_com_3[i][0][j], Defaultdict_comb_loc_3[i][j][k]) + \
                                 distance(Des_Defaultdict_comb_loc_com_3[i][0][j], Des_Defaultdict_comb_loc_3[i][j][k])
                # ================================================================================================== SIF
                Defaultdict_comb_loc_com_cons_3[i].append(SIF*(Constraint +
                                                               distance(Defaultdict_comb_loc_com_3[i][0][j], Taxis[i])))
        # Writing in log.txt file
        # file.write('{0:41} ::= {1}\n'.format('Defaultdict_comb_loc_com_cons_3', dict(Defaultdict_comb_loc_com_cons_3)))

        # Minimum values of Constraints_3
        Defaultdict_comb_loc_com_cons_min_3 = collections.defaultdict(list)
        for i in Defaultdict_comb_loc_com_cons_3:
            Defaultdict_comb_loc_com_cons_min_3[i].append(min(Defaultdict_comb_loc_com_cons_3[i]))
        # If Defaultdict_comb_loc_com_cons_3 dictionary be empty then Defaultdict_comb_loc_com_cons_min_3 will be empty
        # i.e. minimum_3 calculating get ValueError so we can't calculate three in line 449
        try:
            minimum_3 = min(Defaultdict_comb_loc_com_cons_min_3, key=Defaultdict_comb_loc_com_cons_min_3.get)
            # Writing in log.txt file
            # file.write('{0:41} ::= {1}\n'.format('Defaultdict_comb_loc_com_cons_min_3',
            #                                      dict(Defaultdict_comb_loc_com_cons_min_3)))
            file.write('{0:41} ::= {1}\n'.format('3', minimum_3))
        except ValueError:
            check_3 = True

        # Index of minimum values of Constraints_3
        Defaultdict_comb_loc_com_cons_min_index_3 = collections.defaultdict(list)
        for i in Defaultdict_comb_loc_com_cons_3:
            index = Defaultdict_comb_loc_com_cons_3[i].index(min(Defaultdict_comb_loc_com_cons_3[i]))
            Defaultdict_comb_loc_com_cons_min_index_3[i].append(index)
        # Writing in log.txt file
        # file.write('{0:41} ::= {1}\n'.format('Defaultdict_comb_loc_com_cons_min_index_3',
        #                                      dict(Defaultdict_comb_loc_com_cons_min_index_3)))

        # --------------------------------------------------------------------------------------------------------------
        # If Defaultdict_comb_loc_com_cons and Defaultdict_comb_loc_com_cons_3 dictionaries be empty then terminate loop
        # i.e. if there are no riders in catchment area of any taxis then stop this loop and go for new SIF
        if not bool(Defaultdict_comb_loc_com_cons) and not bool(Defaultdict_comb_loc_com_cons_3):
            # Writing in log.txt file
            file.write('\n{}\n\n'.format('There is no possible taxi to choose.'))
            break
        # --------------------------------------------------------------------------------------------------------------
        #                                  Comparision minimum of 3 and 4 riders
        # --------------------------------------------------------------------------------------------------------------
        try:
            four = Defaultdict_comb_loc_com_cons[minimum][Defaultdict_comb_loc_com_cons_min_index[minimum][0]] / 4
        except (IndexError, NameError):
            four = 1000
        try:
            three = Defaultdict_comb_loc_com_cons_3[minimum_3][Defaultdict_comb_loc_com_cons_min_index_3[minimum_3][0]] / 3
        except (IndexError, NameError):
            three = 1000
        # Writing in log.txt file
        file.write('{0:41} ::= {1}\n'.format('four', four))
        file.write('{0:41} ::= {1}\n'.format('three', three))

        # We want to know do we have any taxi with 4 riders, by boolean operator (check)
        if four <= three and not check:
            # Writing in log.txt file
            file.write('Taxi {0} is chosen with 4 passenger.\n'.format(minimum))
            No_four += 1
            # ----------------------------------------------------------------------------------------------------------
            #                                       Shortest path (Start)
            # ----------------------------------------------------------------------------------------------------------
            # path_finding dictionary has two keys {1:[origin sequence], 2:[destination sequence]}
            path_finding = collections.defaultdict(list)
            # Find chosen combination from Defaultdict_comb dictionary
            chosen_passenger = Defaultdict_comb[minimum][Defaultdict_comb_loc_com_cons_min_index[minimum][0]]
            for each_key in chosen_passenger:
                path_finding[1].append(each_key)
                path_finding[2].append(re.sub(r'o', 'd', each_key))
            # Writing in log.txt file
            file.write('{0:41} ::= {1}\n'.format('path_finding', path_finding))

            # Find permutation of riders for chosen taxi in both origin and destination
            path_finding_permutation = collections.defaultdict(list)
            for i in path_finding:
                for j in itertools.permutations(path_finding[i]):
                    path_finding_permutation[i].append(j)
            # Writing in log.txt file
            file.write('{0:41} ::= {1}\n'.format('path_finding_permutation', path_finding_permutation))

            # Calculating traveled distance for each permutation in ============================================= origin
            # path_finding_permutation_dist = {1:[]}
            path_finding_permutation_dist = collections.defaultdict(list)
            for j in range(len(path_finding_permutation[1])):
                sum_dist = 0
                for k in range(len(path_finding_permutation[1][j]) - 1):
                    sum_dist += distance(passengers_O[path_finding_permutation[1][j][k]],
                                         passengers_O[path_finding_permutation[1][j][k + 1]])
                path_finding_permutation_dist[1].append(sum_dist +
                                                        distance(Taxis[minimum],
                                                                 passengers_O[path_finding_permutation[1][j][0]]))

            # ----------------------------------------------------------------------------------------------------------
            # ----------------------------------------------------------------------------------------------------------
            # Calculating traveled distance for each permutation in destination based on origin permutations
            # that are in path_finding_permutation[1] list, i.e. we try all origin sequence to get minimum distance
            # path_finding_permutation_dist = {1:[], 2:[[first_origin_min], [second_origin_min], [third_origin_min],..]}
            for i in range(len(path_finding_permutation[1])):
                list_temporary = []
                # Calculating traveled distance for each permutation in ==================================== destination
                for j in range(len(path_finding_permutation[2])):
                    sum_dist = 0
                    for k in range(len(path_finding_permutation[2][j]) - 1):
                        sum_dist += distance(passengers_D[path_finding_permutation[2][j][k]],
                                             passengers_D[path_finding_permutation[2][j][k + 1]])
                    list_temporary.append(sum_dist + distance(passengers_O[path_finding_permutation[1][i][3]],
                                                              passengers_D[path_finding_permutation[2][j][0]]))
                path_finding_permutation_dist[2].append(list_temporary)
            # Writing in log.txt file
            file.write('{0:41} ::= {1}\n'.format('path_finding_permutation_dist', path_finding_permutation_dist))

            # I don't care how many minimum are in each list of key(2):[  ] of path_finding_permutation_dist?
            # We have minimum in destination per origin's, min_2 = [number of permutation in origin]
            min_2 = [min(path_finding_permutation_dist[2][i]) for i in range(len(path_finding_permutation_dist[2]))]

            # By index_min_1 we can find which sequence of origin is the best for get the minimum traveled distance
            index_min_1 = min_2.index(min(min_2))
            path_min_1 = path_finding_permutation[1][index_min_1]
            min_1 = path_finding_permutation_dist[1][index_min_1]

            # Getting index of permutation that its traveled distance in (destination + origin) become the lowest and
            # Return rider's destination sequence in path_min_2 as a list
            index_min_2 = path_finding_permutation_dist[2][index_min_1].\
                index(min(path_finding_permutation_dist[2][index_min_1]))
            path_min_2 = path_finding_permutation[2][index_min_2]

            # ----------------------------------------------------------------------------------------------------------
            #                                       Put results in df (Data Frame)
            # ----------------------------------------------------------------------------------------------------------
            to_first_rider = distance(Taxis[minimum], fix2[path_min_1[0]])
            origin = min_1 - distance(Taxis[minimum], fix2[path_min_1[0]])
            transfer = distance(fix2[path_min_1[3]], fix3[path_min_2[0]])
            destination = min(min_2) - transfer

            p1_share, p2_share, p3_share, p4_share = finding_distance_sharing(path_min_1, path_min_2)

            p1_individual = distance(passengers_O[path_min_1[0]], passengers_D[re.sub(r'o', 'd', path_min_1[0])])
            p2_individual = distance(passengers_O[path_min_1[1]], passengers_D[re.sub(r'o', 'd', path_min_1[1])])
            p3_individual = distance(passengers_O[path_min_1[2]], passengers_D[re.sub(r'o', 'd', path_min_1[2])])
            p4_individual = distance(passengers_O[path_min_1[3]], passengers_D[re.sub(r'o', 'd', path_min_1[3])])

            # Share mode over individual mode for all chosen passengers
            lst1 = np.array([p1_share, p2_share, p3_share, p4_share], dtype='float')
            lst2 = np.array([p1_individual, p2_individual, p3_individual, p4_individual], dtype='float')
            divide = lst1 / lst2
            divide[divide > 2] = np.NaN
            so1, so2, so3, so4 = divide

            # number_of_non_NaN_value = np.count_nonzero(~np.isnan(divide))
            number_of_NaN_value = np.count_nonzero(np.isnan(divide))

            # nan passenger
            index_of_Nan = [i[0] for i in np.argwhere(np.isnan(divide)).tolist()]
            [nan_passenger.append(path_min_1[i]) for i in index_of_Nan]
            index_of_non_Nan = [i[0] for i in np.argwhere(~np.isnan(divide)).tolist()]

            if number_of_NaN_value == 3 or number_of_NaN_value == 4:
                # Writing in log.txt file
                file.write((('\n-\n We had {} NaN values\n'.format(number_of_NaN_value)).
                            replace(' ', ' ' * 40, 1)).replace('-', '-' * 100, 2))
                No_four -= 1
                if number_of_NaN_value == 3:
                    No_one += 1
                else:
                    No_zero += 1
                pass
            elif number_of_NaN_value == 2 or number_of_NaN_value == 1:
                # Writing in log.txt file
                file.write((('\n-\n We had {} NaN values\n'.format(number_of_NaN_value)).
                            replace(' ', ' ' * 40, 1)).replace('-', '-' * 100, 2))
                No_four -= 1
                if number_of_NaN_value == 2:
                    No_two += 1
                else:
                    No_three += 1
                chosen_passenger = [path_min_1[i] for i in index_of_non_Nan]
                # ------------------------------------------------------------------------------------------------------
                #                                       2_Shortest path (Start)
                # ------------------------------------------------------------------------------------------------------
                # path_finding dictionary has two keys {1:[origin sequence], 2:[destination sequence]}
                path_finding = collections.defaultdict(list)
                # Find chosen combination from Defaultdict_comb dictionary
                for each_key in chosen_passenger:
                    path_finding[1].append(each_key)
                    path_finding[2].append(re.sub(r'o', 'd', each_key))
                # Writing in log.txt file
                file.write('{0:41} ::= {1}\n'.format('path_finding', path_finding))

                # Find permutation of riders for chosen taxi in both origin and destination
                path_finding_permutation = collections.defaultdict(list)
                for i in path_finding:
                    for j in itertools.permutations(path_finding[i]):
                        path_finding_permutation[i].append(j)
                # Writing in log.txt file
                file.write('{0:41} ::= {1}\n'.format('path_finding_permutation', path_finding_permutation))

                # Calculating traveled distance for each permutation in ========================================= origin
                # path_finding_permutation_dist = {1:[]}
                path_finding_permutation_dist = collections.defaultdict(list)
                for j in range(len(path_finding_permutation[1])):
                    sum_dist = 0
                    for k in range(len(path_finding_permutation[1][j]) - 1):
                        sum_dist += distance(passengers_O[path_finding_permutation[1][j][k]],
                                             passengers_O[path_finding_permutation[1][j][k + 1]])
                    path_finding_permutation_dist[1].append(sum_dist +
                                                            distance(Taxis[minimum],
                                                                     passengers_O[path_finding_permutation[1][j][0]]))
                # ------------------------------------------------------------------------------------------------------
                # ------------------------------------------------------------------------------------------------------
                # Calculating traveled distance for each permutation in destination based on origin permutations
                # that are in path_finding_permutation[1] list, i.e. we try all origin sequence to get minimum distance
                # path_finding_permutation_dist = {1:[],
                #                                  2:[[first_origin_min], [second_origin_min], [third_origin_min],..]}
                for i in range(len(path_finding_permutation[1])):
                    list_temporary = []
                    # Calculating traveled distance for each permutation in ================================ destination
                    for j in range(len(path_finding_permutation[2])):
                        sum_dist = 0
                        for k in range(len(path_finding_permutation[2][j]) - 1):
                            sum_dist += distance(passengers_D[path_finding_permutation[2][j][k]],
                                                 passengers_D[path_finding_permutation[2][j][k + 1]])
                        if number_of_NaN_value == 2:
                            list_temporary.append(sum_dist + distance(passengers_O[path_finding_permutation[1][i][1]],
                                                                      passengers_D[path_finding_permutation[2][j][0]]))
                        elif number_of_NaN_value == 1:
                            list_temporary.append(sum_dist + distance(passengers_O[path_finding_permutation[1][i][2]],
                                                                      passengers_D[path_finding_permutation[2][j][0]]))
                    path_finding_permutation_dist[2].append(list_temporary)
                # Writing in log.txt file
                file.write('{0:41} ::= {1}\n'.format('path_finding_permutation_dist', path_finding_permutation_dist))

                # I don't care how many minimum are in each list of key(2):[  ] of path_finding_permutation_dist?
                # We have minimum in destination per origin's, min_2 = [number of permutation in origin]
                min_2 = [min(path_finding_permutation_dist[2][i]) for i in range(len(path_finding_permutation_dist[2]))]

                # By index_min_1 we can find which sequence of origin is the best for get the minimum traveled distance
                index_min_1 = min_2.index(min(min_2))
                path_min_1 = path_finding_permutation[1][index_min_1]
                min_1 = path_finding_permutation_dist[1][index_min_1]

                # Getting index of permutation that its traveled distance in (destination + origin) become the lowest
                # and Return rider's destination sequence in path_min_2 as a list
                index_min_2 = path_finding_permutation_dist[2][index_min_1].\
                    index(min(path_finding_permutation_dist[2][index_min_1]))
                path_min_2 = path_finding_permutation[2][index_min_2]

                # ------------------------------------------------------------------------------------------------------
                #                                       Put results in df (Data Frame)
                # ------------------------------------------------------------------------------------------------------
                to_first_rider = distance(Taxis[minimum], fix2[path_min_1[0]])
                origin = min_1 - distance(Taxis[minimum], fix2[path_min_1[0]])
                if number_of_NaN_value == 2:
                    transfer = distance(fix2[path_min_1[1]], fix3[path_min_2[0]])

                    p1_share, p2_share = finding_distance_sharing(path_min_1, path_min_2)
                    p3_share = np.NaN
                    p4_share = np.NaN

                    p1_individual = distance(passengers_O[path_min_1[0]],
                                             passengers_D[re.sub(r'o', 'd', path_min_1[0])])
                    p2_individual = distance(passengers_O[path_min_1[1]],
                                             passengers_D[re.sub(r'o', 'd', path_min_1[1])])
                    p3_individual = np.NaN
                    p4_individual = np.NaN
                elif number_of_NaN_value == 1:
                    transfer = distance(fix2[path_min_1[2]], fix3[path_min_2[0]])

                    p1_share, p2_share, p3_share = finding_distance_sharing(path_min_1, path_min_2)
                    p4_share = np.NaN

                    p1_individual = distance(passengers_O[path_min_1[0]],
                                             passengers_D[re.sub(r'o', 'd', path_min_1[0])])
                    p2_individual = distance(passengers_O[path_min_1[1]],
                                             passengers_D[re.sub(r'o', 'd', path_min_1[1])])
                    p3_individual = distance(passengers_O[path_min_1[2]],
                                             passengers_D[re.sub(r'o', 'd', path_min_1[2])])
                    p4_individual = np.NaN
                destination = min(min_2) - transfer

                # Share mode over individual mode for all chosen passengers
                lst1 = np.array([p1_share, p2_share, p3_share, p4_share], dtype='float')
                lst2 = np.array([p1_individual, p2_individual, p3_individual, p4_individual], dtype='float')
                divide = lst1 / lst2
                so1, so2, so3, so4 = divide

                # Compute distance in sharing mode(each taxi travel with riders)
                Traveled_Distance[minimum] = (min_1 + min(min_2))

            else:
                # Writing in log.txt file
                file.write((('\n-\n We had {} NaN values\n'.format(number_of_NaN_value)).
                            replace(' ', ' ' * 40, 1)).replace('-', '-' * 100, 2))
                # Compute distance in sharing mode(each taxi travel with riders)
                Traveled_Distance[minimum] = (min_1 + min(min_2))

            df.loc['{}'.format(each_taxi+1)] = [minimum,
                                                path_min_1, path_min_2,
                                                to_first_rider, origin, transfer, destination,
                                                p1_share, p2_share, p3_share, p4_share,
                                                p1_individual, p2_individual, p3_individual, p4_individual,
                                                round(so1, 2), round(so2, 2), round(so3, 2), round(so4, 2)]
            # if number_of_NaN_value in {0, 1, 2}:
            #     path_min_1_loc = [passengers_O[i] for i in path_min_1]
            #     path_min_2_loc = [passengers_D[i] for i in path_min_2]
            #     df_clustering.loc['{}'.format(each_taxi+1)] = [minimum,
            #                                                    path_min_1,
            #                                                    path_min_1_loc,
            #                                                    (np.array(path_min_1_loc).mean(0).round(1)).tolist(),
            #                                                    path_min_2_loc,
            #                                                    (np.array(path_min_2_loc).mean(0).round(1)).tolist()]

            # Removing selected taxi and passengers
            del_dict_item(minimum, Defaultdict_comb, Defaultdict_comb_loc_com_cons_min_index)


            # Writing in log.txt file
            file.write('{0:41} ::= {1}\n'.format('index_min_1', index_min_1))
            file.write('{0:41} ::= {1}\n'.format('path_min_1', path_min_1))
            file.write('{0:41} ::= {1}\n'.format('min_1', min_1))
            file.write('{0:41} ::= {1}\n'.format('index_min_2', index_min_2))
            file.write('{0:41} ::= {1}\n'.format('path_min_2', path_min_2))
            file.write('{0:41} ::= {1}\n'.format('min_2', min_2))

        # We want to know do we have any taxi with 3 riders, by boolean operator (check_3)
        elif four > three and not check_3:
            # Writing in log.txt file
            file.write('Taxi {0} is chosen with 3 passenger.\n'.format(minimum_3))
            No_three += 1
            # ----------------------------------------------------------------------------------------------------------
            #                                      Shortest path_3 (Start)
            # ----------------------------------------------------------------------------------------------------------
            # path_finding dictionary has two keys {1:[origin sequence], 2:[destination sequence]}
            path_finding = collections.defaultdict(list)
            # Find chosen combination from Defaultdict_comb_3 dictionary
            chosen_passenger = Defaultdict_comb_3[minimum_3][Defaultdict_comb_loc_com_cons_min_index_3[minimum_3][0]]
            for each_key in chosen_passenger:
                path_finding[1].append(each_key)
                path_finding[2].append(re.sub(r'o', 'd', each_key))
            # Writing in log.txt file
            file.write('{0:41} ::= {1}\n'.format('path_finding', path_finding))

            # Find permutation of riders for chosen taxi in both origin and destination
            path_finding_permutation = collections.defaultdict(list)
            for i in path_finding:
                for j in itertools.permutations(path_finding[i]):
                    path_finding_permutation[i].append(j)
            # Writing in log.txt file
            file.write('{0:41} ::= {1}\n'.format('path_finding_permutation', path_finding_permutation))

            # Calculating traveled distance for each permutation in ============================================= origin
            # path_finding_permutation_dist = {1:[]}
            path_finding_permutation_dist = collections.defaultdict(list)
            for j in range(len(path_finding_permutation[1])):
                sum_dist = 0
                for k in range(len(path_finding_permutation[1][j]) - 1):
                    sum_dist += distance(passengers_O[path_finding_permutation[1][j][k]],
                                         passengers_O[path_finding_permutation[1][j][k + 1]])
                path_finding_permutation_dist[1].append(sum_dist +
                                                        distance(Taxis[minimum_3],
                                                                 passengers_O[path_finding_permutation[1][j][0]]))

            # ----------------------------------------------------------------------------------------------------------
            # ----------------------------------------------------------------------------------------------------------
            # Calculating traveled distance for each permutation in destination based on origin permutations
            # that are in path_finding_permutation[1] list, i.e. we try all origin sequence to get minimum distance
            # path_finding_permutation_dist = {1:[], 2:[[first_origin_min], [second_origin_min], [third_origin_min],..]}
            for i in range(len(path_finding_permutation[1])):
                list_temporary = []
                # Calculating traveled distance for each permutation in ==================================== destination
                for j in range(len(path_finding_permutation[2])):
                    sum_dist = 0
                    for k in range(len(path_finding_permutation[2][j]) - 1):
                        sum_dist += distance(passengers_D[path_finding_permutation[2][j][k]],
                                             passengers_D[path_finding_permutation[2][j][k + 1]])
                    list_temporary.append(sum_dist + distance(passengers_O[path_finding_permutation[1][i][2]],
                                                              passengers_D[path_finding_permutation[2][j][0]]))
                path_finding_permutation_dist[2].append(list_temporary)
            # Writing in log.txt file
            file.write('{0:41} ::= {1}\n'.format('path_finding_permutation_dist', path_finding_permutation_dist))

            # I don't care how many minimum are in each list of key(2):[  ] of path_finding_permutation_dist?
            # We have minimum in destination per origin's, min_2 = [number of permutation in origin]
            min_2 = [min(path_finding_permutation_dist[2][i]) for i in range(len(path_finding_permutation_dist[2]))]

            # By index_min_1 we can find which sequence of origin is the best for get the minimum traveled distance
            index_min_1 = min_2.index(min(min_2))
            path_min_1 = path_finding_permutation[1][index_min_1]
            min_1 = path_finding_permutation_dist[1][index_min_1]

            # Getting index of permutation that its traveled distance in (destination + origin) become the lowest and
            # Return rider's destination sequence in path_min_2 as a list
            index_min_2 = path_finding_permutation_dist[2][index_min_1].\
                index(min(path_finding_permutation_dist[2][index_min_1]))
            path_min_2 = path_finding_permutation[2][index_min_2]

            # ----------------------------------------------------------------------------------------------------------
            #                                       Put results in df (Data Frame)
            # ----------------------------------------------------------------------------------------------------------
            to_first_rider = distance(Taxis[minimum_3], fix2[path_min_1[0]])
            origin = min_1 - distance(Taxis[minimum_3], fix2[path_min_1[0]])
            transfer = distance(fix2[path_min_1[2]], fix3[path_min_2[0]])
            destination = min(min_2) - transfer

            p1_share, p2_share, p3_share = finding_distance_sharing(path_min_1, path_min_2)
            p4_share = np.NAN

            p1_individual = distance(passengers_O[path_min_1[0]], passengers_D[re.sub(r'o', 'd', path_min_1[0])])
            p2_individual = distance(passengers_O[path_min_1[1]], passengers_D[re.sub(r'o', 'd', path_min_1[1])])
            p3_individual = distance(passengers_O[path_min_1[2]], passengers_D[re.sub(r'o', 'd', path_min_1[2])])
            p4_individual = np.NAN

            # Share mode over individual mode for all chosen passengers
            lst1 = np.array([p1_share, p2_share, p3_share], dtype='float')
            lst2 = np.array([p1_individual, p2_individual, p3_individual], dtype='float')
            divide = lst1 / lst2
            divide[divide > 2] = np.NaN
            so1, so2, so3 = divide
            so4 = np.NaN

            # number_of_non_NaN_value = np.count_nonzero(~np.isnan(divide))
            number_of_NaN_value = np.count_nonzero(np.isnan(divide))

            # nan passenger
            index_of_Nan = [i[0] for i in np.argwhere(np.isnan(divide)).tolist()]
            [nan_passenger.append(path_min_1[i]) for i in index_of_Nan]
            index_of_non_Nan = [i[0] for i in np.argwhere(~np.isnan(divide)).tolist()]

            if number_of_NaN_value == 2 or number_of_NaN_value == 3:
                # Writing in log.txt file
                file.write((('\n-\n We had {} NaN values\n'.format(number_of_NaN_value)).
                            replace(' ', ' ' * 40, 1)).replace('-', '-' * 100, 2))
                No_three -= 1
                if number_of_NaN_value == 2:
                    No_one += 1
                else:
                    No_zero += 1
                pass
            elif number_of_NaN_value == 1:
                # Writing in log.txt file
                file.write((('\n-\n We had {} NaN values\n'.format(number_of_NaN_value)).
                            replace(' ', ' ' * 40, 1)).replace('-', '-' * 100, 2))
                No_three -= 1
                No_two += 1
                chosen_passenger = [path_min_1[i] for i in index_of_non_Nan]
                # ------------------------------------------------------------------------------------------------------
                #                                       2_Shortest path (Start)
                # ------------------------------------------------------------------------------------------------------
                # path_finding dictionary has two keys {1:[origin sequence], 2:[destination sequence]}
                path_finding = collections.defaultdict(list)
                # Find chosen combination from Defaultdict_comb dictionary
                for each_key in chosen_passenger:
                    path_finding[1].append(each_key)
                    path_finding[2].append(re.sub(r'o', 'd', each_key))
                # Writing in log.txt file
                file.write('{0:41} ::= {1}\n'.format('path_finding', path_finding))

                # Find permutation of riders for chosen taxi in both origin and destination
                path_finding_permutation = collections.defaultdict(list)
                for i in path_finding:
                    for j in itertools.permutations(path_finding[i]):
                        path_finding_permutation[i].append(j)
                # Writing in log.txt file
                file.write('{0:41} ::= {1}\n'.format('path_finding_permutation', path_finding_permutation))

                # Calculating traveled distance for each permutation in ========================================= origin
                # path_finding_permutation_dist = {1:[]}
                path_finding_permutation_dist = collections.defaultdict(list)
                for j in range(len(path_finding_permutation[1])):
                    sum_dist = 0
                    for k in range(len(path_finding_permutation[1][j]) - 1):
                        sum_dist += distance(passengers_O[path_finding_permutation[1][j][k]],
                                             passengers_O[path_finding_permutation[1][j][k + 1]])
                    path_finding_permutation_dist[1].append(sum_dist +
                                                            distance(Taxis[minimum_3],
                                                                     passengers_O[path_finding_permutation[1][j][0]]))

                # ------------------------------------------------------------------------------------------------------
                # ------------------------------------------------------------------------------------------------------
                # Calculating traveled distance for each permutation in destination based on origin permutations
                # that are in path_finding_permutation[1] list, i.e. we try all origin sequence to get minimum distance
                # path_finding_permutation_dist = {1:[],
                #                                  2:[[first_origin_min], [second_origin_min], [third_origin_min],..]}
                for i in range(len(path_finding_permutation[1])):
                    list_temporary = []
                    # Calculating traveled distance for each permutation in ================================ destination
                    for j in range(len(path_finding_permutation[2])):
                        sum_dist = 0
                        for k in range(len(path_finding_permutation[2][j]) - 1):
                            sum_dist += distance(passengers_D[path_finding_permutation[2][j][k]],
                                                 passengers_D[path_finding_permutation[2][j][k + 1]])
                        list_temporary.append(sum_dist + distance(passengers_O[path_finding_permutation[1][i][1]],
                                                                  passengers_D[path_finding_permutation[2][j][0]]))
                    path_finding_permutation_dist[2].append(list_temporary)
                # Writing in log.txt file
                file.write('{0:41} ::= {1}\n'.format('path_finding_permutation_dist', path_finding_permutation_dist))

                # I don't care how many minimum are in each list of key(2):[  ] of path_finding_permutation_dist?
                # We have minimum in destination per origin's, min_2 = [number of permutation in origin]
                min_2 = [min(path_finding_permutation_dist[2][i]) for i in range(len(path_finding_permutation_dist[2]))]

                # By index_min_1 we can find which sequence of origin is the best for get the minimum traveled distance
                index_min_1 = min_2.index(min(min_2))
                path_min_1 = path_finding_permutation[1][index_min_1]
                min_1 = path_finding_permutation_dist[1][index_min_1]

                # Getting index of permutation that its traveled distance in (destination + origin) become the lowest
                # and Return rider's destination sequence in path_min_2 as a list
                index_min_2 = path_finding_permutation_dist[2][index_min_1].\
                    index(min(path_finding_permutation_dist[2][index_min_1]))
                path_min_2 = path_finding_permutation[2][index_min_2]

                # ------------------------------------------------------------------------------------------------------
                #                                       Put results in df (Data Frame)
                # ------------------------------------------------------------------------------------------------------
                to_first_rider = distance(Taxis[minimum_3], fix2[path_min_1[0]])
                origin = min_1 - distance(Taxis[minimum_3], fix2[path_min_1[0]])
                transfer = distance(fix2[path_min_1[1]], fix3[path_min_2[0]])
                destination = min(min_2) - transfer

                p1_share, p2_share = finding_distance_sharing(path_min_1, path_min_2)
                p3_share, p4_share = np.NAN, np.NaN

                p1_individual = distance(passengers_O[path_min_1[0]], passengers_D[re.sub(r'o', 'd', path_min_1[0])])
                p2_individual = distance(passengers_O[path_min_1[1]], passengers_D[re.sub(r'o', 'd', path_min_1[1])])
                p3_individual = np.NaN
                p4_individual = np.NAN

                # Share mode over individual mode for all chosen passengers
                lst1 = np.array([p1_share, p2_share, p3_share, p4_share], dtype='float')
                lst2 = np.array([p1_individual, p2_individual, p3_individual, p4_individual], dtype='float')
                divide = lst1 / lst2
                so1, so2, so3, so4 = divide

                # Compute distance in sharing mode(each taxi travel with riders)
                Traveled_Distance[minimum_3] = (min_1 + min(min_2))

            else:
                # Writing in log.txt file
                file.write((('\n-\n We had {} NaN values\n'.format(number_of_NaN_value)).
                            replace(' ', ' ' * 40, 1)).replace('-', '-' * 100, 2))
                # Compute distance in sharing mode(each taxi travel with riders)
                Traveled_Distance[minimum_3] = (min_1 + min(min_2))

            df.loc['{}'.format(each_taxi + 1)] = [minimum_3,
                                                  path_min_1, path_min_2,
                                                  to_first_rider, origin, transfer, destination,
                                                  p1_share, p2_share, p3_share, p4_share,
                                                  p1_individual, p2_individual, p3_individual, p4_individual,
                                                  round(so1, 2), round(so2, 2), round(so3, 2), round(so4, 2)]

            # if number_of_NaN_value in {0, 1}:
            #     path_min_1_loc = [passengers_O[i] for i in path_min_1]
            #     path_min_2_loc = [passengers_D[i] for i in path_min_2]
            #     df_clustering.loc['{}'.format(each_taxi+1)] = [minimum_3,
            #                                                    path_min_1,
            #                                                    path_min_1_loc,
            #                                                    (np.array(path_min_1_loc).mean(0).round(1)).tolist(),
            #                                                    path_min_2_loc,
            #                                                    (np.array(path_min_2_loc).mean(0).round(1)).tolist()]

            # Removing selected taxi and passengers
            del_dict_item(minimum_3, Defaultdict_comb_3, Defaultdict_comb_loc_com_cons_min_index_3)

            # Writing in log.txt file
            file.write('{0:41} ::= {1}\n'.format('index_min_1', index_min_1))
            file.write('{0:41} ::= {1}\n'.format('path_min_1', path_min_1))
            file.write('{0:41} ::= {1}\n'.format('min_1', min_1))
            file.write('{0:41} ::= {1}\n'.format('index_min_2', index_min_2))
            file.write('{0:41} ::= {1}\n'.format('path_min_2', path_min_2))
            file.write('{0:41} ::= {1}\n'.format('min_2', min_2))

    # Sum up traveled distance of missing passengers by sharing mode, so we have Traveled_distance
    missing_passenger = 0
    for i in passengers_O:
        missing_passenger += distance(passengers_O[i], passengers_D[re.sub(r'o', 'd', i)])

    # Sum up traveled distance of passengers who exceed (share to individual) ratio
    nan_pass = 0
    for i in nan_passenger:
        nan_pass += distance(fix2[i], fix3[re.sub(r'o', 'd', i)])

    # Writing in log.txt file
    file.write('{0:41} ::= {1}\n\n'.format('nan_passenger {}'.format(SIF), nan_passenger))
    file.write('{0:41} ::= {1}\n\n'.format('Traveled_Distance {}'.format(SIF), Traveled_Distance))
    file.write('{0:41} ::= {1}\n'.format('1-traveled_distance_individual{}'.format(SIF), sum(traveled_distance.values())))
    file.write('{0:41} ::= {1}\n'.format('2-Traveled_Distance_sharing {}'.format(SIF), sum(Traveled_Distance.values())))
    file.write('{0:41} ::= {1}\n'.format('3-missing_passenger {}'.format(SIF), missing_passenger))
    file.write('{0:41} ::= {1}\n'.format('4-nan_passenger {}'.format(SIF), nan_pass))
    file.write('{0:41} ::= {1}\n'.format('5-Traveled_distance {} = (2+3+4)'.format(SIF),
                                         sum(Traveled_Distance.values())+missing_passenger+nan_pass))

    No_riders_list.append(No_two*2+No_three*3+No_four*4)
    No_zero_list.append(No_zero)
    No_one_list.append(No_one)
    No_two_list.append(No_two)
    No_three_list.append(No_three)
    No_four_list.append(No_four)
    y_Traveled_Distance.append(sum(Traveled_Distance.values()))
    y_Traveled_distance.append(sum(Traveled_Distance.values()) + missing_passenger)
    y_traveled_distance.append(sum(traveled_distance.values()))

    # Save DataFrame as a sheet of excel
    df.to_excel(excel_writer, sheet_name='{}'.format(SIF))
    df_active_cars.loc['{}'.format(SIF)] = [No_zero,
                                            No_one,
                                            No_two,
                                            No_three,
                                            No_four,
                                            No_two+No_three+No_four,
                                            No_two*2+No_three*3+No_four*4,
                                            len(nan_passenger),
                                            len(passengers_O),
                                            No_two*2+No_three*3+No_four*4+len(nan_passenger)+len(passengers_O)]

    # # ========================================================================================================
    # # ========================================================================================================Clustering
    # # ========================================================================================================
    # df_clustering.to_excel(excel_writer_clustering, sheet_name='{}'.format(SIF))

    rss.append(psutil.Process(os.getpid()).memory_info()[0])

    api_list.append(api)
    end = time.time()
    elapsed_time.append(round((end-start)/60, 2))

# Save DataFrame as a sheet of excel
df_active_cars.to_excel(excel_writer, sheet_name='active_cars')
excel_writer.save()
excel_writer.close()
# excel_writer_clustering.save()
# excel_writer_clustering.close()

wb = openpyxl.load_workbook('/home/samim/PycharmProjects/SharedTaxi/output.xlsx')
for ws in ['{}'.format(round(i, 1)) for i in np.linspace(1, 2.5, 16)]:
    wb[ws].merge_cells('A1:A2')
    wb[ws].merge_cells('B1:B2')
    wb[ws].merge_cells('C1:C2')
    wb[ws].merge_cells('D1:D2')
    wb[ws].merge_cells('E1:E2')
    wb[ws].merge_cells('F1:F2')
    wb[ws].merge_cells('G1:G2')
    wb[ws].merge_cells('H1:H2')
    wb[ws].merge_cells('I1:L1')
    wb[ws].merge_cells('M1:P1')
    wb[ws].merge_cells('Q1:T1')
    bullshit = 0
    for row in ['{0}:{0}'.format(i) for i in range(1, 160)]:
        shit = 0
        for cell in wb[ws][row]:
            if bullshit in {0, 1}:
                cell.font = openpyxl.styles.Font(bold=False, color='FF800080')
            if shit in {2, 3}:
                pass
            else:
                cell.alignment = openpyxl.styles.alignment.Alignment(horizontal='center', vertical='top')
            if shit in {0, 4, 5, 6, 8, 9, 10, 12, 13, 14, 16, 17, 18}:
                pass
            else:
                cell.border = openpyxl.styles.borders.Border(right=openpyxl.styles.borders.Side(style='double'))
            shit += 1
        bullshit += 1
wb.save('/home/samim/PycharmProjects/SharedTaxi/output.xlsx')
wb.close()

End = time.time()
print('No_Taxi: {0}, No_passengers: {1}, solved in: {2} min'.format(No_Taxi, No_passengers, round((End-Start)/60, 2)))
ax.set_title('No_Taxi: {0}, No_passengers: {1}, solved in: {2} min'.
             format(No_Taxi, No_passengers, round((End-Start)/60, 2)))

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++Number of active car-plotly
x = np.linspace(1, 2.5, 16)
# plot SIF versus No_zero
trace0 = plotly.graph_objs.Scatter(
    x=x,
    y=np.array(No_zero_list),
    mode='lines+markers',
    name='SIF versus No_zero'
)
# plot SIF versus No_one
trace1 = plotly.graph_objs.Scatter(
    x=x,
    y=np.array(No_one_list),
    mode='lines+markers',
    name='SIF versus No_one'
)
# plot SIF versus No_two
trace2 = plotly.graph_objs.Scatter(
    x=x,
    y=np.array(No_two_list),
    mode='lines+markers',
    name='SIF versus No_two'
)
# plot SIF versus No_three
trace3 = plotly.graph_objs.Scatter(
    x=x,
    y=np.array(No_three_list),
    mode='lines+markers',
    name='SIF versus No_three'
)
# plot SIF versus No_four
trace4 = plotly.graph_objs.Scatter(
    x=x,
    y=np.array(No_four_list),
    mode='lines+markers',
    name='SIF versus No_four'
)
# plot SIF versus (No_two+No_three+No_four)
trace5 = plotly.graph_objs.Scatter(
    x=x,
    y=np.array(No_two_list) + np.array(No_three_list) + np.array(No_four_list),
    mode='lines+markers',
    name='SIF versus No_two+No_three+No_four'
)
data = [trace0, trace1, trace2, trace3, trace4, trace5]
layout = plotly.graph_objs.Layout(
    title='<b>SIF versus taxis with 0, 1, 2, 3, 4 rider</b>',
    titlefont=dict(family='Comic Sans MS', size=18, color='#3c3c3c'),
    hovermode='closest',
    legend=dict(x=1, y=.5, traceorder='normal', font=dict(family='Courier', size=15, color='#000'),
                bgcolor='#FFFFFF', bordercolor='#E2E2E2', borderwidth=2),
    xaxis=dict(title='SIF', zeroline=True, gridwidth=2),
    yaxis=dict(title='Numbers of active Taxi', zeroline=True, gridwidth=2),
    showlegend=True
)
fig1 = plotly.graph_objs.Figure(data=data, layout=layout)
plotly.offline.plot(fig1, filename='active_taxi.html', auto_open=False)


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++No_Riders-plotly
# plot SIF versus No_riders
trace0 = plotly.graph_objs.Scatter(
    x=x,
    y=np.array(No_riders_list),
    mode='lines+markers',
    name='SIF versus No_riders'
)
data = [trace0]
layout = plotly.graph_objs.Layout(
    title='<b>SIF versus No_riders</b>',
    titlefont=dict(family='Comic Sans MS', size=18, color='#3c3c3c'),
    hovermode='closest',
    legend=dict(x=1, y=.5, traceorder='normal', font=dict(family='Courier', size=15, color='#000'),
                bgcolor='#FFFFFF', bordercolor='#E2E2E2', borderwidth=2),
    xaxis=dict(title='SIF', zeroline=True, gridwidth=2),
    yaxis=dict(title='Numbers of passengers who used SharedTaxi', zeroline=True, gridwidth=2),
    showlegend=True
)
fig1 = plotly.graph_objs.Figure(data=data, layout=layout)
plotly.offline.plot(fig1, filename='shared_riders.html', auto_open=False)


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++traveled distance-plotly
# plot SIF versus Traveled_Distance
trace0 = plotly.graph_objs.Scatter(
    x=x,
    y=np.array(y_Traveled_Distance),
    mode='lines+markers',
    name='SIF versus Sharing Mode'
)
# plot SIF versus (Traveled_Distance+traveled_distance)
trace1 = plotly.graph_objs.Scatter(
    x=x,
    y=np.array(y_Traveled_distance),
    mode='lines+markers',
    name='SIF versus Sharing Mode+Individual Mode'
)
# plot SIF versus y_traveled_distance
trace2 = plotly.graph_objs.Scatter(
    x=x,
    y=np.array(y_traveled_distance),
    mode='lines+markers',
    name='SIF versus Individual Mode'
)
data = [trace0, trace1, trace2, trace3]
layout = plotly.graph_objs.Layout(
    title='<b>SIF versus traveled distance</b>',
    titlefont=dict(family='Comic Sans MS', size=18, color='#3c3c3c'),
    hovermode='closest',
    legend=dict(x=1, y=.5, traceorder='normal', font=dict(family='Courier', size=15, color='#000'),
                bgcolor='#FFFFFF', bordercolor='#E2E2E2', borderwidth=2),
    xaxis=dict(title='SIF', zeroline=True, gridwidth=2),
    yaxis=dict(title='Total traveled distance', zeroline=True, gridwidth=2),
    showlegend=True
)
fig2 = plotly.graph_objs.Figure(data=data, layout=layout)
plotly.offline.plot(fig2, filename='traveled_distance.html', auto_open=False)


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++passengers-plotly
# plot passengers in origin
xo, yo = zip(*list(fix2.values()))
zo = []
for i in generator(0, len(list(fix2.values()))):
    Sum = sum([1 if j == list(fix2.values())[i] else 0 for j in list(fix2.values())[:i]])
    zo.append(Sum)
trace0 = plotly.graph_objs.Scatter3d(
    x=xo,
    y=yo,
    z=zo,
    text=list(fix2.keys()),
    textfont=dict(size=8),
    mode='markers+text',
    marker=dict(color='#00bfff', size=3, symbol='circle', line=dict(color='#0000ff', width=1), opacity=0.9),
    textposition='top center',
    name='Passengers in Origin'
)

# plot passengers in destination
xd, yd = map(list, zip(*list(fix3.values())))
zd = []
for i in generator(0, len(list(fix3.values()))):
    Sum = sum([1 if j == list(fix3.values())[i] else 0 for j in list(fix3.values())[:i]])
    zd.append(Sum)
trace1 = plotly.graph_objs.Scatter3d(
    x=xd,
    y=yd,
    z=zd,
    text=list(fix3.keys()),
    textfont=dict(size=8),
    mode='markers+text',
    marker=dict(color='#faaa0a', size=3, symbol='circle', line=dict(color='#9400d3', width=1), opacity=0.8),
    name='Passengers in Destination'
)

# plot taxis
xt, yt = map(list, zip(*list(fix1.values())))
zt = []
for i in generator(0, len(list(fix1.values()))):
    Sum = sum([1 if j == list(fix1.values())[i] else 0 for j in list(fix1.values())[:i]])
    zt.append(Sum)
trace2 = plotly.graph_objs.Scatter3d(
    x=xt,
    y=yt,
    z=zt,
    text=list(fix1.keys()),
    textfont=dict(size=8),
    mode='markers+text',
    marker=dict(color='#800080', size=3, symbol='x', line=dict(color='#fa00fa', width=1), opacity=0.8),
    name='Taxi'
)
data = [trace0, trace1, trace2]
layout = plotly.graph_objs.Layout(
    title='Taxi: {0}, passengers: {1}, solved in: {2} min'.format(No_Taxi, No_passengers, round((End-Start)/60, 2)),
    titlefont=dict(family='Comic Sans MS', size=8, color='rgb(60, 60, 60)'),
    margin=dict(r=0, b=0, l=0, t=0),
    legend=dict(x=1, y=.5, traceorder='normal', font=dict(family='Courier', size=15, color='#000'),
                bgcolor='#FFFFFF', bordercolor='#E2E2E2', borderwidth=2),
    scene=dict(xaxis=dict(tickfont=dict(size=12), backgroundcolor="#c8c8e6", gridcolor="#ffffff", showbackground=True,
                          zerolinecolor="#ffffff"),
               yaxis=dict(tickfont=dict(size=12), backgroundcolor="#e6c8e6", gridcolor="#ffffff", showbackground=True,
                          zerolinecolor="#ffffff"),
               zaxis=dict(tickfont=dict(size=12), backgroundcolor="#e6e6c8", gridcolor="#ffffff", showbackground=True,
                          zerolinecolor="#ffffff"),
               dragmode="turntable",
               annotations=[dict(showarrow=True, z=3, text='<b>Taxi: {0}, passengers: {1}, solved in: {2} min</b>'.
                                 format(No_Taxi, No_passengers, round((End-Start)/60, 2)), textangle=0,
                                 font=dict(family='Comic Sans MS', size=18, color='#3c3c3c'),
                                 arrowcolor="rgba(255, 255, 255, .1)", ax=0, ay=-100)]  # rgba(255,255,255,0.1)=#fafafa
               )
)
fig3 = plotly.graph_objs.Figure(data=data, layout=layout)
plotly.offline.plot(fig3, filename='location.html', auto_open=False)


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++api times-plotly
x = np.linspace(1, 2.5, 16)
# plot SIF versus api
trace0 = plotly.graph_objs.Scatter(
    x=x,
    y=np.array(api_list),
    mode='lines+markers',
    name='SIF versus api'
)
data = [trace0]
layout = plotly.graph_objs.Layout(
    title='<b>SIF versus api</b>',
    titlefont=dict(family='Comic Sans MS', size=18, color='#3c3c3c'),
    hovermode='closest',
    legend=dict(x=1, y=.5, traceorder='normal', font=dict(family='Courier', size=15, color='#000'),
                bgcolor='#FFFFFF', bordercolor='#E2E2E2', borderwidth=2),
    xaxis=dict(title='SIF', zeroline=True, gridwidth=2),
    yaxis=dict(title='Numbers of usage distance function', zeroline=True, gridwidth=2),
    showlegend=True
)
fig1 = plotly.graph_objs.Figure(data=data, layout=layout)
plotly.offline.plot(fig1, filename='api.html', auto_open=False)


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++elapsed time-plotly
x = np.linspace(1, 2.5, 16)
# plot SIF versus Execution time
trace0 = plotly.graph_objs.Scatter(
    x=x,
    y=np.array(elapsed_time),
    mode='lines+markers',
    name='SIF versus Execution time'
)
data = [trace0]
layout = plotly.graph_objs.Layout(
    title='<b>SIF versus Execution time</b>',
    titlefont=dict(family='Comic Sans MS', size=18, color='#3c3c3c'),
    hovermode='closest',
    legend=dict(x=1, y=.5, traceorder='normal', font=dict(family='Courier', size=15, color='#000'),
                bgcolor='#FFFFFF', bordercolor='#E2E2E2', borderwidth=2),
    xaxis=dict(title='SIF', zeroline=True, gridwidth=2),
    yaxis=dict(title='Execution time', zeroline=True, gridwidth=2),
    showlegend=True
)
fig1 = plotly.graph_objs.Figure(data=data, layout=layout)
plotly.offline.plot(fig1, filename='elapsed_time.html', auto_open=False)


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++rss-plotly
x = np.linspace(1, 2.5, 16)
# plot SIF versus rss
trace0 = plotly.graph_objs.Scatter(
    x=x,
    y=np.array(rss),
    mode='lines+markers',
    name='SIF versus rss'
)
data = [trace0]
layout = plotly.graph_objs.Layout(
    title='<b>SIF versus rss</b>',
    titlefont=dict(family='Comic Sans MS', size=18, color='#3c3c3c'),
    hovermode='closest',
    legend=dict(x=1, y=.5, traceorder='normal', font=dict(family='Courier', size=15, color='#000'),
                bgcolor='#FFFFFF', bordercolor='#E2E2E2', borderwidth=2),
    xaxis=dict(title='SIF', zeroline=True, gridwidth=2),
    yaxis=dict(title='rss', zeroline=True, gridwidth=2),
    showlegend=True
)
fig1 = plotly.graph_objs.Figure(data=data, layout=layout)
plotly.offline.plot(fig1, filename='rss.html', auto_open=False)


html_graphs = open("DASHBOARD.html", 'w')
html_graphs.write("<html><head></head><body>"+"\n")
html_graphs.write("<object data='location.html' width='900' height='700'></object>"+"\n")
html_graphs.write("<object data='active_taxi.html' width='900' height='700'></object>"+"\n")
html_graphs.write("<object data='shared_riders.html' width='900' height='700'></object>"+"\n")
html_graphs.write("<object data='traveled_distance.html' width='1100' height='800'></object>"+"\n")
html_graphs.write("<object data='api.html' width='900' height='700'></object>"+"\n")
html_graphs.write("<object data='elapsed_time.html' width='900' height='700'></object>"+"\n")
html_graphs.write("<object data='rss.html' width='900' height='700'></object>"+"\n")
html_graphs.write("</body></html>")
html_graphs.close()


# ==================================================================================================================plot
fig1, axes1 = plt.subplots(nrows=3, ncols=3)
x_new = np.linspace(x.min(), x.max(), 300)

# plot SIF versus No_three
y = np.array(No_three_list)
f = interp1d(x, y, kind='quadratic')
y_smooth = f(x_new)
axes1[0, 0].plot(x_new, y_smooth)
axes1[0, 0].scatter(x, y)
axes1[0, 0].set_title('SIF versus No_three')
axes1[0, 0].set_xlabel('SIF', fontsize=10)
axes1[0, 0].set_ylabel('Numbers of active Taxi', fontsize=10)

# plot SIF versus No_four
y = np.array(No_four_list)
f = interp1d(x, y, kind='quadratic')
y_smooth = f(x_new)
axes1[0, 1].plot(x_new, y_smooth)
axes1[0, 1].scatter(x, y)
axes1[0, 1].set_title('SIF versus No_four')

# plot SIF versus (No_two+No_three+No_four)
temp_list = np.array(No_two_list) + np.array(No_three_list) + np.array(No_four_list)
y = temp_list
f = interp1d(x, y, kind='quadratic')
y_smooth = f(x_new)
axes1[0, 2].plot(x_new, y_smooth)
axes1[0, 2].scatter(x, y)
axes1[0, 2].set_title('SIF versus No_two+No_three+No_four')

# plot SIF versus Traveled_Distance
y = np.array(y_Traveled_Distance)
f = interp1d(x, y, kind='quadratic')
y_smooth = f(x_new)
axes1[1, 0].plot(x_new, y_smooth)
axes1[1, 0].scatter(x, y)
axes1[1, 0].set_title('SIF versus Sharing Mode')
axes1[1, 0].set_xlabel('SIF', fontsize=10)
axes1[1, 0].set_ylabel('Total traveled distance', fontsize=10)

# plot SIF versus (Traveled_Distance+traveled_distance)
y = np.array(y_Traveled_distance)
f = interp1d(x, y, kind='quadratic')
y_smooth = f(x_new)
axes1[1, 1].plot(x_new, y_smooth)
axes1[1, 1].scatter(x, y)
axes1[1, 1].set_title('SIF versus Sharing Mode+Individual Mode')

# plot SIF versus y_traveled_distance
y = np.array(y_traveled_distance)
f = interp1d(x, y, kind='quadratic')
y_smooth = f(x_new)
axes1[1, 2].plot(x_new, y_smooth)
axes1[1, 2].scatter(x, y)
axes1[1, 2].set_title('SIF versus y_traveled_distance')

# plot SIF versus No_Riders
y = np.array(No_riders_list)
f = interp1d(x, y, kind='quadratic')
y_smooth = f(x_new)
axes1[2, 0].plot(x_new, y_smooth)
axes1[2, 0].scatter(x, y)
axes1[2, 0].set_title('SIF versus No_Riders')
axes1[2, 0].set_xlabel('SIF', fontsize=10)
axes1[2, 0].set_ylabel('Total No_Riders', fontsize=10)

# plot SIF versus elapsed_time
y = np.array(elapsed_time)
f = interp1d(x, y, kind='quadratic')
y_smooth = f(x_new)
axes1[2, 1].plot(x_new, y_smooth)
axes1[2, 1].scatter(x, y)
axes1[2, 1].set_title('SIF versus elapsed_time')
axes1[2, 1].set_ylabel('Total elapsed_time', fontsize=10)

# plot SIF versus rss
y = np.array(rss)
f = interp1d(x, y, kind='quadratic')
y_smooth = f(x_new)
axes1[2, 2].plot(x_new, y_smooth)
axes1[2, 2].scatter(x, y)
axes1[2, 2].set_title('SIF versus rss')
axes1[2, 2].set_ylabel('Total rss', fontsize=10)

fig1.subplots_adjust(top=0.9, bottom=0.1, left=0.125, right=0.9, hspace=0.5, wspace=0.3)

# Writing in log.txt file
file.write('{0:16} ::= {1}\n'.format('virtual_memory()', psutil.virtual_memory()))
file.write('{0:16} ::= {1}\n'.format('swap_memory()', psutil.swap_memory()))
file.write('{0:16} ::= {1}\n'.format('memory_info()', psutil.Process(os.getpid()).memory_info()))
file.close()

plt.show()
fig.savefig('/home/samim/PycharmProjects/SharedTaxi/locations.png')
fig1.savefig('/home/samim/PycharmProjects/SharedTaxi/plot.png')