use eden_ecs::api_vpn::{ApiVpn, HopRequest};
use wiremock::{
    matchers::{method, path},
    Mock, MockServer, ResponseTemplate,
};

#[tokio::test]
async fn falls_back_from_429_to_200() {
    let server = MockServer::start().await;

    // anchor served by wiremock
    let anchor = serde_json::json!([
        {"name":"bad","base": format!("{}/fail", server.uri()), "weight":1},
        {"name":"good","base": format!("{}/ok", server.uri()), "weight":3}
    ]);
    Mock::given(method("GET"))
        .and(path("/anchor"))
        .respond_with(ResponseTemplate::new(200).set_body_json(anchor))
        .mount(&server)
        .await;

    // endpoints
    Mock::given(method("GET"))
        .and(path("/fail"))
        .respond_with(ResponseTemplate::new(429))
        .mount(&server)
        .await;
    Mock::given(method("GET"))
        .and(path("/ok"))
        .respond_with(ResponseTemplate::new(200).set_body_string("ok"))
        .mount(&server)
        .await;

    // health probes hit /status/200 under each base
    Mock::given(method("GET"))
        .and(path("/fail/status/200"))
        .respond_with(ResponseTemplate::new(200))
        .mount(&server)
        .await;
    Mock::given(method("GET"))
        .and(path("/ok/status/200"))
        .respond_with(ResponseTemplate::new(200))
        .mount(&server)
        .await;

    let mut vpn = ApiVpn::new(format!("{}/anchor", server.uri()));
    vpn.refresh().await.unwrap();
    let resp = vpn
        .hop(HopRequest {
            path: "".into(), // append nothing so /fail and /ok match
            body: None,
            method: reqwest::Method::GET,
        })
        .await
        .unwrap();

    assert_eq!(resp.text().await.unwrap(), "ok");
}
