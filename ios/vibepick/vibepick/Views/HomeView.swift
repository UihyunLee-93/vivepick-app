import SwiftUI

// MARK: - 01. Home (Today's Briefing)
struct HomeView: View {
    @AppStorage(AppMode.isProModeStorageKey) private var isProMode = false

    private var briefs: [Brief] {
        DummyData.makeBriefs(isProMode: isProMode)
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

                        ForEach(briefs) { brief in
                            NavigationLink {
                                if brief.isUnlocked {
                                    BriefDetailView(brief: brief)
                                } else {
                                    LockedBriefView(slot: brief.slot)
                                }
                            } label: {
                                BriefCard(brief: brief)
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

// MARK: - Brief Card
struct BriefCard: View {
    let brief: Brief

    var body: some View {
        ZStack(alignment: .leading) {
            // Background with illustration
            ZStack(alignment: .trailing) {
                RoundedRectangle(cornerRadius: 20)
                    .fill(VPTheme.surface)

                BriefIllustration(slot: brief.slot)
                    .frame(width: 180, height: 130)
                    .padding(.trailing, -10)
            }

            // Content
            HStack(alignment: .top, spacing: 0) {
                VStack(alignment: .leading, spacing: 0) {
                    HStack(spacing: 6) {
                        Text(brief.slot.emoji)
                            .font(.system(size: 13))
                        Text(brief.slot.time)
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(.white.opacity(0.7))
                    }

                    Text(brief.slot.title)
                        .font(.system(size: 19, weight: .bold))
                        .foregroundColor(.white)
                        .padding(.top, 6)

                    Text(brief.slot.tagline)
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
        if brief.isUnlocked {
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
