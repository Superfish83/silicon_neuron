interface databus# (
    parameter  WIDTH = 32,
    parameter  DEPTH = 256
);
    wire [WIDTH-1:0] read;
    wire [WIDTH-1:0] write;
    wire we;
    // wire oe,
    // wire cs,
    wire [$clog2(DEPTH)-1:0] addr;

    modport to_mem (
    input read,
    output write, we, addr
    );

    modport from_mem (
    output read,
    input write, we, addr
    );
    
endinterface //databus