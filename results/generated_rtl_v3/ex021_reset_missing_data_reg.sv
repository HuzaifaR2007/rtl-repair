module valid_data_reg (
    input logic clk,
    input logic rst,
    input logic load,
    input logic [7:0] data_in,
    output logic [7:0] data_out,
    output logic valid_out
);
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            data_out <= 8'b0;
            valid_out <= 1'b0;
        end else if (load) begin
            data_out <= data_in;
            valid_out <= 1'b1;
        end
    end
endmodule
