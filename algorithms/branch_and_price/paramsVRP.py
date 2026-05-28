class ParamsVRP:
    def __init__(self, nbclients=25, capacity=0, mvehic=0, speed=1.0, service_in_tw=False):
        self.datasetName = ""
        self.verbose = False
        self.rndseed = 0
        self.nbclients = nbclients
        self.capacity = capacity
        self.mvehic = mvehic
        self.speed = speed
        self.service_in_tw = service_in_tw

        self.verybig = 1e10
        self.gap = 1e-6
        self.maxlength = 0.0

        self.citieslab = None
        self.posx = None
        self.posy = None
        self.d = None
        self.a = None
        self.b = None
        self.s = None

        self.dist_base = None
        self.dist = None
        self.ttime = None
        self.cost = None
        self.edges = None
        self.wval = None

    def init_params(self, input_path):
        try:
            with open(input_path, 'r') as file:
                lines = file.readlines()

            if len(lines) < 10:
                raise ValueError(f"File {input_path} does not have enough lines.")

            self.datasetName = lines[0].strip()
            print(f'---------- [Dataset: {self.datasetName}] ----------')

            self.mvehic = int(lines[4].strip().split()[0])
            self.capacity = int(lines[4].strip().split()[1])
            self.nbclients = len(lines) - 9
            print(f'Vehicles: {self.mvehic}')
            print(f'Capacity: {self.capacity}')
            print(f'Clients: {self.nbclients}')

            self.citieslab = [None] * self.nbclients
            self.posx = np.zeros(self.nbclients)
            self.posy = np.zeros(self.nbclients)
            self.d = np.zeros(self.nbclients)
            self.a = np.zeros(self.nbclients, dtype=int)
            self.b = np.zeros(self.nbclients, dtype=int)
            self.s = np.zeros(self.nbclients, dtype=int)
            self.dist_base = np.zeros((self.nbclients, self.nbclients))
            self.dist = np.zeros((self.nbclients, self.nbclients))
            self.ttime = np.zeros((self.nbclients, self.nbclients))
            self.cost = np.zeros((self.nbclients, self.nbclients))
            self.edges = np.zeros((self.nbclients, self.nbclients))
            self.wval = np.zeros(self.nbclients)

            for i in range(0, self.nbclients - 1):
                data = lines[9 + i].split()
                self.citieslab[i] = int(data[0])
                self.posx[i] = float(data[1])
                self.posy[i] = float(data[2])
                self.d[i] = float(data[3])
                self.a[i] = int(data[4])
                self.b[i] = int(data[5])
                self.s[i] = int(data[6])
                if self.service_in_tw:
                    self.b[i] -= self.s[i]
                print(f"Client {i}: {self.citieslab[i]} {self.posx[i]} {self.posy[i]} {self.d[i]} {self.a[i]} {self.b[i]} {self.s[i]}")

            # Copy depot info to end depot
            self.citieslab[self.nbclients - 1] = self.nbclients - 1
            self.posx[self.nbclients - 1] = self.posx[0]
            self.posy[self.nbclients - 1] = self.posy[0]
            self.d[self.nbclients - 1] = 0.0
            self.a[self.nbclients - 1] = self.a[0]
            self.b[self.nbclients - 1] = self.b[0]
            self.s[self.nbclients - 1] = 0
            print(f'End depot {self.citieslab[self.nbclients - 1]}: '
                  f'{self.posx[self.nbclients - 1]} {self.posy[self.nbclients - 1]} '
                  f'{self.d[self.nbclients - 1]} {self.a[self.nbclients - 1]} '
                  f'{self.b[self.nbclients - 1]} {self.s[self.nbclients - 1]}')

            for i in range(self.nbclients):
                max_dist = 0
                for j in range(self.nbclients):
                    self.dist_base[i, j] = np.round(
                        10 * np.sqrt((self.posx[i] - self.posx[j]) ** 2 + (self.posy[i] - self.posy[j]) ** 2)) / 10.0
                    if max_dist < self.dist_base[i, j]:
                        max_dist = self.dist_base[i, j]
                self.maxlength += max_dist

            for i in range(self.nbclients):
                self.dist_base[i, 0] = self.verybig
                self.dist_base[self.nbclients - 1, i] = self.verybig
                self.dist_base[i, i] = self.verybig

            for i in range(self.nbclients):
                for j in range(self.nbclients):
                    self.dist[i, j] = self.dist_base[i, j]

            for i in range(self.nbclients):
                for j in range(self.nbclients):
                    self.ttime[i, j] = self.dist_base[i, j] / self.speed

            for j in range(self.nbclients):
                self.cost[0][j] = self.dist[0][j]
                self.cost[j][self.nbclients - 1] = self.dist[j][self.nbclients - 1]

            for i in range(1, self.nbclients):
                self.wval[i] = 0.0

            print(f"---------- [ParamsVRP initialized] ----------")

        except FileNotFoundError:
            print(f"Error: File {input_path} not found.")
        except ValueError as e:
            print(f"ValueError: {e}")
        except Exception as e:
            print(f"Error in init_params: {e}")

    def __str__(self):
        return (f"ParamsVRP(\n"
                f"  nbclients={self.nbclients},\n"
                f"  capacity={self.capacity},\n"
                f"  mvehic={self.mvehic},\n"
                f"  speed={self.speed},\n"
                f"  service_in_tw={self.service_in_tw},\n"
                f"  verybig={self.verybig},\n"
                f"  gap={self.gap},\n"
                f"  maxlength={self.maxlength}\n"
                f")")
