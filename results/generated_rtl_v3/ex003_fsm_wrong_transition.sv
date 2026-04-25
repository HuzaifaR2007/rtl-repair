module traffic_fsm (
    input logic clk,
    input logic rst,
    input logic tick,
    output logic green,
    output logic red
);
    typedef enum logic [1:0] {S0, S1} state_t;
    state_t state, next_state;

    always_ff @(posedge clk or posedge rst) begin
        if (rst)
            state <= S0;
        else
            state <= next_state;
    end

    always_comb begin
        next_state = state;
        case (state)
            S0: if (tick) next_state = S1;
            S1: if (tick) next_state = S0; // Corrected from S1 to S0
        endcase
    end

    always_comb begin
        green = 0;
        red = 0;
        case (state)
            S0: green = 1;
            S1: red = 1;
        endcase
    end
endmodule
