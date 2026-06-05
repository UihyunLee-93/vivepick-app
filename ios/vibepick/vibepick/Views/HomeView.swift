import SwiftUI

// MARK: - 01. Home (Today's Briefing)
struct HomeView: View {
    @Environment(\.scenePhase) private var scenePhase
    @AppStorage(AppMode.isProModeStorageKey) private var isProMode = false
    @State private var briefs: [Brief] = []
    @State private var briefsBySlot: [BriefSlot: [Brief]] = [:]
    @State private var isLoading = false
    @State private var errorMessage: String? = nil
    @State private var hasLoadedBriefings = false
    @State private var shouldRefreshOnNextActive = false

    private var displayGroups: [BriefSlotGroup] {
        BriefSlotGroup.makeGroups(from: briefs, isProMode: isProMode)
    }

    private var shouldShowLoadingOverlay: Bool {
        isLoading
    }

    private var isInitialBriefingLoad: Bool {
        isLoading && !hasLoadedBriefings
    }

    var body: some View {
        NavigationStack {
            ZStack {
                VPTheme.background.ignoresSafeArea()

                ScrollView {
                    VStack(spacing: 16) {
                        header
                            .padding(.top, 8)
                            .padding(.bottom, 6)

                        if let errorMessage, briefs.isEmpty {
                            errorView(message: errorMessage)
                        }

                        if !isInitialBriefingLoad {
                            ForEach(displayGroups) { group in
                                NavigationLink {
                                    if group.isUnlocked {
                                        BriefDetailView(group: group)
                                    } else {
                                        LockedBriefView(slot: group.slot)
                                    }
                                } label: {
                                    BriefCard(group: group)
                                }
                                .buttonStyle(.plain)
                                .disabled(!group.hasBriefs)
                            }
                        }
                    }
                    .padding(.horizontal, 18)
                    .padding(.bottom, 32)
                }
                .disabled(shouldShowLoadingOverlay)
                .blur(radius: shouldShowLoadingOverlay ? 1.5 : 0)

                if shouldShowLoadingOverlay {
                    loadingOverlay
                }
            }
            .navigationBarHidden(true)
        }
        .task {
            await loadBriefingsIfNeeded()
        }
        .refreshable {
            await loadAllBriefings(forceRefresh: true)
        }
        .onChange(of: scenePhase) { _, newPhase in
            handleScenePhaseChange(newPhase)
        }
    }

    private var loadingOverlay: some View {
        ZStack {
            Color.black.opacity(0.48)
                .ignoresSafeArea()

            ProgressView()
                .controlSize(.regular)
                .tint(.white.opacity(0.92))
        }
        .transition(.opacity)
    }

    private func errorView(message: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                Image(systemName: "exclamationmark.triangle.fill")
                    .font(.system(size: 13, weight: .bold))
                    .foregroundColor(VPTheme.negative)
                Text("데이터 로드 실패")
                    .font(.system(size: 13, weight: .bold))
                    .foregroundColor(.white)
            }

            Text(message)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(VPTheme.textTertiary)
                .lineLimit(3)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(14)
        .background(VPTheme.surface)
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(VPTheme.negative.opacity(0.18), lineWidth: 1))
    }

    private func handleScenePhaseChange(_ newPhase: ScenePhase) {
        switch newPhase {
        case .background:
            shouldRefreshOnNextActive = true
        case .active:
            guard shouldRefreshOnNextActive, hasLoadedBriefings else { return }
            shouldRefreshOnNextActive = false
            Task {
                await refreshCurrentSlotBriefings()
            }
        case .inactive:
            break
        @unknown default:
            break
        }
    }

    private func loadBriefingsIfNeeded() async {
        guard !hasLoadedBriefings else { return }
        await loadAllBriefings(forceRefresh: false)
    }

    private func loadAllBriefings(forceRefresh: Bool = false) async {
        await loadBriefings(for: BriefSlot.allCases, forceRefresh: forceRefresh)
    }

    private func refreshCurrentSlotBriefings() async {
        await loadBriefings(for: [currentBriefSlot()], forceRefresh: true)
    }

    private func loadBriefings(for slots: [BriefSlot], forceRefresh: Bool = false) async {
        guard !isLoading else { return }
        guard forceRefresh || !hasLoadedBriefings else { return }

        isLoading = true
        errorMessage = nil

        do {
            let loadedBriefsBySlot = try await withThrowingTaskGroup(of: (BriefSlot, [Brief]).self) { group in
                for slot in slots {
                    group.addTask {
                        let slotBriefs = try await NetworkManager.shared.fetchBriefings(timeSlot: slot)
                        let todayBriefs = slotBriefs.filter { Calendar.current.isDateInToday($0.publishedAt) }
                        return (slot, todayBriefs)
                    }
                }

                var results: [BriefSlot: [Brief]] = [:]
                for try await (slot, slotBriefs) in group {
                    results[slot] = slotBriefs
                }
                return results
            }

            for (slot, slotBriefs) in loadedBriefsBySlot {
                briefsBySlot[slot] = slotBriefs
            }
            briefs = BriefSlot.allCases.flatMap { briefsBySlot[$0] ?? [] }
            hasLoadedBriefings = true
            isLoading = false
        } catch {
            isLoading = false

            let nsError = error as NSError
            if nsError.domain == NSURLErrorDomain && nsError.code == NSURLErrorCancelled {
                print("API 요청 취소: 화면 전환 또는 SwiftUI task 취소")
                return
            }

            errorMessage = "데이터 로드 실패: \(error.localizedDescription)"
            print("API Error: \(error)")
        }
    }

    private func currentBriefSlot(at date: Date = Date()) -> BriefSlot {
        let components = Calendar.current.dateComponents([.hour, .minute], from: date)
        let minutes = (components.hour ?? 0) * 60 + (components.minute ?? 0)

        if minutes >= 20 * 60 {
            return .night
        } else if minutes >= 12 * 60 + 30 {
            return .noon
        }
        return .morning
    }

    private var header: some View {
        HStack(alignment: .center) {
            VStack(alignment: .leading, spacing: 5) {
                Text("오늘의 브리핑")
                    .font(.system(size: 24, weight: .bold))
                    .foregroundColor(.white)

                Text(todayString())
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(VPTheme.textTertiary)
            }

            Spacer()
        }
    }

    private func todayString() -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "ko_KR")
        formatter.dateFormat = "M월 d일 EEEE"
        return formatter.string(from: Date())
    }
}

// MARK: - Brief Card
struct BriefCard: View {
    let group: BriefSlotGroup

    private var isInactive: Bool { !group.hasBriefs }

    var body: some View {
        ZStack(alignment: .leading) {
            // Background with illustration
            ZStack(alignment: .trailing) {
                RoundedRectangle(cornerRadius: 20)
                    .fill(VPTheme.surface.opacity(isInactive ? 0.55 : 1))

                BriefIllustration(slot: group.slot)
                    .frame(width: 180, height: 130)
                    .padding(.trailing, -10)
                    .opacity(isInactive ? 0.22 : 1)
            }

            // Content
            HStack(alignment: .top, spacing: 0) {
                VStack(alignment: .leading, spacing: 0) {
                    HStack(spacing: 6) {
                        Text(group.slot.emoji)
                            .font(.system(size: 13))
                        Text(group.slot.time)
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(.white.opacity(0.7))
                        Spacer(minLength: 0)
                        Text("\(group.count)건")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(isInactive ? VPTheme.textMuted : VPTheme.textTertiary)
                    }

                    Text(group.slot.title)
                        .font(.system(size: 19, weight: .bold))
                        .foregroundColor(isInactive ? .white.opacity(0.46) : .white)
                        .padding(.top, 6)

                    Text(group.slot.tagline)
                        .font(.system(size: 11.5, weight: .medium))
                        .foregroundColor(isInactive ? VPTheme.textMuted : VPTheme.textTertiary)
                        .lineLimit(2)
                        .multilineTextAlignment(.leading)
                        .fixedSize(horizontal: false, vertical: true)
                        .padding(.top, 4)

                    Spacer(minLength: 8)

                    statusPill
                }

                Spacer(minLength: 0)
            }
            .padding(16)
        }
        .frame(height: 130)
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .overlay(
            RoundedRectangle(cornerRadius: 20)
                .stroke(Color.white.opacity(isInactive ? 0.035 : 0.06), lineWidth: 1)
        )
        .opacity(isInactive ? 0.72 : 1)
    }

    @ViewBuilder
    private var statusPill: some View {
        if !group.hasBriefs {
            HStack(spacing: 5) {
                Image(systemName: "clock")
                    .font(.system(size: 9, weight: .bold))
                Text("브리핑 없음")
                    .font(.system(size: 11, weight: .semibold))
            }
            .foregroundColor(VPTheme.textMuted)
            .padding(.horizontal, 9)
            .padding(.vertical, 4)
            .background(Color.white.opacity(0.04))
            .clipShape(Capsule())
        } else if group.isUnlocked {
            HStack(spacing: 6) {
                Circle()
                    .fill(VPTheme.positive)
                    .frame(width: 6, height: 6)
                Text("열람 가능")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(VPTheme.positive)
            }
        } else {
            HStack(spacing: 5) {
                Image(systemName: "lock.fill")
                    .font(.system(size: 9, weight: .bold))
                Text("준비 중")
                    .font(.system(size: 11, weight: .semibold))
            }
            .foregroundColor(.white.opacity(0.5))
            .padding(.horizontal, 9)
            .padding(.vertical, 4)
            .background(Color.white.opacity(0.06))
            .clipShape(Capsule())
        }
    }
}

// MARK: - Brief Illustration
struct BriefIllustration: View {
    let slot: BriefSlot

    var body: some View {
        ZStack {
            switch slot {
            case .morning: morningArt
            case .noon:    noonArt
            case .night:   nightArt
            }
        }
        .clipped()
    }

    private var morningArt: some View {
        ZStack {
            // Soft horizon glow
            LinearGradient(
                colors: [Color.clear, Color(hex: "FF3E7F").opacity(0.18), Color(hex: "FF8A4C").opacity(0.28)],
                startPoint: .leading, endPoint: .trailing
            )

            // Sun
            Circle()
                .fill(
                    LinearGradient(
                        colors: [Color(hex: "FFD27A"), Color(hex: "FF6B9D")],
                        startPoint: .topLeading, endPoint: .bottomTrailing
                    )
                )
                .frame(width: 78, height: 78)
                .shadow(color: Color(hex: "FF6B9D").opacity(0.6), radius: 22)
                .offset(x: 28, y: 12)

            // Horizon glow line
            Capsule()
                .fill(Color(hex: "FF8A4C").opacity(0.55))
                .frame(width: 160, height: 1.5)
                .blur(radius: 1.5)
                .offset(y: 36)
        }
    }

    private var noonArt: some View {
        ZStack {
            LinearGradient(
                colors: [Color.clear, Color(hex: "5BA8FF").opacity(0.18), Color(hex: "FFB86B").opacity(0.22)],
                startPoint: .leading, endPoint: .trailing
            )

            // High sun
            Circle()
                .fill(
                    LinearGradient(
                        colors: [Color(hex: "FFE7A1"), Color(hex: "FFB86B")],
                        startPoint: .top, endPoint: .bottom
                    )
                )
                .frame(width: 64, height: 64)
                .shadow(color: Color(hex: "FFB86B").opacity(0.55), radius: 18)
                .offset(x: 30, y: -10)

            // Distant horizon
            Capsule()
                .fill(Color(hex: "5BA8FF").opacity(0.35))
                .frame(width: 150, height: 1.2)
                .offset(y: 40)
        }
    }

    private var nightArt: some View {
        ZStack {
            LinearGradient(
                colors: [Color.clear, Color(hex: "1B1659").opacity(0.5), Color(hex: "6E4FF2").opacity(0.45)],
                startPoint: .leading, endPoint: .trailing
            )

            // Crescent moon
            ZStack {
                Circle()
                    .fill(Color(hex: "C7BBFF"))
                    .frame(width: 58, height: 58)
                Circle()
                    .fill(VPTheme.surface)
                    .frame(width: 50, height: 50)
                    .offset(x: -12, y: -6)
            }
            .compositingGroup()
            .shadow(color: Color(hex: "8B5CF6").opacity(0.55), radius: 16)
            .offset(x: 30, y: -10)

            // Stars
            ForEach(0..<5, id: \.self) { i in
                Circle()
                    .fill(Color.white.opacity(0.65))
                    .frame(width: 2.2, height: 2.2)
                    .offset(
                        x: [10, -10, 50, -40, 30][i],
                        y: [-30, 20, 30, -10, 38][i]
                    )
            }
        }
    }
}

#Preview {
    HomeView()
}
