import SwiftUI

struct SplashView: View {
    var onStart: () -> Void

    var body: some View {
        ZStack {
            VPTheme.background.ignoresSafeArea()

            RadialGradient(
                colors: [VPTheme.orange.opacity(0.28), .clear],
                center: .center,
                startRadius: 30,
                endRadius: 260
            )
            .ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer()

                VStack(spacing: 18) {
                    AppLogo(size: 74)

                    Text("VibePick")
                        .font(.system(size: 30, weight: .bold))
                        .foregroundColor(.white)

                    Text("오늘 시장 분위기를 빠르게.")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(VPTheme.grayText)
                }

                VStack(spacing: 10) {
                    SplashSignalRow(icon: "flame.fill", title: "#AI", status: "관심 확대 흐름", color: VPTheme.orange)
                    SplashSignalRow(icon: "cloud.fill", title: "#2차전지", status: "거래량 둔화", color: VPTheme.blue)
                    SplashSignalRow(icon: "eye.fill", title: "#금리", status: "관망 분위기", color: VPTheme.purple)
                }
                .padding(.top, 48)
                .padding(.horizontal, 24)

                Spacer()

                Button(action: onStart) {
                    Text("시작하기  →")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(.black)
                        .frame(maxWidth: .infinity)
                        .frame(height: 54)
                        .background(Color.white)
                        .clipShape(RoundedRectangle(cornerRadius: 14))
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
                        Color(red: 1.0, green: 0.56, blue: 0.28),
                        Color(red: 1.0, green: 0.26, blue: 0.42),
                        Color(red: 0.58, green: 0.42, blue: 1.0)
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
            .shadow(color: VPTheme.orange.opacity(0.35), radius: 24, x: 0, y: 12)
    }
}

struct SplashSignalRow: View {
    let icon: String
    let title: String
    let status: String
    let color: Color

    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(color)
                .font(.system(size: 14, weight: .semibold))

            Text(title)
                .font(.system(size: 13, weight: .bold))
                .foregroundColor(.white)

            Spacer()

            Text(status)
                .font(.system(size: 12, weight: .semibold))
                .foregroundColor(.white.opacity(0.78))
        }
        .padding(.horizontal, 14)
        .frame(height: 46)
        .background(VPTheme.card)
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
