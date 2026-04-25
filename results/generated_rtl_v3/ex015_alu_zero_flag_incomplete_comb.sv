module alu8 (
    input logic [7:0] a,
    input logic [7:0] b,
    input logic [1:0] op,
    output logic [7:0] y,
    output logic zero
);
    always_comb begin
        case (op)
            2'b00: begin
                y = a + b;
                zero = (y == 8'd0);
            end
            2'b01: begin
                y = a - b;
                zero = (y == 8'd0);
            end
            2'b10: begin
                y = a & b;
                zero = (y == 8'd0);
            end
            2'b11: begin
                y = a | b;
                zero = (y == 8'd0);
            end
        endcase
    end
endmodule
