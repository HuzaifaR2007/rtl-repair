`timescale 1ns/1ps

module traffic_fsm_tb;
    logic clk;
    logic rst;
    logic tick;
    logic green;
    logic red;

    traffic_fsm dut (
        .clk(clk),
        .rst(rst),
        .tick(tick),
        .green(green),
        .red(red)
    );

    always #5 clk = ~clk;

    task check_outputs(input logic expected_green, input logic expected_red, input string label);
        begin
            if (green !== expected_green || red !== expected_red) begin
                $display("FAIL: %s | green=%0b red=%0b expected green=%0b red=%0b",
                         label, green, red, expected_green, expected_red);
                $finish;
            end else begin
                $display("PASS: %s", label);
            end
        end
    endtask

    initial begin
        clk = 0;
        rst = 1;
        tick = 0;

        repeat (2) @(posedge clk);
        rst = 0;
        @(posedge clk);
        #1;
        check_outputs(1'b1, 1'b0, "reset starts in S0 / green");

        tick = 1;
        @(posedge clk);
        #1;
        check_outputs(1'b0, 1'b1, "tick moves S0 to S1 / red");

        tick = 0;
        @(posedge clk);
        #1;
        check_outputs(1'b0, 1'b1, "tick low holds S1 / red");

        tick = 1;
        @(posedge clk);
        #1;
        check_outputs(1'b1, 1'b0, "tick moves S1 back to S0 / green");

        tick = 0;
        @(posedge clk);
        #1;
        check_outputs(1'b1, 1'b0, "tick low holds S0 / green");

        $display("ALL TESTS PASSED");
        $finish;
    end
endmodule