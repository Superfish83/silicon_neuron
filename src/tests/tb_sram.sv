module tb_sram ();
    localparam WIDTH = 32;
    localparam DEPTH = 16384;
    localparam NUM_BANKS = 64;

    logic clk;
    logic we;
    logic [$clog2(DEPTH)-1:0] addr;
    logic signed [WIDTH-1:0] wword;
    logic signed [WIDTH-1:0] rword;

    sram #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH),
        .NUM_BANKS(NUM_BANKS)
    ) uut (
        .clk(clk),
        .we(we),
        .addr(addr),
        .wword(wword),
        .rword(rword)
    );

    initial begin
        we = 0; addr = 0;
        wword = 0;

        #10;
        we = 1; addr = 1;
        wword = 42;

        #10;
        we = 0; addr = 0;

        #10;
        we = 0; addr = 1;

        #10;
        we = 0; addr = 257;

        #10;
        we = 1; addr = 257;
        wword = 42;

        #10;
        we = 0; addr = 257;
        wword = 7;

        #10;
        we = 0; addr = 1;
        wword = 7;

        #10;
        we = 0; addr = 257;
        wword = 7;
        
        #10;
        we = 1; addr = 257;
        wword = 7;

        #10;
        we = 0; addr = 257;
        wword = 7;
    end

    always begin
        clk = 1;
        forever #5 clk = ~clk; // 5 ns clock period
    end

endmodule