import SwiftUI
import UserNotifications

final class NotificationPresentationDelegate: NSObject, UNUserNotificationCenterDelegate {
    static let shared = NotificationPresentationDelegate()

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification
    ) async -> UNNotificationPresentationOptions {
        [.banner, .list, .sound]
    }
}

struct NotificationService {
    static let shared = NotificationService()

    private let center = UNUserNotificationCenter.current()

    func configureForegroundPresentation() {
        center.delegate = NotificationPresentationDelegate.shared
    }

    func requestAuthorizationIfNeeded() async -> Bool {
        let settings = await center.notificationSettings()

        switch settings.authorizationStatus {
        case .authorized, .provisional, .ephemeral:
            return true
        case .notDetermined:
            do {
                return try await center.requestAuthorization(options: [.alert, .sound, .badge])
            } catch {
                return false
            }
        case .denied:
            return false
        @unknown default:
            return false
        }
    }

    func updateDailyNotification(for slot: BriefSlot, isEnabled: Bool) async {
        let identifier = dailyIdentifier(for: slot)
        center.removePendingNotificationRequests(withIdentifiers: [identifier])

        guard isEnabled else { return }
        guard await requestAuthorizationIfNeeded() else { return }

        var dateComponents = DateComponents()
        dateComponents.hour = slot.notificationHour
        dateComponents.minute = slot.notificationMinute

        let content = UNMutableNotificationContent()
        content.title = slot.notificationTitle
        content.body = slot.notificationBody
        content.sound = .default
        content.threadIdentifier = "daily-brief"

        let trigger = UNCalendarNotificationTrigger(dateMatching: dateComponents, repeats: true)
        let request = UNNotificationRequest(identifier: identifier, content: content, trigger: trigger)

        try? await center.add(request)
    }

    func scheduleTestNotification() async -> Date? {
        guard await requestAuthorizationIfNeeded() else { return nil }

        await removePendingTestNotifications()

        let scheduledDate = Date().addingTimeInterval(10)
        let content = UNMutableNotificationContent()
        content.title = "테스트 알림"
        content.body = "10초 테스트 알림입니다. 앱이 켜져 있어도 배너로 표시됩니다."
        content.sound = .default
        content.threadIdentifier = "test-brief"

        let trigger = UNTimeIntervalNotificationTrigger(timeInterval: 10, repeats: false)
        let request = UNNotificationRequest(
            identifier: "test-brief-\(UUID().uuidString)",
            content: content,
            trigger: trigger
        )

        do {
            try await center.add(request)
            return scheduledDate
        } catch {
            return nil
        }
    }

    private func removePendingTestNotifications() async {
        let requests = await withCheckedContinuation { continuation in
            center.getPendingNotificationRequests { requests in
                continuation.resume(returning: requests)
            }
        }

        let identifiers = requests
            .map(\.identifier)
            .filter { $0.hasPrefix("test-brief-") }

        center.removePendingNotificationRequests(withIdentifiers: identifiers)
    }

    private func dailyIdentifier(for slot: BriefSlot) -> String {
        "daily-brief-\(slot.rawValue)"
    }
}

extension BriefSlot {
    var notificationHour: Int {
        switch self {
        case .morning: return 7
        case .noon: return 12
        case .night: return 20
        }
    }

    var notificationMinute: Int {
        switch self {
        case .morning: return 30
        case .noon: return 30
        case .night: return 0
        }
    }

    var notificationTitle: String {
        "\(title)이 도착했어요"
    }

    var notificationBody: String {
        switch self {
        case .morning:
            return "장 시작 전 시장 분위기와 오늘 볼 만한 흐름을 확인해보세요."
        case .noon:
            return "오전장을 지나며 바뀐 시장 분위기를 짧게 정리했어요."
        case .night:
            return "오늘 시장 마감 분위기와 내일 볼 포인트를 확인해보세요."
        }
    }
}

@main
struct VibePickApp: App {
    init() {
        NotificationService.shared.configureForegroundPresentation()
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

struct RootTabView: View {
    @State private var selectedTab = 0

    var body: some View {
        TabView(selection: $selectedTab) {
            HomeView()
                .tabItem { Label("홈", systemImage: "house.fill") }
                .tag(0)

            SettingsView()
                .tabItem { Label("설정", systemImage: "gearshape.fill") }
                .tag(1)
        }
        .tint(VPTheme.purple)
        .onAppear {
            let appearance = UITabBarAppearance()
            appearance.configureWithOpaqueBackground()
            appearance.backgroundColor = UIColor(red: 0.043, green: 0.047, blue: 0.094, alpha: 1.0)
            appearance.shadowColor = UIColor.white.withAlphaComponent(0.08)

            UITabBar.appearance().standardAppearance = appearance
            UITabBar.appearance().scrollEdgeAppearance = appearance
        }
    }
}

#Preview {
    RootTabView()
}
