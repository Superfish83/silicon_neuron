module sram_bank #(
    parameter WIDTH    = 32,       // Width (bits per word)
    parameter DEPTH    = 256       // Depth (# of words)
) (
    input logic                        clk,
    input logic                        we,   // write enable
    input logic [$clog2(DEPTH)-1:0]    addr, // address to read/write
    input logic signed [WIDTH-1:0]     wword, 
    output logic signed [WIDTH-1:0]    rword
);
    logic signed [WIDTH-1:0] memory [0:DEPTH-1]; // SRAM memory array

    always @(posedge clk) begin
        if (we) begin
            memory[addr] <= wword; // Write to SRAM
        end
        rword <= memory[addr]; // Read from SRAM
    end

endmodule