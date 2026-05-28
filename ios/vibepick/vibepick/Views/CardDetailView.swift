import SwiftUI

// MARK: - 04. Card Detail (Full-bleed hero)
struct CardDetailView: View {
    let brief: Brief
    @Environment(\.dismiss) private var dismiss

    private var slot: BriefSlot { brief.slot }

    var body: some View {
        ZStack(alignment: .top) {
            VPTheme.background.ignoresSafeArea()

            heroImage
                .ignoresSafeArea(edges: .top)

            ScrollView {
                VStack(spacing: 0) {
                    Color.clear.frame(height: 230)
                    heroTitle
                    body_
                }
            }
            .ignoresSafeArea(edges: .top)

            // Floating top bar overlay
            topBar
                .padding(.horizontal, 16)
                .padding(.top, 6)
        }
        .navigationBarHidden(true)
    }

    // MARK: Hero (fixed image)
    private var heroImage: some View {
        VStack(spacing: 0) {
            ZStack {
                heroBackdrop
                    .frame(height: 320)
                    .clipped()

                LinearGradient(
                    colors: [Color.clear, VPTheme.background.opacity(0.4), VPTheme.background],
                    startPoint: .top, endPoint: .bottom
                )
                .frame(height: 320)
            }

            Spacer()
        }
    }

    private var heroTitle: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 6) {
                Image(systemName: brief.primaryCategory.iconName)
                    .font(.system(size: 11, weight: .bold))
                    .foregroundColor(brief.primaryCategory.color)
                    .frame(width: 14)

                Text(brief.categoryLabel)
                    .font(.system(size: 11, weight: .bold))
                    .tracking(0.6)
                    .foregroundColor(.white.opacity(0.86))
            }

            Text(brief.title)
                .font(.system(size: 26, weight: .bold))
                .foregroundColor(.white)
                .lineSpacing(3)
                .multilineTextAlignment(.leading)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(.horizontal, 20)
        .padding(.bottom, 22)
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    @ViewBuilder
    private var heroBackdrop: some View {
        switch brief.primaryCategory {
        case .all:
            categoryHero(colors: slot.gradientColors, symbol: "sparkles", pattern: .rings)
        case .aiTech:
            categoryHero(colors: [Color(hex: "1E1B4B"), Color(hex: "7C3AED"), Color(hex: "22D3EE")], symbol: "cpu.fill", pattern: .grid)
        case .finance:
            categoryHero(colors: [Color(hex: "064E3B"), Color(hex: "10B981"), Color(hex: "A7F3D0")], symbol: "chart.line.uptrend.xyaxis", pattern: .bars)
        case .energy:
            categoryHero(colors: [Color(hex: "431407"), Color(hex: "EA580C"), Color(hex: "FDE68A")], symbol: "bolt.fill", pattern: .rays)
        case .mobility:
            categoryHero(colors: [Color(hex: "082F49"), Color(hex: "0284C7"), Color(hex: "BAE6FD")], symbol: "car.fill", pattern: .tracks)
        case .bio:
            categoryHero(colors: [Color(hex: "052E16"), Color(hex: "16A34A"), Color(hex: "BBF7D0")], symbol: "cross.case.fill", pattern: .cells)
        case .consumerLife:
            categoryHero(colors: [Color(hex: "4A044E"), Color(hex: "DB2777"), Color(hex: "FBCFE8")], symbol: "bag.fill", pattern: .bubbles)
        case .industryManufacturing:
            categoryHero(colors: [Color(hex: "1E293B"), Color(hex: "64748B"), Color(hex: "CBD5E1")], symbol: "gearshape.2.fill", pattern: .gears)
        case .global:
            categoryHero(colors: [Color(hex: "172554"), Color(hex: "2563EB"), Color(hex: "BFDBFE")], symbol: "globe.americas.fill", pattern: .orbits)
        case .crypto:
            categoryHero(colors: [Color(hex: "422006"), Color(hex: "F59E0B"), Color(hex: "FEF3C7")], symbol: "bitcoinsign.circle.fill", pattern: .coins)
        case .contentEntertainment:
            categoryHero(colors: [Color(hex: "3B0764"), Color(hex: "A855F7"), Color(hex: "F0ABFC")], symbol: "play.rectangle.fill", pattern: .frames)
        }
    }

    private enum HeroPattern {
        case rings, grid, bars, rays, tracks, cells, bubbles, gears, orbits, coins, frames
    }

    private func categoryHero(colors: [Color], symbol: String, pattern: HeroPattern) -> some View {
        ZStack {
            LinearGradient(colors: colors, startPoint: .topLeading, endPoint: .bottomTrailing)

            Circle()
                .fill(colors.last?.opacity(0.28) ?? Color.white.opacity(0.18))
                .frame(width: 240, height: 240)
                .blur(radius: 12)
                .offset(x: 120, y: -50)

            Circle()
                .fill(colors.first?.opacity(0.42) ?? Color.black.opacity(0.2))
                .frame(width: 220, height: 220)
                .blur(radius: 16)
                .offset(x: -130, y: 90)

            heroPattern(pattern, accent: colors.last ?? .white)
                .opacity(0.72)

            Image(systemName: symbol)
                .font(.system(size: 92, weight: .bold))
                .foregroundColor(.white.opacity(0.2))
                .offset(x: 92, y: 24)
        }
    }

    @ViewBuilder
    private func heroPattern(_ pattern: HeroPattern, accent: Color) -> some View {
        switch pattern {
        case .rings:
            ForEach(0..<4, id: \.self) { i in
                Circle()
                    .stroke(Color.white.opacity(0.16), lineWidth: 1)
                    .frame(width: CGFloat(90 + i * 46), height: CGFloat(90 + i * 46))
                    .offset(x: -70, y: CGFloat(-42 + i * 18))
            }
        case .grid:
            LazyVGrid(columns: Array(repeating: GridItem(.fixed(34), spacing: 10), count: 7), spacing: 10) {
                ForEach(0..<35, id: \.self) { i in
                    RoundedRectangle(cornerRadius: 7)
                        .stroke(Color.white.opacity(i % 3 == 0 ? 0.22 : 0.08), lineWidth: 1)
                        .frame(width: 34, height: 24)
                }
            }
            .rotationEffect(.degrees(-10))
            .offset(x: -10, y: 20)
        case .bars:
            HStack(alignment: .bottom, spacing: 10) {
                ForEach([44, 76, 58, 116, 88, 132, 96], id: \.self) { height in
                    RoundedRectangle(cornerRadius: 6)
                        .fill(Color.white.opacity(0.16))
                        .frame(width: 18, height: CGFloat(height))
                }
            }
            .offset(x: -76, y: 56)
        case .rays:
            ForEach(0..<14, id: \.self) { i in
                Capsule()
                    .fill(accent.opacity(0.22))
                    .frame(width: 4, height: 170)
                    .rotationEffect(.degrees(Double(i) * 14))
                    .offset(y: 48)
            }
        case .tracks:
            ForEach(0..<5, id: \.self) { i in
                Capsule()
                    .stroke(Color.white.opacity(0.14), lineWidth: 2)
                    .frame(width: 260, height: 34)
                    .rotationEffect(.degrees(-18))
                    .offset(x: CGFloat(-40 + i * 18), y: CGFloat(-70 + i * 38))
            }
        case .cells:
            ForEach(0..<12, id: \.self) { i in
                Circle()
                    .stroke(Color.white.opacity(0.14), lineWidth: 1.5)
                    .frame(width: CGFloat([28, 44, 62, 36][i % 4]), height: CGFloat([28, 44, 62, 36][i % 4]))
                    .offset(x: CGFloat([-130, -72, -14, 42, 96, 138][i % 6]), y: CGFloat([-86, -38, 22, 76][i % 4]))
            }
        case .bubbles:
            ForEach(0..<12, id: \.self) { i in
                Circle()
                    .fill(Color.white.opacity(0.12))
                    .frame(width: CGFloat([18, 28, 42, 56][i % 4]), height: CGFloat([18, 28, 42, 56][i % 4]))
                    .offset(x: CGFloat([-144, -92, -35, 20, 82, 134][i % 6]), y: CGFloat([-82, -28, 34, 86][i % 4]))
            }
        case .gears:
            ForEach(0..<5, id: \.self) { i in
                Image(systemName: "gearshape.fill")
                    .font(.system(size: CGFloat(26 + i * 10), weight: .bold))
                    .foregroundColor(Color.white.opacity(0.13))
                    .rotationEffect(.degrees(Double(i * 18)))
                    .offset(x: CGFloat([-130, -62, 20, 92, 142][i]), y: CGFloat([-48, 58, -86, 38, -8][i]))
            }
        case .orbits:
            ForEach(0..<5, id: \.self) { i in
                Ellipse()
                    .stroke(Color.white.opacity(0.14), lineWidth: 1)
                    .frame(width: CGFloat(120 + i * 38), height: CGFloat(46 + i * 20))
                    .rotationEffect(.degrees(Double(-28 + i * 16)))
            }
        case .coins:
            ForEach(0..<10, id: \.self) { i in
                Circle()
                    .stroke(accent.opacity(0.25), lineWidth: 2)
                    .frame(width: CGFloat([28, 38, 54][i % 3]), height: CGFloat([28, 38, 54][i % 3]))
                    .offset(x: CGFloat([-130, -72, -18, 42, 104][i % 5]), y: CGFloat([-78, -18, 42, 92][i % 4]))
            }
        case .frames:
            ForEach(0..<7, id: \.self) { i in
                RoundedRectangle(cornerRadius: 10)
                    .stroke(Color.white.opacity(0.15), lineWidth: 1.5)
                    .frame(width: 86, height: 52)
                    .rotationEffect(.degrees(Double(-18 + i * 7)))
                    .offset(x: CGFloat(-132 + i * 42), y: CGFloat([-72, -22, 34, 82][i % 4]))
            }
        }
    }

    // MARK: Body content
    private var body_: some View {
        VStack(alignment: .leading, spacing: 18) {
            moodSection
            summarySection
            if !brief.positivePoints.isEmpty {
                pointsSection(
                    title: "긍정 포인트",
                    points: brief.positivePoints,
                    icon: "arrow.up.right",
                    color: VPTheme.positive
                )
            }
            if !brief.negativePoints.isEmpty {
                pointsSection(
                    title: "부정 포인트",
                    points: brief.negativePoints,
                    icon: "arrow.down.right",
                    color: VPTheme.negative
                )
            }
            stocksSection
            aiBriefFooter
        }
        .padding(.horizontal, 18)
        .padding(.top, 6)
        .padding(.bottom, 32)
    }

    private var moodSection: some View {
        HStack {
            Text("현재 분위기")
                .font(.system(size: 11, weight: .bold))
                .tracking(0.8)
                .foregroundColor(VPTheme.textTertiary)

            Spacer()

            HStack(spacing: 5) {
                Text(brief.mood.rawValue)
                    .font(.system(size: 12, weight: .bold))
                Text(brief.mood.arrow)
                    .font(.system(size: 13, weight: .bold))
            }
            .foregroundColor(brief.mood.color)
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(brief.mood.color.opacity(0.16))
            .overlay(Capsule().stroke(brief.mood.color.opacity(0.4), lineWidth: 1))
            .clipShape(Capsule())
        }
    }

    private var summarySection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("핵심 한눈 요약")
                .font(.system(size: 13, weight: .bold))
                .foregroundColor(.white)

            Text(brief.summary)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(VPTheme.textSecondary)
                .lineSpacing(5)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(VPTheme.surface)
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(Color.white.opacity(0.05), lineWidth: 1))
    }

    private func pointsSection(title: String, points: [String], icon: String, color: Color) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.system(size: 13, weight: .bold))
                .foregroundColor(.white)

            VStack(spacing: 10) {
                ForEach(Array(points.enumerated()), id: \.offset) { _, point in
                    HStack(alignment: .top, spacing: 10) {
                        ZStack {
                            Circle()
                                .fill(color.opacity(0.16))
                                .frame(width: 22, height: 22)
                            Image(systemName: icon)
                                .font(.system(size: 10, weight: .bold))
                                .foregroundColor(color)
                        }

                        Text(point)
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(VPTheme.textSecondary)
                            .lineSpacing(3)
                            .fixedSize(horizontal: false, vertical: true)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
            }
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(VPTheme.surface)
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(Color.white.opacity(0.05), lineWidth: 1))
    }

    private var stocksSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("관련 종목")
                    .font(.system(size: 13, weight: .bold))
                    .foregroundColor(.white)
                Spacer()
                Text("\(brief.relatedStocks.count)개")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(VPTheme.textTertiary)
            }

            LazyVGrid(columns: [GridItem(.adaptive(minimum: 90), spacing: 8)], alignment: .leading, spacing: 8) {
                ForEach(brief.relatedStocks, id: \.self) { stock in
                    Text(stock)
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(.white.opacity(0.86))
                        .padding(.horizontal, 11)
                        .padding(.vertical, 7)
                        .background(Color.white.opacity(0.06))
                        .overlay(Capsule().stroke(Color.white.opacity(0.08), lineWidth: 1))
                        .clipShape(Capsule())
                }
            }
        }
    }

    private var aiBriefFooter: some View {
        HStack(spacing: 10) {
            Image(systemName: "sparkles")
                .font(.system(size: 13, weight: .bold))
                .foregroundColor(VPTheme.purple)
            Text("AI 브리핑 · 투자 권유가 아닌 시장 흐름 참고 정보입니다.")
                .font(.system(size: 10.5, weight: .semibold))
                .tracking(0.3)
                .foregroundColor(VPTheme.textTertiary)
                .lineLimit(2)
                .fixedSize(horizontal: false, vertical: true)
            Spacer()
        }
        .padding(12)
        .background(VPTheme.purple.opacity(0.08))
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(VPTheme.purple.opacity(0.18), lineWidth: 1))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: Floating top bar
    private var topBar: some View {
        HStack(spacing: 10) {
            Button { dismiss() } label: {
                Image(systemName: "chevron.left")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.white)
                    .frame(width: 34, height: 34)
                    .background(.ultraThinMaterial)
                    .background(Color.black.opacity(0.2))
                    .clipShape(Circle())
                    .overlay(Circle().stroke(Color.white.opacity(0.18), lineWidth: 1))
            }

            Spacer()

            HStack(spacing: 6) {
                Text(slot.emoji)
                    .font(.system(size: 13))
                Text("\(slot.time) \(slot.title)")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(.white)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 7)
            .background(.ultraThinMaterial)
            .background(Color.black.opacity(0.2))
            .clipShape(Capsule())
            .overlay(Capsule().stroke(Color.white.opacity(0.18), lineWidth: 1))

            Spacer()

            Color.clear.frame(width: 34, height: 34)
        }
    }
}

#Preview {
    NavigationStack {
        CardDetailView(brief: DummyData.briefs[0])
    }
}
