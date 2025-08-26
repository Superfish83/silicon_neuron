module neuron_processor #(
    parameter NR_WIDTH = 48,
    parameter NR_V_WIDTH = 20,
    parameter NR_I_WIDTH = 8,
    parameter NR_V_FRAC_WIDTH = 11
) (
    input logic [NR_WIDTH-1:0] neuron_in,
    output logic [NR_WIDTH-1:0] neuron_out,
    output logic fire
);
    logic signed [NR_V_WIDTH-1:0] v_old, v_new;
    logic signed [NR_V_WIDTH-1:0] w_old, w_new;
    logic signed [NR_I_WIDTH-1:0] I_old, I_new;
    logic signed [NR_V_WIDTH-1:0] I_extend;

    assign {v_old, w_old, I_old} = neuron_in;
    assign I_extend = {I_old[7], I_old, 11'b0}; // Sign extend
    assign I_new = I_old;//0; Todo FOR DEBUGGING
    assign neuron_out = {v_new, w_new, I_new};

    always @(v_new) begin // Todo FOR DEBUGGING
        $display("V: %f",  $itor(v_new * (2.0**-(NR_V_FRAC_WIDTH))));
    end

    IZH_integrator_approx #(
        .V_WIDTH(NR_V_WIDTH),
        .FR_WIDTH(NR_V_FRAC_WIDTH)
    ) integrator  (
        .v_old(v_old),
        .w_old(w_old),
        .I(I_extend),
        .v_new(v_new),
        .w_new(w_new),
        .fire(fire)
    );

endmodule

   
