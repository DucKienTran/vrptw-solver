import copy


class Route:
    def __init__(self, path=None, cost=0.0, Q=0.0):
        self.path = path if path is not None else []
        self.cost = cost
        self.Q = Q

    def clone(self):
        return copy.deepcopy(self)

    def remove_city(self, city):
        if city in self.path:
            self.path.remove(city)

    def add_city(self, city, after_city=None):
        if after_city is None:
            self.path.append(city)
        else:
            index = self.path.index(after_city)
            self.path.insert(index + 1, city)

    def set_cost(self, cost):
        self.cost = cost

    def get_cost(self):
        return self.cost

    def set_Q(self, Q):
        self.Q = Q

    def get_Q(self):
        return self.Q

    def get_path(self):
        return self.path

    def switch_path(self):
        self.path = self.path[::-1]

    def __str__(self):
        return f"Route(cost={self.cost}, Q={self.Q}, path={self.path})"

    def __repr__(self):
        return self.__str__()
