// Top module of a banked SRAM

module sram #(
    parameter WIDTH      = 32,       // Width (bits per word)
    parameter DEPTH      = 16384,    // Depth (# of words)
    parameter NUM_BANKS  = 64        // Number of banks
) (
    input logic                     clk,
    input logic                     we,    // write enable
    input logic [$clog2(DEPTH)-1:0] addr,  // address to read/write
    input logic signed [WIDTH-1:0]  wword,
    output logic signed [WIDTH-1:0] rword
);
    localparam BANK_DEPTH = DEPTH / NUM_BANKS; // Depth of each bank

    // (1) Address Decoding
    logic [$clog2(NUM_BANKS)-1:0]   bank_select;  // index of bank
    logic [$clog2(BANK_DEPTH)-1:0]  bank_addr;    // address within bank
    assign bank_select = addr[$clog2(DEPTH)-1:$clog2(BANK_DEPTH)];
    assign bank_addr = addr[$clog2(BANK_DEPTH)-1:0];

    // (2) Route Read/Write of banks
    logic [WIDTH-1:0] bank_rword [0:NUM_BANKS-1];
    always_comb begin
        rword = bank_rword[bank_select];
    end
    generate
        for (genvar i = 0; i < NUM_BANKS; i++) begin
            sram_bank #(
                .WIDTH(WIDTH),
                .DEPTH(BANK_DEPTH)
            ) bank_i (
                .clk(clk),
                .we(we && (bank_select == i)),
                .addr(bank_addr),
                .wword(wword),
                .rword(bank_rword[i])
            );
        end
    endgenerate
endmodule