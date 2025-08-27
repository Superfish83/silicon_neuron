module neuron_accumulator #(
    parameter NR_WIDTH = 56,
    parameter NR_I_WIDTH = 8,
    parameter SR_SYN_WIDTH = 4
) (
    input logic [NR_WIDTH-1:0] neuron_in,
    input logic signed [SR_SYN_WIDTH-1:0] syn_in,
    output logic [NR_WIDTH-1:0] neuron_out
);
    logic signed [NR_I_WIDTH-1:0] I_old, synin_ext, I_tmp, I_new;

    always_comb begin
        I_old = neuron_in[NR_I_WIDTH-1:0];
        
        // sign extend
        synin_ext = {{4{syn_in[3]}}, syn_in}; // Todo: replace hardcoded reset value
        I_tmp = I_old + synin_ext;

        // Addition with saturation
        if (I_old[NR_I_WIDTH-1] == synin_ext[NR_I_WIDTH-1]) begin
            if (I_tmp[NR_I_WIDTH-1] != I_old[NR_I_WIDTH-1]) begin // When overflow is detected
                I_new = {I_old[NR_I_WIDTH-1:0], 7'(0)}; // Todo: replace hardcoded reset value
            end
            else begin
                I_new = I_tmp;
            end
        end
        else begin
            I_new = I_tmp;
        end

        //$display("Accumulator: I_old = %d, synin_ext = %d, I_new = %d", I_old, synin_ext, I_new);

        neuron_out = {neuron_in[NR_WIDTH-1:NR_I_WIDTH], I_new};
    end

endmodule