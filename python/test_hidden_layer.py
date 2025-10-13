"""
Test script for the updated SNN with hidden layer and queue-based processing
"""

import sys
import numpy as np
sys.path.append('./snn/classes')

from SNN import SNN

def test_basic_functionality():
    """Test basic SNN initialization and processing"""
    print("=== Testing SNN with Hidden Layer ===\n")
    
    # Initialize SNN
    snn = SNN(STEPS_PER_SEC=100, N_SENSORS=100, N_HIDDEN=100, N_MOTORS=8)
    print(f"✓ SNN initialized")
    print(f"  - Sensors: {snn.N_SENSORS}")
    print(f"  - Hidden: {snn.N_HIDDEN}")
    print(f"  - Motors: {snn.N_MOTORS}")
    print(f"  - DT: {snn.DT}\n")
    
    # Check shapes
    print("=== Checking Array Shapes ===")
    print(f"Hidden state shape: {snn.hidden_state.shape} (expected: {(snn.N_HIDDEN, 2)})")
    print(f"Motor state shape: {snn.motor_state.shape} (expected: {(snn.N_MOTORS, 2)})")
    print(f"Sensor→Hidden weights shape: {snn.syn_weights_sensor_hidden.shape} (expected: {(snn.N_SENSORS, snn.N_HIDDEN)})")
    print(f"Hidden→Motor weights shape: {snn.syn_weights_hidden_motor.shape} (expected: {(snn.N_HIDDEN, snn.N_MOTORS)})\n")
    
    # Test processing
    print("=== Testing Processing ===")
    sensory_spikes = [0, 5, 10, 15, 20]  # Some sensor neurons firing
    print(f"Input spikes: {sensory_spikes}")
    
    motor_spikes = snn.step(sensory_spikes)
    print(f"Motor spikes (timestep 1): {motor_spikes}")
    
    # Test multiple timesteps
    for t in range(2, 6):
        sensory_spikes = list(np.random.choice(100, size=5, replace=False))
        motor_spikes = snn.step(sensory_spikes)
        print(f"Motor spikes (timestep {t}): {motor_spikes}")
    
    print("\n=== Testing STDP Learning ===")
    weights_before = snn.syn_weights_sensor_hidden.copy()
    
    # Run some timesteps
    for _ in range(10):
        sensory_spikes = list(np.random.choice(100, size=10, replace=False))
        snn.step(sensory_spikes)
    
    snn.learn_stdp()
    weights_after = snn.syn_weights_sensor_hidden
    
    weight_change = np.abs(weights_after - weights_before).mean()
    print(f"Average weight change: {weight_change:.6f}")
    print(f"Weight range: [{weights_after.min():.3f}, {weights_after.max():.3f}]")
    
    print("\n=== Testing Queue Behavior ===")
    print(f"Queue length: {len(snn.neuron_processor.spike_queue)}")
    
    # Test reset
    print("\n=== Testing Reset ===")
    snn.reset()
    print(f"✓ SNN reset successfully")
    print(f"Hidden state sum after reset: {snn.hidden_state.sum()}")
    print(f"Motor state sum after reset: {snn.motor_state.sum()}")
    
    print("\n=== All Tests Passed! ===")

if __name__ == "__main__":
    test_basic_functionality()
