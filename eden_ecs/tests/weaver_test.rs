use eden_ecs::weaver::{PolicyContext, WeaverPolicy};

struct ClampingPolicy;

impl WeaverPolicy for ClampingPolicy {
    fn apply(&mut self, ctx: &mut PolicyContext<'_>) {
        for weight in ctx.edge_weights.iter_mut() {
            *weight = weight.clamp(0.0, 1.0);
        }
    }

    fn name(&self) -> &'static str {
        "ClampingPolicy"
    }
}

#[test]
fn custom_weaver_policy_clamps_edge_weights() {
    let mut edge_weights = vec![-0.25_f32, 0.25, 1.25, 0.75];
    let flow_rates = vec![0.0_f32; edge_weights.len()];

    let mut ctx = PolicyContext {
        edge_weights: &mut edge_weights,
        flow_rates: &flow_rates,
    };

    let mut policy = ClampingPolicy;
    policy.apply(&mut ctx);

    assert_eq!(ctx.edge_weights.as_slice(), &[0.0, 0.25, 1.0, 0.75]);
    assert_eq!(policy.name(), "ClampingPolicy");
}
