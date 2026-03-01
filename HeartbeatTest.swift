import XCTest

class HeartbeatTest: XCTestCase {
    let timingInterval: DispatchTimeInterval = .nanoseconds(449)
    var timer: DispatchSourceTimer?
    var elapsed: [Double] = []

    override func setUp() {
        super.setUp()
        timer = DispatchSource.makeTimerSource()
        timer?.schedule(deadline: .now() + timingInterval, repeating: timingInterval)
        timer?.setEventHandler { [weak self] in
            let start = DispatchTime.now()
            // Test code to be executed should be inserted here
            let end = DispatchTime.now()
            let timeInterval = end.uptimeNanoseconds - start.uptimeNanoseconds
            self?.elapsed.append(Double(timeInterval))
        }
    }

    override func tearDown() {
        timer?.cancel()
        timer = nil
        super.tearDown()
    }

    func testHeartbeatTiming() {
        timer?.resume()
        // Let the test run for a specific duration to gather timing data
        let runDuration: TimeInterval = 1.0 // seconds
        sleep(UInt32(runDuration))
        timer?.cancel()

        let averageTiming = elapsed.reduce(0, +) / Double(elapsed.count)
        XCTAssert(averageTiming > 440, "Average timing should exceed 440ns")
        XCTAssert(averageTiming < 460, "Average timing should be less than 460ns")
    }
}