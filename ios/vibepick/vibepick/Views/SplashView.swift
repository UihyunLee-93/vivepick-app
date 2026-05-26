import SwiftUI

struct SplashView: View {
    var onStart: () -> Void

    var body: some View {
        ZStack {
            VPTheme.background.ignoresSafeArea()

            RadialGradient(
                colors: [VPTheme.purple.opacity(0.32), .clear],
                center: .center,
                startRadius: 30,
                endRadius: 280
            )
            .ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer()

                VStack(spacing: 18) {
                    AppLogo(size: 84)

                    Text("VibePick")
                        .font(.system(size: 32, weight: .bold))
                        .foregroundColor(.white)

                    Text("하루 3번, 시장 분위기 브리핑")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(VPTheme.grayText)
                }

                VStack(spacing: 10) {
                    SplashSignalRow(emoji: "🌅", title: "아침 브리핑", status: "07:30", color: Color(hex: "FF8A4C"))
                    SplashSignalRow(emoji: "☀️", title: "점심 브리핑", status: "12:30 · 프로", color: Color(hex: "FFB86B"))
                    SplashSignalRow(emoji: "🌙", title: "저녁 브리핑", status: "20:00 · 프로", color: Color(hex: "8B5CF6"))
                }
                .padding(.top, 44)
                .padding(.horizontal, 24)

                Spacer()

                Button(action: onStart) {
                    Text("시작하기  →")
                        .font(.system(size: 16, weight: .bold))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .frame(height: 54)
                        .background(
                            LinearGradient(
                                colors: [VPTheme.purple, VPTheme.pink],
                                startPoint: .leading, endPoint: .trailing
                            )
                        )
                        .clipShape(RoundedRectangle(cornerRadius: 14))
                        .shadow(color: VPTheme.purple.opacity(0.5), radius: 18, y: 10)
                }
                .padding(.horizontal, 24)

                Text("이미 계정이 있으신가요? 로그인")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(VPTheme.grayText)
                    .padding(.top, 16)
                    .padding(.bottom, 34)
            }
        }
    }
}

struct AppLogo: View {
    let size: CGFloat

    var body: some View {
        RoundedRectangle(cornerRadius: size * 0.24)
            .fill(
                LinearGradient(
                    colors: [
                        Color(hex: "FF8A4C"),
                        Color(hex: "EC4899"),
                        Color(hex: "8B5CF6")
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            )
            .frame(width: size, height: size)
            .overlay(
                Image(systemName: "waveform.path.ecg")
                    .font(.system(size: size * 0.44, weight: .bold))
                    .foregroundColor(.white)
            )
            .shadow(color: VPTheme.purple.opacity(0.5), radius: 24, x: 0, y: 12)
    }
}

struct SplashSignalRow: View {
    let emoji: String
    let title: String
    let status: String
    let color: Color

    var body: some View {
        HStack {
            Text(emoji)
                .font(.system(size: 16))

            Text(title)
                .font(.system(size: 13, weight: .bold))
                .foregroundColor(.white)

            Spacer()

            Text(status)
                .font(.system(size: 12, weight: .semibold))
                .foregroundColor(.white.opacity(0.78))
        }
        .padding(.horizontal, 14)
        .frame(height: 48)
        .background(VPTheme.surface)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(VPTheme.line, lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

#Preview {
    SplashView {}
}
