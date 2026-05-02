`timescale 1ns/1ps

module mod6_counter_tb;
    logic clk;
    logic rst;
    logic en;
    logic [2:0] count;

    logic [2:0] hold_value;

    mod6_counter dut (
        .clk(clk),
        .rst(rst),
        .en(en),
        .count(count)
    );

    always #5 clk = ~clk;

    task check_count(input logic [2:0] expected, input string label);
        begin
            if (count === 3'd6) begin
                $display("FAIL: %s | count reached invalid modulo-6 value 6", label);
                $finish;
            end

            if (count !== expected) begin
                $display("FAIL: %s | count=%0d expected=%0d", label, count, expected);
                $finish;
            end else begin
                $display("PASS: %s | count=%0d", label, count);
            end
        end
    endtask

    initial begin
        clk = 0;
        rst = 1;
        en = 0;

        repeat (2) @(posedge clk);
        #1;
        check_count(3'd0, "reset clears count to 0");

        rst = 0;
        en = 1;

        @(posedge clk); #1; check_count(3'd1, "enabled count 0 to 1");
        @(posedge clk); #1; check_count(3'd2, "enabled count 1 to 2");
        @(posedge clk); #1; check_count(3'd3, "enabled count 2 to 3");
        @(posedge clk); #1; check_count(3'd4, "enabled count 3 to 4");
        @(posedge clk); #1; check_count(3'd5, "enabled count 4 to 5");
        @(posedge clk); #1; check_count(3'd0, "wraps from 5 back to 0");

        @(posedge clk); #1; check_count(3'd1, "continues after wrap");

        en = 0;
        hold_value = count;

        repeat (3) begin
            @(posedge clk);
            #1;
            check_count(hold_value, "en low holds count");
        end

        rst = 1;
        @(posedge clk);
        #1;
        check_count(3'd0, "reset clears count during operation");

        $display("ALL TESTS PASSED");
        $finish;
    end
endmodule