module tb_network_processor;
    localparam NR_WIDTH           = 48; // width of a neuron word
    localparam NR_DEPTH           = 16; // # of words in neuron SRAM
    localparam NR_V_WIDTH         = 20; // width of each of the V and W parts in a neuron word
    localparam NR_V_FRAC_WIDTH    = 11; // width of each of the fractional parts of V and W (fixed-point)
    localparam NR_I_WIDTH         = 8;  // width of I part in a neuron word

    localparam SR_WIDTH           = 64;      // width of a synapse word
    localparam SR_DEPTH           = 16384;   // # of words in synapse SRAM
    localparam SR_NUM_BANKS       = 64;      // # of banks in synapse SRAM

    localparam MAX_NETWORK_TIME   = 65536;   // maximum simulation step

    // Processor Module input
    logic clk;
    logic reset;
    logic initialize;
    logic input_occurred;
    logic [$clog2(SR_DEPTH)-1:0] input_index;
    
    logic syn_write_occurred; // synapse SRAM write
    logic [$clog2(SR_DEPTH)-1:0] syn_write_index;
    logic [SR_WIDTH-1:0] syn_write_wword;

    // Processor Module output
    logic can_receive_input;
    logic can_update_synapse;
    logic [$clog2(MAX_NETWORK_TIME)-1:0] network_time;
    logic output_occurred;
    logic [$clog2(NR_DEPTH)-1:0] output_index;

    network_processor #(
        .NR_WIDTH(NR_WIDTH),
        .NR_DEPTH(NR_DEPTH),
        .NR_V_WIDTH(NR_V_WIDTH),
        .NR_V_FRAC_WIDTH(NR_V_FRAC_WIDTH),
        .NR_I_WIDTH(NR_I_WIDTH),

        .SR_WIDTH(SR_WIDTH),
        .SR_DEPTH(SR_DEPTH),
        .SR_NUM_BANKS(SR_NUM_BANKS),

        .MAX_NETWORK_TIME(MAX_NETWORK_TIME)
    ) uut (
        .clk(clk),
        .reset(reset),
        .initialize(initialize),
        .input_occurred(input_occurred),
        .input_index(input_index),
        .syn_write_occurred(syn_write_occurred),
        .syn_write_index(syn_write_index),
        .syn_write_wword(syn_write_wword),
        .can_receive_input(can_receive_input),
        .can_update_synapse(can_update_synapse),
        .network_time(network_time),
        .output_occurred(output_occurred),
        .output_index(output_index)
    );

initial begin
    $dumpfile("tb_network_processor.vcd");
    $dumpvars(0, tb_network_processor);
end

localparam CYCLE = 10;
always #(CYCLE/2) clk=~clk;

initial begin
    clk = 1;
    reset = 1;
    initialize = 0;
    input_occurred = 0;
    input_index = 0;

    #(CYCLE);
    reset = 0;

    #(CYCLE*4);
    initialize = 1;
    
    #(CYCLE);
    initialize = 0;
end

endmodule