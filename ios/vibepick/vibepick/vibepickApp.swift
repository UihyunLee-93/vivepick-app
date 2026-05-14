import SwiftUI

@main
struct VibePickApp: App {
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
                .tabItem { Label("홈", systemImage: "house") }
                .tag(0)

            SavedView()
                .tabItem { Label("저장", systemImage: "bookmark") }
                .tag(1)

            ProfileView()
                .tabItem { Label("프로필", systemImage: "person") }
                .tag(2)
        }
        .tint(VPTheme.orange)
        .onAppear {
            let appearance = UITabBarAppearance()
            appearance.configureWithOpaqueBackground()
            appearance.backgroundColor = UIColor(red: 0.035, green: 0.055, blue: 0.095, alpha: 1.0)
            appearance.shadowColor = UIColor.white.withAlphaComponent(0.08)

            UITabBar.appearance().standardAppearance = appearance
            UITabBar.appearance().scrollEdgeAppearance = appearance
        }
    }
}

#Preview {
    RootTabView()
}
