# Residual RL

The deployed actor and filters are in `../runtime/control.py` (`ResidualPolicy`, `filter_residual`, `guard_residual_authority`, `steering_postprocess`). The archived actor has six inputs, two 256-wide ReLU hidden layers and one tanh output. Checkpoint state normalization is applied before inference.

The deployment residual bound is 0.18 rad. The filter order is saturation, 0.03 rad/step slew limit, LPF with previous-value coefficient 0.6, then saturation. Channel alpha scaling precedes the authority guard. The guard preserves at least half the LQR magnitude when the residual opposes LQR; below a 0.02 rad LQR floor it caps effective residual magnitude at 0.02 rad. Final steering processing follows afterward.

Training settings cannot be inferred from deployment defaults. The archived training summary records 100 episodes and a maximum of 5000 steps, but the exact historical training CLI and all optimizer settings are not archived. Do not relabel current script defaults as confirmed training parameters. Checkpoint redistribution remains pending.
