module edge_detect (
    input logic clk,
    input logic rst,
    input logic sig,
    output logic pulse
);
    logic prev;

    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            prev <= 1'b0;
            pulse <= 1'b0;
        end else begin
            prev <= sig;
            pulse <= sig & ~prev;
        end
    end
endmodule
