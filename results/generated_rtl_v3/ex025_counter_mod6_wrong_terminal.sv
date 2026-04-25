module mod6_counter (
    input logic clk,
    input logic rst,
    input logic en,
    output logic [2:0] count
);
    always_ff @(posedge clk or posedge rst) begin
        if (rst)
            count <= 3'd0;
        else if (en) begin
            if (count == 3'd5)
                count <= 3'd0;
            else
                count <= count + 1'b1;
        end
    end
endmodule
