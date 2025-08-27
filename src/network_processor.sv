module network_processor #(
    parameter NR_WIDTH           = 48, // width of a neuron word
    parameter NR_DEPTH           = 16, // # of words in neuron SRAM
    parameter NR_V_WIDTH         = 20, // width of each of the V and W parts in a neuron word
    parameter NR_V_FRAC_WIDTH    = 11, // width of each of the fractional parts of V and W (fixed-point)
    parameter NR_I_WIDTH         = 8,  // width of I part in a neuron word

    parameter SR_WIDTH           = 64,      // width of a synapse word
    parameter SR_DEPTH           = 16384,   // # of words in synapse SRAM
    parameter SR_NUM_BANKS       = 64,      // # of banks in synapse SRAM

    parameter MAX_NETWORK_TIME   = 65536    // maximum simulation step
)(
    // * Input signals shared with the controller *
    input logic clk,
    input logic reset,
    input logic                         initialize,  // signal to initialize the neurons and start processing
    input logic                         input_occurred, // spike input
    input logic [$clog2(SR_DEPTH)-1:0]  input_index,

    // * Input signals NOT shared with the controller *
    input logic                         syn_write_occurred, // synapse SRAM write
    input logic [$clog2(SR_DEPTH)-1:0]  syn_write_index, 
    input logic [SR_WIDTH-1:0]          syn_write_wword,

    // * Output signals shared with the controller *
    output logic                        can_receive_input,
    output logic                        can_update_synapse,
    output logic [$clog2(MAX_NETWORK_TIME)-1:0] network_time, // elapsed time in the simulated neural network

    // * Output signals NOT shared with the controller *
    output logic                        output_occurred,
    output logic [$clog2(NR_DEPTH)-1:0] output_index
);
    localparam SR_SYN_WIDTH = SR_WIDTH / NR_DEPTH; // width of a synaptic weight in synapse words

    // (1) wires carrying internal control signals
    logic [$clog2(NR_DEPTH)-1:0] c_neuron_index;
    logic [$clog2(SR_DEPTH)-1:0] c_syn_read_index;
    logic c_neuron_we;
    logic c_init;
    logic c_proc;
    logic c_accu;

    // (2) Controller (Finite State Machine)
    network_controller #(
        .NR_WIDTH(NR_WIDTH),
        .NR_DEPTH(NR_DEPTH),
        .SR_WIDTH(SR_WIDTH),
        .SR_DEPTH(SR_DEPTH),
        .MAX_NETWORK_TIME(MAX_NETWORK_TIME)
    ) controller (
        // * Input signals shared with the network processor *
        .clk(clk),
        .reset(reset),
        .initialize(initialize),
        .input_occurred(input_occurred),
        .input_index(input_index),

        // * Output signals shared with the network processor *
        .can_receive_input(can_receive_input),
        .can_update_synapse(can_update_synapse),
        .network_time(network_time),

        // * Control Signals *
        .c_neuron_index(c_neuron_index),
        .c_syn_read_index(c_syn_read_index),
        .c_neuron_we(c_neuron_we),
        .c_init(c_init),
        .c_proc(c_proc),
        .c_accu(c_accu)
    );

    // (3) SRAMs storing neuron states and synaptic weights

    // (3-1) Multiplexing neuron read/write signals
    logic [NR_WIDTH-1:0] neuron_rword;
    logic [NR_WIDTH-1:0] neuron_wword_init;
    logic [NR_WIDTH-1:0] neuron_wword_accu;
    logic [NR_WIDTH-1:0] neuron_wword_proc;
    logic [NR_WIDTH-1:0] neuron_wword;

    assign neuron_wword_init = { (20'(-65)<<<11), (20'(-12)<<<11), (8'(0)) }; // Todo: replace hardcoded reset value
    assign neuron_wword = c_init ? neuron_wword_init :
                          c_accu ? neuron_wword_accu :
                          c_proc ? neuron_wword_proc : 0;

    logic [$clog2(SR_DEPTH)-1:0] synapse_index;
    logic synapse_we;
    logic [SR_WIDTH-1:0] synapse_rword;
    logic [SR_WIDTH-1:0] synapse_wword;
    assign synapse_we = (can_update_synapse && syn_write_occurred);
    assign synapse_index = synapse_we ? syn_write_index : c_syn_read_index;
    assign synapse_wword = syn_write_wword;

    // (3-2) Neuron SRAM (Single Bank)
    sram #(
        .WIDTH(NR_WIDTH),
        .DEPTH(NR_DEPTH),
        .NUM_BANKS(1)
    ) sram_neuron (
        .clk(clk),
        .we(c_neuron_we),
        .addr(c_neuron_index),
        .wword(neuron_wword),
        .rword(neuron_rword)
    );

    // (3-3) Synapse SRAM (Multiple Banks)
    sram #(
        .WIDTH(SR_WIDTH),
        .DEPTH(SR_DEPTH),
        .NUM_BANKS(SR_NUM_BANKS)
    ) sram_synapse (
        .clk(clk),
        .we(synapse_we),
        .addr(synapse_index),
        .wword(synapse_wword),
        .rword(synapse_rword)
    );

    // (4) Time-multiplexed Neuron Accumulator and Processor

    // (4-1) Neuron Accumulator
    logic [SR_SYN_WIDTH-1:0] weight;
    assign weight = synapse_rword[(SR_SYN_WIDTH * c_neuron_index) +: SR_SYN_WIDTH];

    neuron_accumulator #(
        .NR_WIDTH(NR_WIDTH),
        .NR_I_WIDTH(NR_I_WIDTH),
        .SR_SYN_WIDTH(SR_SYN_WIDTH)
    ) neuron_accu (
        .neuron_in(neuron_rword),
        .neuron_out(neuron_wword_accu),
        .syn_in(weight)
    );

    // (4-2) Neuron Processor
    assign output_index = c_neuron_index;

    neuron_processor #(
        .NR_WIDTH(NR_WIDTH),
        .NR_V_WIDTH(NR_V_WIDTH),
        .NR_I_WIDTH(NR_I_WIDTH),
        .NR_V_FRAC_WIDTH(NR_V_FRAC_WIDTH)
    ) neuron_proc (
        .neuron_in(neuron_rword),
        .neuron_out(neuron_wword_proc),
        .fire(output_occurred)
    );


endmodule