import SwiftUI

struct ProfileView: View {
    private let profile = DummyData.userProfile
    @State private var morningBrief = true
    @State private var closeBrief = true

    var body: some View {
        ZStack {
            VPTheme.background.ignoresSafeArea()

            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    header
                    profileCard
                    interestSettings
                    alarmCard
                    proCard
                    infoRows
                }
                .padding(.horizontal, 18)
                .padding(.top, 16)
                .padding(.bottom, 30)
            }
        }
    }

    private var header: some View {
        HStack {
            Text("프로필")
                .font(.system(size: 22, weight: .bold))
                .foregroundColor(.white)

            Spacer()

            Text("v1.0.0")
                .font(.system(size: 10, weight: .bold))
                .foregroundColor(.white.opacity(0.34))
        }
    }

    private var profileCard: some View {
        HStack(spacing: 14) {
            Circle()
                .fill(
                    LinearGradient(
                        colors: [VPTheme.orange, Color(red: 0.66, green: 0.48, blue: 1.0)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .frame(width: 58, height: 58)
                .overlay(
                    Text(profile.avatar)
                        .font(.system(size: 24, weight: .bold))
                        .foregroundColor(.white)
                )

            VStack(alignment: .leading, spacing: 5) {
                Text(profile.name)
                    .font(.system(size: 16, weight: .bold))
                    .foregroundColor(.white)

                Text(profile.email)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(.white.opacity(0.48))

                if profile.isPro {
                    Text("PRO")
                        .font(.system(size: 9, weight: .bold))
                        .foregroundColor(VPTheme.orange)
                        .padding(.horizontal, 7)
                        .padding(.vertical, 3)
                        .background(VPTheme.orange.opacity(0.14))
                        .clipShape(Capsule())
                }
            }

            Spacer()

            Image(systemName: "chevron.right")
                .foregroundColor(.white.opacity(0.32))
        }
        .padding(16)
        .background(VPTheme.card)
        .clipShape(RoundedRectangle(cornerRadius: 18))
    }

    private var interestSettings: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionTitle("내 관심 설정")

            TagWrap(tags: profile.interestTags, color: VPTheme.orange)
            TagWrap(tags: profile.interestStocks, color: VPTheme.blue)
        }
        .padding(16)
        .background(VPTheme.card)
        .clipShape(RoundedRectangle(cornerRadius: 18))
    }

    private var alarmCard: some View {
        VStack(spacing: 0) {
            ToggleRow(icon: "bell", title: "아침 브리핑", subtitle: "매일 오전 08:30", isOn: $morningBrief)
            Divider().background(VPTheme.line)
            ToggleRow(icon: "clock", title: "장마감 브리핑", subtitle: "매일 오후 18:00", isOn: $closeBrief)
        }
        .padding(.horizontal, 16)
        .background(VPTheme.card)
        .clipShape(RoundedRectangle(cornerRadius: 18))
    }

    private var proCard: some View {
        HStack(spacing: 12) {
            Image(systemName: "sparkles")
                .font(.system(size: 16, weight: .bold))
                .foregroundColor(.black)
                .frame(width: 40, height: 40)
                .background(VPTheme.orange)
                .clipShape(RoundedRectangle(cornerRadius: 12))

            VStack(alignment: .leading, spacing: 5) {
                Text("VibePick PRO")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.white)

                Text("무제한 태그 · 관심 종목 브리핑 · 실시간 알림")
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(.white.opacity(0.58))
                    .lineLimit(1)
            }

            Spacer()

            Button("관리") {}
                .font(.system(size: 12, weight: .bold))
                .foregroundColor(.black)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color.white)
                .clipShape(Capsule())
        }
        .padding(14)
        .background(
            LinearGradient(
                colors: [VPTheme.orange.opacity(0.28), VPTheme.card],
                startPoint: .leading,
                endPoint: .trailing
            )
        )
        .clipShape(RoundedRectangle(cornerRadius: 18))
    }

    private var infoRows: some View {
        VStack(spacing: 10) {
            ProfileRow(icon: "info.circle", title: "앱 정보 · 투자 유의사항")
            ProfileRow(icon: "questionmark.circle", title: "도움말")
            ProfileRow(icon: "rectangle.portrait.and.arrow.right", title: "로그아웃")
        }
    }
}

struct SectionTitle: View {
    let title: String

    init(_ title: String) {
        self.title = title
    }

    var body: some View {
        Text(title)
            .font(.system(size: 13, weight: .bold))
            .foregroundColor(.white)
    }
}

struct TagWrap: View {
    let tags: [String]
    let color: Color

    var body: some View {
        LazyVGrid(columns: [GridItem(.adaptive(minimum: 76), spacing: 8)], alignment: .leading, spacing: 8) {
            ForEach(tags, id: \.self) { tag in
                Text(tag)
                    .font(.system(size: 11, weight: .bold))
                    .foregroundColor(color)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 7)
                    .background(color.opacity(0.12))
                    .clipShape(Capsule())
            }
        }
    }
}

struct ToggleRow: View {
    let icon: String
    let title: String
    let subtitle: String
    @Binding var isOn: Bool

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .foregroundColor(.white.opacity(0.58))
                .frame(width: 28, height: 28)

            VStack(alignment: .leading, spacing: 3) {
                Text(title)
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.white)

                Text(subtitle)
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(.white.opacity(0.44))
            }

            Spacer()

            Toggle("", isOn: $isOn)
                .labelsHidden()
                .tint(VPTheme.orange)
        }
        .padding(.vertical, 13)
    }
}

struct ProfileRow: View {
    let icon: String
    let title: String

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .foregroundColor(.white.opacity(0.56))
                .frame(width: 28, height: 28)

            Text(title)
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(.white.opacity(0.78))

            Spacer()

            Image(systemName: "chevron.right")
                .font(.system(size: 11, weight: .bold))
                .foregroundColor(.white.opacity(0.28))
        }
        .padding(14)
        .background(VPTheme.card)
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }
}

#Preview {
    ProfileView()
}
