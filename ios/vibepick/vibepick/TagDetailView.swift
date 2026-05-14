import SwiftUI

struct TagDetailView: View {
    let vibe: Vibe
    @State private var isSaved = false
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ZStack {
            VPTheme.background.ignoresSafeArea()

            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    topBar
                    titleSection
                    moodBar
                    pointCards
                    stockSection
                    aiBrief
                }
                .padding(.horizontal, 18)
                .padding(.top, 14)
                .padding(.bottom, 32)
            }
        }
        .navigationBarHidden(true)
    }

    private var topBar: some View {
        HStack {
            Button(action: { dismiss() }) {
                Image(systemName: "chevron.left")
                    .font(.system(size: 15, weight: .bold))
                    .foregroundColor(.white.opacity(0.86))
                    .frame(width: 36, height: 36)
                    .background(VPTheme.card)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
            }

            Spacer()

            HStack(spacing: 10) {
                Button(action: { isSaved.toggle() }) {
                    Image(systemName: isSaved ? "bookmark.fill" : "bookmark")
                }

                Button(action: {}) {
                    Image(systemName: "square.and.arrow.up")
                }
            }
            .font(.system(size: 15, weight: .semibold))
            .foregroundColor(.white.opacity(0.82))
        }
    }

    private var titleSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 8) {
                Image(systemName: vibe.state.icon)
                    .font(.system(size: 15, weight: .bold))
                    .foregroundColor(vibe.state.color)

                Text("#\(vibe.tag)")
                    .font(.system(size: 15, weight: .bold))
                    .foregroundColor(.white)

                Text(vibe.state.rawValue)
                    .font(.system(size: 11, weight: .bold))
                    .foregroundColor(vibe.state.color)
                    .padding(.horizontal, 7)
                    .padding(.vertical, 4)
                    .background(vibe.state.color.opacity(0.15))
                    .clipShape(Capsule())

                Spacer()

                Text("7개 이슈")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(.white.opacity(0.38))
            }

            Text(vibe.title.replacingOccurrences(of: " ", with: "\n"))
                .font(.system(size: 32, weight: .bold))
                .foregroundColor(.white)
                .lineSpacing(2)

            Text(vibe.detail)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.white.opacity(0.62))
                .lineLimit(2)
        }
    }

    private var moodBar: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("시장 모드")
                    .font(.system(size: 11, weight: .bold))
                    .tracking(1.0)
                    .foregroundColor(.white.opacity(0.44))

                Spacer()

                Text(vibe.state.rawValue)
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(vibe.state.color)
            }

            GeometryReader { proxy in
                ZStack(alignment: .leading) {
                    Capsule()
                        .fill(Color.white.opacity(0.08))
                        .frame(height: 6)

                    Capsule()
                        .fill(
                            LinearGradient(
                                colors: [VPTheme.purple, VPTheme.blue, VPTheme.orange],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .frame(width: proxy.size.width * 0.78, height: 6)

                    Circle()
                        .fill(vibe.state.color)
                        .frame(width: 14, height: 14)
                        .offset(x: proxy.size.width * 0.78 - 7)
                        .shadow(color: vibe.state.color.opacity(0.6), radius: 8)
                }
            }
            .frame(height: 16)

            HStack {
                Text("약함")
                Spacer()
                Text("관망")
                Spacer()
                Text("강세")
            }
            .font(.system(size: 10, weight: .medium))
            .foregroundColor(.white.opacity(0.34))
        }
        .padding(16)
        .background(VPTheme.card)
        .clipShape(RoundedRectangle(cornerRadius: 16))
    }

    private var pointCards: some View {
        HStack(spacing: 12) {
            DetailPointCard(
                title: "긍정 포인트",
                text: positiveText,
                color: VPTheme.orange,
                icon: "bolt.fill"
            )

            DetailPointCard(
                title: "주의 포인트",
                text: cautionText,
                color: VPTheme.purple,
                icon: "exclamationmark.triangle.fill"
            )
        }
    }

    private var positiveText: String {
        switch vibe.tag {
        case "AI": return "AI 인프라 관심 유지"
        case "반도체": return "실적 기대감 유지"
        case "2차전지": return "저가 매수 관심"
        case "금리": return "발표 후 방향 확인"
        default: return "관심 회복 흐름"
        }
    }

    private var cautionText: String {
        switch vibe.tag {
        case "AI": return "단기 과열 부담"
        case "반도체": return "환율·금리 변수"
        case "2차전지": return "거래량 둔화"
        case "금리": return "시장 흔들림 가능"
        default: return "흐름 확인 필요"
        }
    }

    private var stockSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("관련 종목")
                    .font(.system(size: 13, weight: .bold))
                    .foregroundColor(.white)

                Spacer()

                Text("\(vibe.relatedStocks.count)개")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(.white.opacity(0.36))
            }

            FlowLayout(items: vibe.relatedStocks) { stock in
                Text(stock)
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(.white.opacity(0.84))
                    .padding(.horizontal, 11)
                    .padding(.vertical, 7)
                    .background(VPTheme.cardSoft)
                    .clipShape(Capsule())
            }
        }
    }

    private var aiBrief: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "sparkles")
                    .foregroundColor(VPTheme.blue)

                Text("AI 추가 브리핑")
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(VPTheme.blue)
            }

            Text("\(vibe.tag) 흐름은 \(vibe.summary) 상태입니다. 단기 방향보다 시장 관심이 이어지는지 확인하는 구간입니다.")
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.white.opacity(0.68))
                .lineLimit(3)

            Text("투자 권유가 아닌 시장 흐름 참고 정보입니다.")
                .font(.system(size: 10, weight: .bold))
                .tracking(0.7)
                .foregroundColor(.white.opacity(0.28))
                .padding(.top, 2)
        }
        .padding(16)
        .background(VPTheme.card)
        .clipShape(RoundedRectangle(cornerRadius: 16))
    }
}

struct DetailPointCard: View {
    let title: String
    let text: String
    let color: Color
    let icon: String

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Image(systemName: icon)
                .foregroundColor(color)
                .font(.system(size: 14, weight: .bold))

            Text(title)
                .font(.system(size: 10, weight: .bold))
                .tracking(0.8)
                .foregroundColor(color)

            Text(text)
                .font(.system(size: 14, weight: .bold))
                .foregroundColor(.white)
                .lineLimit(2)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(14)
        .background(color.opacity(0.10))
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(color.opacity(0.18), lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: 16))
    }
}

struct FlowLayout<Data: RandomAccessCollection, Content: View>: View where Data.Element: Hashable {
    let items: Data
    let content: (Data.Element) -> Content

    init(items: Data, @ViewBuilder content: @escaping (Data.Element) -> Content) {
        self.items = items
        self.content = content
    }

    var body: some View {
        LazyVGrid(columns: [GridItem(.adaptive(minimum: 86), spacing: 8)], alignment: .leading, spacing: 8) {
            ForEach(Array(items), id: \.self) { item in
                content(item)
            }
        }
    }
}

#Preview {
    TagDetailView(vibe: DummyData.vibes[0])
}
