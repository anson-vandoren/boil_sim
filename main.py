import matplotlib.pyplot as plt

C_WATER = 4.18  # J/g*°C
BOILING = 100.0
BP_WATER = 100  # °C
POWER = 1500  # watts
RESOLUTION = 100  # milliseconds

U_STEEL = 26  # W/mK
A_STEEL = 0.0645  # m^2
T_AMBIENT = 25
EPS = 0.0001


def calc_new_temp(c: float, in_temp: float, mass: float, e_out: float, e_in: float) -> float:
    energy = e_in - e_out
    delta_t = energy / (mass * c)
    return min(in_temp + delta_t, 1000)  # TODO: fix this


def to_sec(milliseconds: int) -> float:
    return milliseconds / 1000.0


pressure = {}


class Control:
    def __init__(self, setpoint):
        self.setpoint = setpoint
        self.output = False
        self.time = 0
        self.kp = 1e-1
        self.ki = 1e-7
        self.kd = 1e4
        self.pressure = 0
        self.integral = 0
        self.last_error = 0
        self.pressure_history = {}

    def tick(self, feedback):
        error = (self.setpoint - feedback) / self.setpoint
        self.integral += error * RESOLUTION

        kp = error * self.kp
        self.pressure = kp

        ki = self.integral * self.ki
        self.pressure += ki

        derr = (error - self.last_error) / RESOLUTION
        kd = derr * self.kd
        self.pressure += kd

        if self.pressure > 0:
            self.output = True
        else:
            self.output = False

        self.pressure_history[to_sec(self.time)] = self.pressure
        self.time += RESOLUTION
        self.last_error = error

    def turn_on(self):
        self.output = True


def main():
    m_water = 1000  # grams
    t_water = 25  # °C
    t_meas = t_water
    curr_time = 0
    temps_actual = {}
    temps_meas = {}
    setpoint = 80
    relay = Control(setpoint)
    relay.turn_on()
    first_cross = 0
    while curr_time < RESOLUTION * (1000 / RESOLUTION) * 5000:
        heat_loss = U_STEEL * A_STEEL * (t_water - T_AMBIENT)
        heat_gain = POWER * to_sec(RESOLUTION) if relay.output else 0
        t_water = round(calc_new_temp(C_WATER, t_water, m_water, heat_loss, heat_gain), 3)
        temps_actual[to_sec(curr_time)] = t_water
        t_meas = temps_actual.get(to_sec(curr_time) - 10, t_meas)
        t_meas = round(t_meas, 3)
        temps_meas[to_sec(curr_time)] = t_meas
        # print(f"Actual temp: {t_water}\tMeasured temp: {t_meas}\tTime: {to_sec(curr_time)}\tRelay: {relay.output}")

        # control loop
        relay.tick(t_meas)
        curr_time += RESOLUTION
        if t_meas >= setpoint and first_cross == 0:
            first_cross = curr_time

    fig, ax1 = plt.subplots()
    ax1.set_xlabel("time (sec)")
    ax1.set_ylabel("temp (C)")
    ax1.plot(temps_actual.keys(), temps_actual.values(), label="Actual")
    ax1.plot(temps_meas.keys(), temps_meas.values(), label="Measured")
    ax1.plot(temps_actual.keys(), [setpoint for s in range(len(temps_actual))], label="Setpoint")

    ax2 = ax1.twinx()
    ax2.set_ylabel("relative")
    ax2.plot(relay.pressure_history.keys(), relay.pressure_history.values(), label="Pressure")

    fig.tight_layout()
    plt.legend()
    plt.show()
    print(to_sec(first_cross))


if __name__ == "__main__":
    main()
