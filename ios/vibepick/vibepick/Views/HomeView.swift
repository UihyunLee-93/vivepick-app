import SwiftUI

// MARK: - 01. Home (Today's Briefing)
struct HomeView: View {
    @AppStorage(AppMode.isProModeStorageKey) private var isProMode = false
    @State private var briefs: [Brief] = []
    @State private var isLoading = false
    @State private var errorMessage: String? = nil
    @State private var crawlLoading = false
    @State private var crawlMessage = ""
    @State private var crawlAttemptCount = 0
    @State private var lastCrawlCheckText = "-"

    private var displayGroups: [BriefSlotGroup] {
        BriefSlotGroup.makeGroups(from: briefs, isProMode: isProMode)
    }

    private var shouldShowCrawlDetailCard: Bool {
        crawlLoading || !crawlMessage.isEmpty || !briefs.isEmpty
    }

    private var firstLoadedBrief: Brief? {
        briefs.sorted { $0.publishedAt > $1.publishedAt }.first
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

                        crawlTestPanel

                        if shouldShowCrawlDetailCard {
                            crawlDetailCard
                        }

                        if isLoading && briefs.isEmpty {
                            loadingView
                        }

                        if let errorMessage, briefs.isEmpty {
                            errorView(message: errorMessage)
                        }

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
                        }
                    }
                    .padding(.horizontal, 18)
                    .padding(.bottom, 32)
                }
            }
            .navigationBarHidden(true)
        }
        .task {
            await loadBriefings()
        }
        .refreshable {
            await loadBriefings()
        }
    }

    private var crawlTestPanel: some View {
        VStack(alignment: .leading, spacing: 10) {
            Button {
                Task {
                    await testCrawling()
                }
            } label: {
                HStack(spacing: 8) {
                    Image(systemName: "bolt.fill")
                        .font(.system(size: 13, weight: .bold))
                    Text(crawlLoading ? "크롤링 진행 중" : "크롤링 테스트")
                        .font(.system(size: 13, weight: .bold))
                    Spacer()
                    if crawlLoading {
                        ProgressView()
                            .tint(.white)
                    }
                }
                .foregroundColor(.white)
                .padding(.horizontal, 14)
                .frame(height: 44)
                .background(
                    LinearGradient(
                        colors: [Color(hex: "2563EB"), VPTheme.purple],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .clipShape(RoundedRectangle(cornerRadius: 14))
            }
            .buttonStyle(.plain)
            .disabled(crawlLoading)

            if !crawlMessage.isEmpty {
                Text(crawlMessage)
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(VPTheme.textTertiary)
                    .lineLimit(2)
            }
        }
        .padding(14)
        .background(VPTheme.surface)
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(Color.white.opacity(0.05), lineWidth: 1))
    }

    private var crawlDetailCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: "doc.text.magnifyingglass")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(VPTheme.purple)

                Text("크롤링 테스트 확인")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.white)

                Spacer()

                Text(briefs.isEmpty ? "대기" : "서버 데이터")
                    .font(.system(size: 10, weight: .bold))
                    .foregroundColor(briefs.isEmpty ? VPTheme.textTertiary : VPTheme.positive)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background((briefs.isEmpty ? Color.white : VPTheme.positive).opacity(0.10))
                    .clipShape(Capsule())
            }

            HStack(spacing: 8) {
                CrawlMetric(title: "요청", value: "\(crawlAttemptCount)회")
                CrawlMetric(title: "브리핑", value: "\(briefs.count)개")
                CrawlMetric(title: "확인", value: lastCrawlCheckText)
            }

            if let firstLoadedBrief {
                VStack(alignment: .leading, spacing: 8) {
                    HStack(spacing: 6) {
                        Text(firstLoadedBrief.slot.emoji)
                            .font(.system(size: 13))
                        Text(firstLoadedBrief.slot.title)
                            .font(.system(size: 12, weight: .bold))
                            .foregroundColor(.white.opacity(0.86))
                        Spacer()
                        Text("총 \(briefs.count)개")
                            .font(.system(size: 10, weight: .semibold))
                            .foregroundColor(VPTheme.textTertiary)
                    }

                    Text(firstLoadedBrief.title)
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(.white)
                        .lineLimit(2)

                    Text(firstLoadedBrief.summary)
                        .font(.system(size: 11.5, weight: .medium))
                        .foregroundColor(VPTheme.textTertiary)
                        .lineLimit(2)

                    NavigationLink {
                        CardDetailView(brief: firstLoadedBrief)
                    } label: {
                        HStack(spacing: 6) {
                            Text("첫 브리핑 상세 보기")
                                .font(.system(size: 12, weight: .bold))
                            Image(systemName: "chevron.right")
                                .font(.system(size: 10, weight: .bold))
                        }
                        .foregroundColor(.white)
                        .padding(.horizontal, 11)
                        .padding(.vertical, 7)
                        .background(VPTheme.purple.opacity(0.22))
                        .clipShape(Capsule())
                    }
                    .buttonStyle(.plain)
                }
                .padding(12)
                .background(Color.white.opacity(0.04))
                .clipShape(RoundedRectangle(cornerRadius: 12))
            } else {
                Text("크롤링 완료 후 서버에서 받은 첫 브리핑이 여기에 표시됩니다.")
                    .font(.system(size: 11.5, weight: .medium))
                    .foregroundColor(VPTheme.textTertiary)
                    .lineLimit(2)
            }
        }
        .padding(14)
        .background(VPTheme.surfaceElevated)
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(VPTheme.purple.opacity(0.18), lineWidth: 1))
    }

    private var loadingView: some View {
        HStack(spacing: 10) {
            ProgressView()
                .tint(.white)
            Text("브리핑을 불러오는 중입니다")
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(VPTheme.textSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(18)
        .background(VPTheme.surface)
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(Color.white.opacity(0.05), lineWidth: 1))
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

    private func loadBriefings() async {
        isLoading = true
        errorMessage = nil

        do {
            briefs = try await NetworkManager.shared.fetchBriefings()
            lastCrawlCheckText = timeString(from: Date())
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

    private func testCrawling() async {
        crawlLoading = true
        crawlMessage = "크롤링 시작 중..."
        crawlAttemptCount = 0
        lastCrawlCheckText = "-"
        errorMessage = nil
        briefs = []

        do {
            _ = try await NetworkManager.shared.triggerCrawl()
            crawlMessage = "크롤링 시작됨. 잠시 후 자동 새로고침합니다..."

            try await Task.sleep(nanoseconds: 2_000_000_000)

            for index in 1...60 {
                crawlAttemptCount = index
                await loadBriefings()

                if !briefs.isEmpty {
                    crawlMessage = "크롤링 완료! 데이터가 로드되었습니다."
                    crawlLoading = false
                    return
                }

                crawlMessage = "크롤링 중... \(index)초"
                try await Task.sleep(nanoseconds: 1_000_000_000)
            }

            crawlMessage = "크롤링 타임아웃: 1분 안에 새 데이터가 확인되지 않았습니다."
            crawlLoading = false
        } catch {
            crawlMessage = "크롤링 실패: \(error.localizedDescription)"
            crawlLoading = false
        }
    }

    private func timeString(from date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "ko_KR")
        formatter.dateFormat = "HH:mm:ss"
        return formatter.string(from: date)
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

            HStack(spacing: 4) {
                Image(systemName: isProMode ? "crown.fill" : "person.fill")
                    .font(.system(size: 9, weight: .bold))
                Text(isProMode ? "프로" : "무료")
                    .font(.system(size: 10, weight: .bold))
                    .tracking(0.4)
            }
            .foregroundColor(.white)
            .padding(.horizontal, 9)
            .padding(.vertical, 5)
            .background(
                LinearGradient(
                    colors: [VPTheme.purple, VPTheme.pink],
                    startPoint: .leading, endPoint: .trailing
                )
            )
            .clipShape(Capsule())
            .shadow(color: VPTheme.purple.opacity(0.4), radius: 8, y: 4)
        }
    }

    private func todayString() -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "ko_KR")
        formatter.dateFormat = "M월 d일 EEEE"
        return formatter.string(from: Date())
    }
}

private struct CrawlMetric: View {
    let title: String
    let value: String

    var body: some View {
        VStack(spacing: 4) {
            Text(title)
                .font(.system(size: 10, weight: .bold))
                .foregroundColor(VPTheme.textMuted)
            Text(value)
                .font(.system(size: 11.5, weight: .bold))
                .foregroundColor(.white.opacity(0.86))
                .lineLimit(1)
                .minimumScaleFactor(0.8)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 8)
        .background(Color.white.opacity(0.04))
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }
}

// MARK: - Brief Card
struct BriefCard: View {
    let group: BriefSlotGroup

    var body: some View {
        ZStack(alignment: .leading) {
            // Background with illustration
            ZStack(alignment: .trailing) {
                RoundedRectangle(cornerRadius: 20)
                    .fill(VPTheme.surface)

                BriefIllustration(slot: group.slot)
                    .frame(width: 180, height: 130)
                    .padding(.trailing, -10)
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
                            .foregroundColor(VPTheme.textTertiary)
                    }

                    Text(group.slot.title)
                        .font(.system(size: 19, weight: .bold))
                        .foregroundColor(.white)
                        .padding(.top, 6)

                    Text(group.slot.tagline)
                        .font(.system(size: 11.5, weight: .medium))
                        .foregroundColor(VPTheme.textTertiary)
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
                .stroke(Color.white.opacity(0.06), lineWidth: 1)
        )
    }

    @ViewBuilder
    private var statusPill: some View {
        if group.isUnlocked {
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
                Text("프로 전용")
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
