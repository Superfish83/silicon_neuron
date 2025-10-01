import numpy as np
import matplotlib.pyplot as plt

from approxTest import f_orig

def compare_plot():
    num_lines = 1600
    dt = 1/4 #ms
    T = np.arange(0, num_lines * dt, dt)
    I = 10.0

    V1 = get_v_from_f(T, dt, I)
    V2 = get_v_from_transcript(num_lines)
    plt.plot(T, V1, color='blue', linestyle='--', label='Python Sim')
    plt.plot(T, V2, color='red', label='Verilog Sim Transcript')

    plt.title(f'I = {I}mA')
    plt.xlabel('Time (ms)')
    plt.ylabel('V (mV)')
    plt.ylim(-80, 40)

    plt.grid()
    plt.legend()
    plt.show()


def get_v_from_f(T, dt, I):
    V = np.zeros_like(T)
    W = np.zeros_like(T)

    V[0] = -65.0
    W[0] = -12.0

    for i in range(len(T)-1):
        I_t = I if i >= 10 else 0.0

        dVdt, dWdt = f_orig(V[i], W[i], I_t)
        V[i+1] = V[i] + dVdt * dt
        W[i+1] = W[i] + dWdt * dt

        if V[i+1] >= 32:
            V[i+1] = -65.0
            W[i+1] += 8.0

    return V

def get_v_from_transcript(num_lines):
    count = 0
    v_list = []

    with open('./python/transcript.txt', 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith('# V: '):
                v_list.append(float(line[5:].strip()))
                count += 1
                if count >= num_lines:
                    break
    return np.array(v_list)


if __name__ == "__main__":
    compare_plot()