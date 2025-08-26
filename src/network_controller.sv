typedef enum reg [1:0] {
    IDLE,
    INIT, // Initializing Neuron 
    PROC, // processing neuron dynamics (IZH model)
    ACCU  // processing synaptic input accumulation
} c_state;

module network_controller #(
    parameter NR_WIDTH = 56, 
    parameter NR_DEPTH = 16,
    parameter SR_WIDTH = 64,
    parameter SR_DEPTH = 16384,
    parameter MAX_NETWORK_TIME = 65536
)(
    // * Input signals shared with the network processor *
    input logic clk,
    input logic reset,
    input logic                         initialize,  // signal to initialize the neurons and start processing
    input logic                         input_occurred,
    input logic [$clog2(SR_DEPTH)-1:0]  input_index,

    // * Output signals shared with the network processor *
    output logic                        can_receive_input,
    output logic [$clog2(MAX_NETWORK_TIME)-1:0] network_time, // elapsed time in the simulated neural network

    // * Control Signals *
    output logic [$clog2(NR_DEPTH)-1:0] c_neuron_index,     // neuron SRAM access index
    output logic [$clog2(SR_DEPTH)-1:0] c_synapse_index,    // synapse SRAM access index
    output logic                        c_neuron_we,        // neuron SRAM write enable
    output logic                        c_synapse_we,       // synapse SRAM write enable
    output logic                        c_init,             // whether the state is INIT
    output logic                        c_proc,             // whether the state is PROC
    output logic                        c_accu              // whether the state is ACCU
);
    // (1-1) State register and its associated control signals
    c_state state;
    assign c_init = (state == INIT);
    assign c_proc = (state == PROC);
    assign c_accu = (state == ACCU);

    // (1-2) Network time counter which and its associated output signal
    reg [$clog2(MAX_NETWORK_TIME)-1:0] network_time_counter;
    assign network_time = network_time_counter;

    // (1-3) Phase and SRAM access index registers, and their associated control signals
    reg phase;                         // 0: Read SRAM, 1: Write SRAM
    reg [$clog2(NR_DEPTH)-1:0] i_init; // time multiplexing index for neuron initialization
    reg [$clog2(NR_DEPTH)-1:0] i_proc; // time multiplexing index for neuron processing
    reg [$clog2(NR_DEPTH)-1:0] i_accu; // time multiplexing index for neuron accumulation
    reg [$clog2(SR_DEPTH)-1:0] synapse_index;

    assign c_neuron_index = (state == INIT) ? i_init :
                            (state == PROC) ? i_proc :
                            (state == ACCU) ? i_accu : 0;
    assign c_synapse_index = synapse_index;
    assign c_neuron_we = (state == PROC && phase == 1) || (state == INIT);
    assign c_synapse_we = 0;

    // (1-4) output signal whether the controller can receive input at the current clock
    assign can_receive_input = (state == PROC && phase == 1) 
        || ((state == ACCU && i_accu == (NR_DEPTH-1)) && (phase == 1));


    // (2) State transition logic
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state <= IDLE;
            network_time_counter <= 0;

            phase <= 0;
            i_init <= 0;
            i_proc <= 0;
            i_accu <= 0;
            synapse_index <= 0;
        end

        else begin
            if (state == IDLE) begin
                if (initialize == 1) begin
                    state <= INIT;

                    i_init <= 0;
                    phase <= 1;
                end
            end

            else if (state == INIT) begin
                i_init <= i_init + 1;

                if (i_init == (NR_DEPTH-1)) begin
                    state <= PROC;

                    i_proc <= 0;
                    phase <= 0;
                end
            end

            else if (state == PROC) begin
                phase <= ~phase;

                if (phase == 1) begin
                    i_proc <= i_proc + 1;
                end
                
                if (phase == 1 && i_proc == (NR_DEPTH-1)) begin
                    network_time_counter <= network_time_counter + 1;
                end

                if (can_receive_input && input_occurred) begin
                    state <= ACCU;

                    synapse_index <= input_index;
                    i_accu <= 0;
                end
            end

            else if (state == ACCU) begin
                phase <= ~phase;

                if (phase == 1) begin
                    i_accu <= i_accu + 1;
                end

                if (can_receive_input && input_occurred) begin
                    synapse_index <= input_index;
                end

                if (can_receive_input && !input_occurred) begin
                    state <= PROC;
                end
            end
        end
    end
    
endmodule
    
    