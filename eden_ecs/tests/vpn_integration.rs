use eden_ecs::vpn::EndpointHealth;
use std::time::Duration;
use wiremock::{
    matchers::{method, path},
    Mock, MockServer, ResponseTemplate,
};

#[tokio::test]
async fn fallback_on_429_to_200() {
    let server = MockServer::start().await;

    Mock::given(method("GET"))
        .and(path("/fail"))
        .respond_with(ResponseTemplate::new(429))
        .mount(&server)
        .await;

    Mock::given(method("GET"))
        .and(path("/success"))
        .respond_with(ResponseTemplate::new(200).set_body_string("ok"))
        .mount(&server)
        .await;

    let endpoints = [
        format!("{}/fail", server.uri()),
        format!("{}/success", server.uri()),
    ];

    let mut health = EndpointHealth::with_default_cooldown();

    // first endpoint fails -> cooldown
    let resp1 = reqwest::get(&endpoints[0]).await.unwrap();
    assert_eq!(resp1.status(), 429);
    health.record_failure(&endpoints[0]);
    assert!(health.is_on_cooldown(&endpoints[0]));

    // second succeeds
    let resp2 = reqwest::get(&endpoints[1]).await.unwrap();
    assert_eq!(resp2.status(), 200);
    let body = resp2.text().await.unwrap();
    assert_eq!(body, "ok");

    // mark success for visibility
    health.record_success(&endpoints[1], Duration::from_millis(5));
}
