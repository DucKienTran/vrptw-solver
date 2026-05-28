import numpy as np
from .route import Route
from .paramsVRP import ParamsVRP
from sortedcontainers import SortedSet
from functools import total_ordering

'''
Shortest path with resource constraints.
Inspired by Irnish and Desaulniers, "SHORTEST PATH PROBLEMS WITH RESOURCE CONSTRAINTS".
For educational demonstration only.

Four main data structures:
  labels      - list of all labels created along feasible paths
  U           - sorted set of indices of unprocessed labels
  P           - sorted set of indices of processed labels ending at depot with negative cost
  city2labels - for each city, the list of label indices attached to that vertex
'''


class SPPRC:

    def __init__(self, userParam=None):
        self.paramsVRP = ParamsVRP() if userParam is None else userParam
        self.labels = []

    @total_ordering
    class label:
        def __init__(self, city, index_prev_label, cost, ttime, demand, dominated, vertex_visited, parent):
            self.city = city
            self.index_prev_label = index_prev_label
            self.cost = cost
            self.ttime = ttime
            self.demand = demand
            self.dominated = dominated
            self.vertex_visited = vertex_visited
            self.parent = parent

        def updateLabel(self, a1, a2, a3, a4, a5, a6, a7):
            self.city = a1
            self.index_prev_label = a2
            self.cost = a3
            self.ttime = a4
            self.demand = a5
            self.dominated = a6
            self.vertex_visited = a7

        def __lt__(self, other):
            if self.cost - other.cost < -1e-7:
                return True
            elif self.cost - other.cost > 1e-7:
                return False
            else:
                if self.city == other.city:
                    if self.ttime - other.ttime < -1e-7:
                        return True
                    elif self.ttime - other.ttime > 1e-7:
                        return False
                    else:
                        if self.demand - other.demand < -1e-7:
                            return True
                        elif self.demand - other.demand > 1e-7:
                            return False
                        else:
                            i = 0
                            while i < self.parent.paramsVRP.nbclients:
                                if self.vertex_visited[i] != other.vertex_visited[i]:
                                    if self.vertex_visited[i]:
                                        return True
                                    else:
                                        return False
                                i += 1
                            return False
                elif self.city > other.city:
                    return False
                else:
                    return True

        def __eq__(self, other):
            if self.cost - other.cost < -1e-7 or self.cost - other.cost > 1e-7:
                return False
            if self.city < other.city or self.city > other.city:
                return False
            if self.ttime - other.ttime < -1e-7 or self.ttime - other.ttime > 1e-7:
                return False
            if self.demand - other.demand < -1e-7 or self.demand - other.demand > 1e-7:
                return False

            if self.cost - other.cost > -1e-7 and self.cost - other.cost < 1e-7:
                if self.city == other.city:
                    if self.ttime - other.ttime > -1e-7 and self.ttime - other.ttime < 1e-7:
                        if self.demand - other.demand > -1e-7 and self.demand - other.demand < 1e-7:
                            i = 0
                            while i < self.parent.paramsVRP.nbclients:
                                if self.vertex_visited[i] != other.vertex_visited[i]:
                                    return False
                                i += 1
                            return True

    def shortestPath(self, userParamArg, routes, nbroute):
        print("[---SPPRC.shortestPath called---]")
        self.paramsVRP = userParamArg

        U = SortedSet(key=lambda x: x)
        P = SortedSet(key=lambda x: x)

        cust = [False] * self.paramsVRP.nbclients
        cust[0] = True
        self.labels.append(self.label(0, -1, 0.0, 0, 0, False, cust, self))
        U.add(0)

        checkDom = [0] * self.paramsVRP.nbclients
        city2labels = [[] for _ in range(self.paramsVRP.nbclients)]
        city2labels[0].append(0)

        nbsol = 0
        maxsol = 2 * nbroute

        while U and nbsol < maxsol:
            current_idx = U.pop(0)
            current = self.labels[current_idx]

            # Dominance check
            cleaning = []
            for i in range(checkDom[current.city], len(city2labels[current.city])):
                for j in range(i):
                    l1, l2 = city2labels[current.city][i], city2labels[current.city][j]
                    la1, la2 = self.labels[l1], self.labels[l2]
                    if not la1.dominated and not la2.dominated and l1 != l2:

                        # Check if label 2 is dominated by label 1
                        pathdom = True
                        for k in range(1, self.paramsVRP.nbclients - 1):
                            if not pathdom:
                                break
                            pathdom = pathdom and (not la1.vertex_visited[k] or la2.vertex_visited[k])
                        if pathdom and la1.cost <= la2.cost and la1.ttime <= la2.ttime and la1.demand <= la2.demand:
                            U.discard(l2)
                            self.labels[l2].dominated = True
                            cleaning.append(l2)
                            pathdom = False

                        # Check if label 1 is dominated by label 2
                        pathdom = True
                        for k in range(1, self.paramsVRP.nbclients - 1):
                            pathdom = pathdom and (not la2.vertex_visited[k] or la1.vertex_visited[k])
                        if pathdom and la2.cost <= la1.cost and la2.ttime <= la1.ttime and la2.demand <= la1.demand:
                            U.discard(l1)
                            self.labels[l1].dominated = True
                            cleaning.append(l1)
                            j = len(city2labels[current.city])

            for c in cleaning:
                city2labels[current.city].remove(c)
            cleaning = None

            checkDom[current.city] = len(city2labels[current.city])

            # Expand label
            if not current.dominated:
                if current.city == self.paramsVRP.nbclients - 1:
                    if current.cost < -1e-7:
                        P.add(current_idx)
                        nbsol = sum(1 for labi in P if not self.labels[labi].dominated)
                else:
                    for i in range(self.paramsVRP.nbclients):
                        if not current.vertex_visited[i] and self.paramsVRP.dist[current.city][i] < self.paramsVRP.verybig - 1e-6:
                            tt = current.ttime + self.paramsVRP.ttime[current.city][i] + self.paramsVRP.s[current.city]
                            if tt < self.paramsVRP.a[i]:
                                tt = self.paramsVRP.a[i]
                            d = current.demand + self.paramsVRP.d[i]

                            if tt <= self.paramsVRP.b[i] and d <= self.paramsVRP.capacity:
                                idx = len(self.labels)
                                newcust = current.vertex_visited[:]
                                newcust[i] = True

                                # Speedup: Feillet 2004 technique
                                for j in range(1, self.paramsVRP.nbclients - 1):
                                    if not newcust[j]:
                                        tt2 = tt + self.paramsVRP.ttime[i][j] + self.paramsVRP.s[i]
                                        d2 = d + self.paramsVRP.d[j]
                                        if tt2 > self.paramsVRP.b[j] or d2 > self.paramsVRP.capacity:
                                            newcust[j] = True

                                self.labels.append(self.label(i, current_idx, current.cost + self.paramsVRP.cost[current.city][i], tt, d, False, newcust, self))
                                if idx not in U:
                                    U.add(idx)
                                    city2labels[i].append(idx)
                                else:
                                    self.labels[idx].dominated = True

        # Extract routes from P
        i = 0
        checkDom = None
        while i < nbroute and P:
            lab = P.pop(0)
            if not self.labels[lab].dominated:
                if self.labels[lab].cost < -1e-4:
                    route = Route()
                    route.set_cost(self.labels[lab].cost)
                    route.add_city(self.labels[lab].city)
                    path = self.labels[lab].index_prev_label
                    while path >= 0:
                        route.add_city(self.labels[path].city)
                        path = self.labels[path].index_prev_label
                    route.switch_path()
                    routes.append(route)
                    i += 1
