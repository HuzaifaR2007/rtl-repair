module uart_tx_fsm (
    input logic clk,
    input logic rst,
    input logic start,
    input logic baud_tick,
    input logic [2:0] bit_index,
    output logic in_data,
    output logic in_stop
);
    typedef enum logic [1:0] {IDLE, START, DATA, STOP} state_t;
    state_t state, next_state;

    always_ff @(posedge clk or posedge rst) begin
        if (rst)
            state <= IDLE;
        else
            state <= next_state;
    end

    always_comb begin
        next_state = state;
        case (state)
            IDLE:  if (start) next_state = START;
            START: if (baud_tick) next_state = DATA;
            DATA:  if (baud_tick && bit_index == 3'd7) next_state = STOP;
            STOP:  if (baud_tick) next_state = IDLE;
        endcase
    end

    assign in_data = (state == DATA);
    assign in_stop = (state == STOP);
endmodule
