import SwiftUI

struct ContentView: View {
    @State private var hasStarted = false

    var body: some View {
        if hasStarted {
            RootTabView()
        } else {
            SplashView {
                withAnimation(.easeInOut(duration: 0.25)) {
                    hasStarted = true
                }
            }
        }
    }
}

#Preview {
    ContentView()
}
